# Copyright © 2007 Hubert Bielenia
#
# Oprogramowanie chronione licencją EUPL, Wersja 1.2.
# Nie wolno korzystać z tego utworu w sposób inny niż
# zgodnie z Licencją.
# Kopia Licencji dostępna jest pod adresem:
#
# https://joinup.ec.europa.eu/software/page/eupl5
#
# Z wyjątkiem przypadków wymaganych obowiązującym prawem
# lub uzgodnionych na piśmie, oprogramowanie
# rozpowszechniane w ramach Licencji jest rozpowszechniane
# w „ISTNIEJĄCEJ FORMIE",
# BEZ JAKIEGOKOLWIEK RODZAJU GWARANCJI LUB WARUNKÓW,
# wyraźnych lub dorozumianych.
# W celu poznania szczegółowych postanowień dotyczących
# pozwoleń i ograniczeń w ramach Licencji, należy zapoznać
# się z treścią licencji.
"""Moduły pomocnicze paczki `transactions2pln`.

Zawiera funkcje i klasy abstrahujące część zadań potrzebnych przy obliczeniach
dokonywanych z użyciem niniejszej paczki:
`JSONWrapper` -- Klasa opakowująca deskryptor pliku wyjściowego
i udostępniająca interfejs podobny do `csv.writer` ale zapisujący
w formacie JSON.
`TablesManager` -- Klasa implementująca interfejs do pobierania plików
z odpowiednimi tabelami NBP, parsowania ich i uzyskiwania danych.
`NBPDialect` -- Klasa implementująca dialekt plików CSV umożliwiający
odczytanie tabel NBP.
`get_column_index` -- Funkcja zwracająca indeks kolumny w tabeli na podstawie
nagłówka, liczby lub litery.
"""
import csv
import json
import locale
import os
import string
import typing
from datetime import date, datetime, timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve


class JSONWrapper():
	"""Opakowuje deskryptor pliku i umożliwia zapisywanie do niego
	wierszy danych które automatycznie tłumaczy na format JSON.

	Ideą tej klasy jest to, by zapewniała podobny interfejs co obiekty
	zwracane przez funkcję `csv.writer`. Dzięki temu obsługa formatów
	CSV i JSON nie wymaga osobnych ścieżek kodu. Dane w formacie JSON
	są zapisywane jako elementy tablicy.

	Obiekty tej klasy udostępniają następujące atrybuty:
	`labels` -- Lista łańcuchów zawierających nagłówki jaka została ustawiona
	przy tworzeniu obiektu.
	`writerow` -- Metoda pozwalająca na zapis wiersza danych
	do pliku wyjściowego.
	`writeend` -- Metoda zapisująca znak końca tablicy w pliku wyjściowym.
	"""

	def __init__(
		self,
		file: typing.IO[str],
		labels: list[str]|None = None
	) -> None:
		"""Metoda inicjalizująca obiekty klasy `JSONWrapper`.

		Przyjmuje następujące parametry:
		`file` -- Deskryptor pliku do którego mają być zapisywane dane
		w formacie JSON z użyciem innych funkcji tej klasy.
		`labels` -- Opcjonalnie, lista łańcuchów zawierająca nagłówki.
		Jeżeli zostanie podana, dane będą zapisywane jako obiekty.
		"""
		self._labels: list[str]|None = labels
		self._file: typing.IO[str] = file
		self._file.write('[') # Zapisuje znak otwierający tablicę w formacie JSON.
		# Flaga oznaczająca, że dopiero zaczęliśmy zapisywanie danych. Dzięki temu
		# metoda writerow() nie umieści tu przecinka.
		self._started = True

	@property
	def labels(self) -> list[str]|None:
		"""Lista łańcuchów zawierających nagłówki,
		jeżeli została podana przy inicjalizacji obiektu.
		"""
		return self._labels

	def writerow(self, row: list[str]) -> None:
		"""Zapisanie wiersza danych do pliku wyjściowego.

		Funkcja przyjmuje jeden argument, `row`, będący listą łańcuchów
		gdzie kolejne elementy listy odpowiadają wartościom w kolejnych kolumnach.
		Jeżeli przy inicjalizacji obiektu został podany argument `labels`,
		w pliku wyjściowym zapisywane są obiekty JSON gdzie klucze to elementy
		listy `labels` a wartości - listy `row`. Jeżeli nie podano argumentu
		`labels`, cały wiersz jest zapisywany jako tablica, osadzona w głównej
		tablicy w pliku.
		"""
		# Jeżeli nie mamy nagłówków, zapisujemy wiersz jako listę.
		writeable: list[str]|dict[str, str] = row
		if self._labels:
			# Jeżeli mamy nagłówki, zapisujemy wiersz jako słownik gdzie klucze
			# to nagłówki a wartości - dane z wiersza.
			writeable = {}
			for index, item in enumerate(row):
				# Przypisanie danych z wiersza do nagłówków wg kolejności.
				writeable[self._labels[index]] = item
		# Wyczyszczenie flagi oznaczającej początek zapisu, jeśli została
		# ustawiona. Jeśli nie, zapisujemy przecinek ponieważ jesteśmy gdzieś
		# w środku pliku.
		if self._started:
			self._started = False
		else:
			self._file.write(',')
		self._file.write(json.dumps(writeable))
		self._file.flush()

	def writeend(self) -> None:
		"""Zapisuje znak końca tablicy w formacie JSON."""
		self._file.write(']')
		self._file.flush()


ExchangeTable: typing.TypeAlias = dict[date, list[str]]


class TablesManager():
	"""Interfejs do pobierania i odczytywania danych
	z tabeli kursów dziennych NBP.

	Obiekty tej klasy udostępniają następujące atrybuty:
	`DOWNLOAD_URL` -- Łańcuch zawierający wzorzec URL do plików z tabelami.
	Może zawierać pola zgodne ze składnią formatowania łańcuchów Pythona
	(https://docs.python.org/3/library/string.html#formatstrings) o nazwach:
	`table` wskazujące na oznaczenie tabeli i `year` wskazujące na rok.
	`CURRENCY_MAP` -- Słownik w którym kluczami są oznaczenia tabel NBP
	a wartościami zbiory zawierające łańcuchy odpowiadające kodom ISO 4217
	walut, jakie zawiera dana tabela.
	`year` -- Liczba całkowita oznaczająca rok dla którego pobierane są tabele.
	`get_table` -- Metoda zwracająca dane z wybranej tabeli.
	`get_exchange_ratio` -- Metoda zwracająca kurs w PLN wybranej waluty
	w wybranym dniu.
	"""
	DOWNLOAD_URL: str = 'https://static.nbp.pl/dane/kursy/Archiwum/archiwum_tab_{table}_{year}.csv' # noqa: E501
	CURRENCY_MAP: dict[str, set[str]] = {
		'a': {
			'THB', 'USD', 'AUD', 'HKD', 'CAD', 'NZD', 'EUR', 'HUF', 'CHF', 'GBP',
			'UAH', 'JPY', 'CZK', 'DKK', 'ISK', 'NOK', 'SEK', 'RON', 'BGN', 'TRY',
			'ILS', 'CLP', 'PHP', 'MXN', 'ZAR', 'BRL', 'MYR', 'IDR', 'INR', 'KRW',
			'CNY', 'XDR'
		},
		'b': {
			'AFN', 'MGA', 'PAB', 'ETB', 'VES', 'BOB', 'CRC', 'SVC', 'NIO', 'GMD',
			'MKD', 'DZD', 'BHD', 'IQD', 'JOD', 'KWD', 'LYD', 'RSD', 'TND', 'MAD',
			'AED', 'STN', 'BSD', 'BBD', 'BZD', 'BND', 'FJD', 'GYD', 'JMD', 'LRD',
			'NAD', 'SRD', 'TTD', 'XCD', 'SBD', 'ZWL', 'VND', 'AMD', 'CVE', 'AWG',
			'BIF', 'XOF', 'XAF', 'XPF', 'DJF', 'GNF', 'KMF', 'CDF', 'RWF', 'EGP',
			'GIP', 'LBP', 'SSP', 'SDG', 'SYP', 'GHS', 'HTG', 'PYG', 'ANG', 'PGK',
			'LAK', 'MWK', 'ZMW', 'AOA', 'MMK', 'GEL', 'MDL', 'ALL', 'HNL', 'SLE',
			'SZL', 'LSL', 'AZN', 'MZN', 'NGN', 'ERN', 'TWD', 'TMT', 'MRU', 'TOP',
			'MOP', 'ARS', 'DOP', 'COP', 'CUP', 'UYU', 'BWP', 'GTQ', 'IRR', 'YER',
			'QAR', 'OMR', 'SAR', 'KHR', 'BYN', 'RUB', 'LKR', 'MVR', 'MUR', 'NPR',
			'PKR', 'SCR', 'PEN', 'KGS', 'TJS', 'UZS', 'KES', 'SOS', 'TZS', 'UGX',
			'BDT', 'WST', 'KZT', 'MNT', 'VUV', 'BAM'
		},
	}

	def __init__(
			self,
			tmp_dir: TemporaryDirectory, # type: ignore[type-arg]
			year: int,
		) -> None:
		"""Metoda inicjalizująca obiekty klasy `TablesManager.

		Przyjmuje następujące parametry:
		`tmp_dir` -- Obiekt katalogu tymczasowego do użytku roboczego.
		`year` -- Liczba całkowita oznaczająca rok dla którego obiekt
		ma pobierać i udostępniać dane o kursach.
		"""
		self.year: int = year
		self._tmpdir: TemporaryDirectory = tmp_dir # type: ignore[type-arg]
		self._currency_lookup: dict[str, int] = {}

	def _download_table(self, table: str, year: int) -> ExchangeTable:
		# Pobieranie i parsowanie pliku tabeli.
		url: str = self.DOWNLOAD_URL.format(table=table, year=year)
		dest: str = os.path.join(
			self._tmpdir.name, f'archiwum_tab_{table}_{year}.csv')
		urlretrieve(url, dest)

		parsed_table: dict[date, list[str]] = {}
		with open(dest, 'r', encoding='cp1250') as tablefile:
			for row in csv.reader(tablefile, dialect=NBPDialect()):
				if row:
					# Wiersze w tabelach NBP zaczynają się albo od daty, albo od
					# łańcucha `kod ISO`. Daty parsujemy i zapisujemy w słowniku
					# jako klucze a resztę wiersza - jako wartość. Wiersz `kod ISO`
					# zawiera kody ISO 4217 w kolejności występowania w wierszach -
					# - mapujemy kod do kolumny w polu `self._currency_lookup`.
					try:
						row_date = datetime.strptime(row[0], '%Y%m%d')
					except ValueError:
						if row[0] == 'kod ISO':
							for i, v in enumerate(row[1:]):
								self._currency_lookup[v] = i
					else:
						parsed_table.setdefault(row_date.date(), row[1:])

		return parsed_table

	def get_table(self, table: str) -> ExchangeTable:
		"""Pobiera i zwraca pełne dane z podanej tabeli kursów dziennych NBP.

		Funkcja przyjmuje jeden argument, `table`, będący łańcuchem zawierającym
		oznaczenie tabeli NBP i zwraca słownik zawierający dane z tej tabeli.
		W zwracanym słowniku klucze są datami (rok z którego pochodzą jest
		określony przez atrybut `year`) a wartości - wierszami tabeli.
		"""
		if table not in self.CURRENCY_MAP:
			raise ValueError(
				f"oznaczenie '{table}' nie odpowiada "
				"żadnej z tabel publikowanych przez NBP."
			)
		# Już pobrane tabele są zapisane w atrybutach o prefiksie `table_`.
		table_attr: str = 'table_' + table
		saved_table: ExchangeTable|None = getattr(self, table_attr, None)
		if saved_table is not None:
			return saved_table
		else:
			new_table: ExchangeTable = self._download_table(table, self.year)
			setattr(self, table_attr, new_table)
			return new_table

	def get_exchange_ratio(self, currency: str, check_date: date) -> Decimal:
		"""Zwraca kurs danej waluty z danego dnia, wyrażony w PLN.

		Funkcja przyjmuje argumenty:
		`currency` -- Łańcuch będący trzyliterowym kodem ISO 4217 oznaczającym
		walutę, dla jakiej zwrócony będzie kurs.
		`check_date` -- Data określająca dzień, z którego zwrócony będzie kurs.
		"""
		table_mark: str
		for k, v in self.CURRENCY_MAP.items():
			if currency in v:
				table_mark = k
				break
		else:
			raise ValueError(
				f"waluta o symbolu '{currency}' nie figuruje w żadnej z tabel NBP.")

		table: ExchangeTable = self.get_table(table_mark)

		date_row: list[str]
		day_cnt = 0
		# Nie wszystkie daty są uwzględnione w tabeli - w weekendy i święta
		# NBP nie publikuje kursów. Należy wtedy przyjąć ostatni opublikowany
		# kurs. Dlatego odczytując kurs sprawdzamy najpierw dostępność
		# danej daty. Jeśli dla daty nie ma kursu, próbujemy
		# odczytać za dzień poprzedni, następnie za dwa dni wstecz itp.
		# Przyjmujemy, że przerwa w publikowaniu kursów nie powinna być dłuższa
		# niż 4 dni.
		while day_cnt < 4:
			try:
				# Obliczamy, o ile dni wstecz się cofnąć.
				# Dla pierwszego przebiegu pętli będzie to 0.
				date_row = table[check_date - timedelta(day_cnt)]
			except KeyError:
				day_cnt += 1 # Jeśli nie udało się odczytać kursu, cofamy się o dzień.
			else:
				break
		else:
			raise ValueError(
				f"brak wiersza dla daty {check_date!s} "
				f"w tabeli {table_mark.capitalize()}."
			)

		return locale.atof( # type: ignore
			date_row[self._currency_lookup[currency]], Decimal) # type: ignore


class NBPDialect(csv.Dialect):
	"""Dialekt modułu `csv` z biblioteki standardowej
	kompatybilny z formatem tabel kursów dziennych NBP.
	"""
	delimiter: str = ';'
	lineterminator: str = '\r\n'
	quoting: int = csv.QUOTE_NONE


def get_column_index(
	column: str|None = None,
	labels: list[str] = [],
) -> int|None:
	"""Zwraca kolejność kolumny na podstawie nagłówka, liczby lub litery.

	Funkcja przyjmuje dwa argumenty: `column` może być łańcuchem zawierającym
	nagłówek, liczbę lub literę oznaczające kolumnę w zestawie danych
	tabelarycznych. Liczba lub litera są traktowane tak, jak w
	arkuszach kalkulacyjnych, i oznaczają kolejność danej kolumny od lewej
	strony, gdzie kolumna będąca najbardziej po lewej ma oznaczenie `1` lub `A`.
	`labels` przyjmuje listę łańcuchów, gdzie każdy łańcuch to nagłówek kolumny.
	Kolejność łańcuchów w liście musi odpowiadać kolejności kolumn od lewej.
	Tego argumentu nie trzeba podawać, jeśli argument `column` nie jest
	nagłówkiem.
	"""
	if column is None:
		return # type: ignore[return-value]
	if len(column) > 1:
		return labels.index(column)
	if len(column) == 1:
		if column.isdigit():
			return int(column) - 1
		else:
			return string.ascii_lowercase.index(column.lower())
	return # type: ignore[return-value]
