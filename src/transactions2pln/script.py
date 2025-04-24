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
"""Funkcje służące do uruchamiania `transactions2pln`
jako programu wiersza poleceń.

Zawiera następujące funkcje:
`run` -- Obsługuje opcje wiersza poleceń i wywołuje funkcję
	`transactions2pln()`.
`transactions2pln` -- Główna funkcja programu, przyjmuje argumenty
	przygotowane przez funkcję `run()`, oblicza i zapisuje wartości transakcji.
"""
import csv
import decimal
import locale
import sys
import typing
from argparse import (
	ArgumentParser,
	FileType,
	Namespace,
)
from datetime import date, datetime, timedelta
from tempfile import TemporaryDirectory

from transactions2pln import exceptions as exc, utils

_ERROR_CODE_MAP: dict[typing.Type[Exception], int] = {
	RuntimeError: 2,
	ValueError: 3,
	exc.ColumnParameterError: 4,
	exc.RowProcessingError: 5,
}


def _str_from_decimal(d: decimal.Decimal) -> str:
	return locale.str(d) # type: ignore


def run() -> int:
	"""Uruchamia funkcję `transactions2pln` jako program wiersza poleceń.

	Ta funkcja ustawia opcje wiersza poleceń i pozwala na ich przekazanie
	podczas uruchamiania modułu `transactions2pln` jako programu. Następnie
	wywołuje funkcję `transactions2pln` i przekazuje jej otrzymane opcje.

	Zwraca 0 jeśli wykonanie zakończyło się sukcesem, lub jedną z
	poniższych wartości jeśli napotka błąd:
	1 -- Błąd nie pasujący do żadnej z pozostałych wartości.
	2 -- Błąd środowiska uruchomieniowego lub systemu.
	3 -- Błąd pliku wejściowego lub wyjściowego.
	4 -- Błąd opcji wiersza poleceń.
	5 -- Błąd przetwarzania danych.

	Dokładniejsze komunikaty błędów są zapisywane do standardowego strumienia
	błędów.
	"""

	argparser: ArgumentParser = ArgumentParser(
		prog="transactions2pln",
		description="Dodaje wartości w PLN do pliku CSV z transakcjami.",
	)

	arggroup_io: typing.Any = argparser.add_argument_group(
		"Opcje wejścia i wyjścia")
	arggroup_io.add_argument(
		'input',
		type=FileType('r'),
		help="Ścieżka do pliku CSV.",
	)
	arggroup_io.add_argument(
		'-o', '--output',
		type=FileType('w'),
		help="""
			Ścieżka do pliku wynikowego. Domyślnie:
			pusta, program zwraca wynik do wyjścia konsoli.
		""",
	)
	arggroup_io.add_argument(
		'-j', '--json',
		action='store_true',
		help="Zwróć wyniki w formacie JSON.",
	)

	arggroup_parse: typing.Any = argparser.add_argument_group(
		"Opcje parsowania pliku wejściowego")
	arggroup_parse.add_argument(
		'-a', '--amount-column',
		help="""
			Kolumna zawierająca kwotę transakcji - może być podana jako
			nagłówek, liczba albo litera. Domyślnie: ostatnia kolumna w pliku.
		""",
	)
	arggroup_parse.add_argument(
		'-c', '--currency',
		default='USD',
		help="""
			Waluta transakcji. Może być podana jako trzyliterowy kod,
			nagłówek kolumny, liczba albo litera. Domyślnie: USD.
		""",
	)
	arggroup_parse.add_argument(
		'-d', '--date-column',
		default='',
		help="""
			Kolumna zawierająca datę transakcji - może być podana jako
			nagłówek, liczba albo litera. Domyślnie: program spróbuje
			znaleźć automatycznie dla każdego wiersza.
		""",
	)
	arggroup_parse.add_argument(
		'-f', '--date-format',
		default='%%x',
		help="""
			Format dat używanych w kolumnie z datą transakcji. Ten parametr
			używa formatu strftime() udokumentowanego pod adresem
			https://docs.python.org/3.11/library/datetime.html#strftime-and-strptime-format-codes
			Domyślnie: %%x
		"""
	)
	arggroup_parse.add_argument(
		'-l', '--no-labels',
		dest='labels',
		action='store_false',
		help="""
			Nie traktuj pierwszego wiersza jako nagłówków kolumn. Z tym parametrem
			program traktuje całą zawartość pliku wejściowego jako dane w kolumnach.
		""",
	)

	args: Namespace = argparser.parse_args()
	tmpdir: TemporaryDirectory = TemporaryDirectory() # type: ignore[type-arg]
	decimal.getcontext().prec = 10

	try:
		transactions2pln(args, tmpdir)
		args.input.close()
	except Exception as err:
		args.input.close()
		if sys.flags.dev_mode:
			raise
		else:
			print(str(err), file=sys.stderr)
			return _ERROR_CODE_MAP.get(err.__class__, 1)
	else:
		return 0


def transactions2pln(
		args: Namespace,
		tmpdir: TemporaryDirectory, # type: ignore[type-arg]
	) -> None:
	"""Oblicza wartości w PLN dla transakcji w innych walutach
	i dodaje je do pliku wejściowego.

	Funkcja przyjmuje dwa argumenty: `args` zawierający argumenty przekazane
	przez interfejs wiersza poleceń i `tmpdir` będący tymczasową ścieżką
	do użycia jako katalog roboczy.

	Argument `args` powinien posiadać następujące atrybuty:
	`input` -- Otwarty deskryptor pliku zawierającego transakcje
	w formacie CSV (**plik wejściowy**).
	`output` -- Otwarty deskryptor pliku do którego funkcja zapisze
	transakcje z pliku wejściowego rozszerzone o wartości w PLN
	(**plik wyjściowy**).
	`date_format` -- Łańcuch opisujący format w jakim w pliku wejściowym
	zapisane są daty transakcji, zgodny z `datetime.strftime`.
	`date_column` -- Łańcuch oznaczajacy kolumnę w pliku wejściowym
	zawierającą daty transakcji; może być to litera, liczba lub nagłówek
	jeśli atrybut `labels` zawiera wartość `True`.
	`currency` -- Łańcuch oznaczający kolumnę w pliku wejściowym
	zawierającą walutę danej transakcji (patrz opis atrybutu `date_column`)
	albo trzyliterowy kod zgodny z ISO 4217.
	`amount_column` -- Łańcuch oznaczający kolumnę w pliku wejściowym
	zawierającą wartości transakcji (patrz opis atrybutu `date_column`).
	`json` -- Wartość logiczna, jeżeli jest to `True` funkcja zapisuje
	plik wyjściowy w formacie JSON.
	`labels` -- Wartość logiczna, jeżeli jest to `True` pierwsza linijka
	pliku wejściowego jest traktowana jako nagłówki kolumn a nie zawartość.
	"""
	# `locale.getlocale()` zwraca łańcuch lub krotkę której elementami
	# mogą być łańcuchy lub `None`. W tym bloku uzyskujemy jednolity łańcuch
	# z każdej możliwej struktury danych.
	current_locale: str|tuple[str] = locale.getlocale() # type: ignore
	current_locale_string: str
	# `str.join()` połączy zarówno elementy tupli, jak i łańcucha.
	# Lambda zamienia `None` na pusty łańcuch.
	current_locale_string = ''.join(
		map(lambda s: s or '', current_locale)
	).lower()

	if any((
		current_locale_string.startswith('pl'),
		current_locale_string.startswith('polish')
	)):
		locale.setlocale(locale.LC_NUMERIC, locale.getlocale())
	else:
		raise RuntimeError(
			"Program działa prawidłowo tylko "
			"gdy język systemu jest ustawiony na polski.",
		)

	input = csv.reader(args.input)
	current_row: int = 0

	labels: list[str] = []
	if args.labels:
		try:
			# Dodajemy nagłówki dla kolumn, które wypełniamy przetwarzając dane.
			labels = next(input) + ["kurs do PLN", "kwota w PLN"]
		except StopIteration as err:
			# Próba wczytania nagłówków to jedyna sytuacja, gdy przeszkadza nam
			# pusty plik. Jeżeli nie ma nagłówków, po prostu nic nie zwracamy
			# (pusty input -> pusty output).
			raise ValueError(
				f"Błąd przy próbie odczytu z pliku {args.input.name}: "
				"plik wygląda na pusty."
			) from err
		else:
			current_row += 1

	# Waluta może być podana jako kod ISO 4217 albo odwołanie do kolumny.
	# W tym bloku tworzymy funkcję `get_currency()` która będzie nam zawsze
	# zwracać właściwy kod.
	if all((
		args.currency.isupper(),
		len(args.currency) == 3,
		args.currency not in labels,
	)):
		# Waluta została podana jako kod - `get_currency()` po prostu go zwraca.
		def get_currency(row: list[str]) -> str: return str(args.currency)
	else:
		# Waluta podana jako odwołanie do kolumny. Najpierw musimy uzyskać
		# indeks kolumny.
		try:
			currency_column_idx: int|None = utils.get_column_index(
				args.currency, labels)
			assert currency_column_idx is not None
		except (AssertionError, ValueError) as err:
			# Jeżeli nie możemy uzyskać indeksu, zwracamy błąd.
			raise exc.ColumnParameterError('currency', args.currency) from err
		# W tym wariancie, `get_currency()` dynamicznie odczytuje walutę
		# dla każdego wiersza.
		def get_currency(row: list[str]) -> str: return row[currency_column_idx]

	# Wartość i data mogą być podane tylko jako odwołania do kolumny,
	# więc nie wymagają takich akrobacji jak waluta.
	try:
		amount_column_idx: int|None = utils.get_column_index(
			args.amount_column, labels)
	except ValueError as err:
		raise exc.ColumnParameterError('amount-column', args.amount_column) from err

	try:
		date_column_idx: int|None = utils.get_column_index(args.date_column, labels)
	except ValueError as err:
		raise exc.ColumnParameterError('date-column', args.date_column) from err

	output: typing.Any = args.output or sys.stdout
	if args.json:
		output = utils.JSONWrapper(output, labels)
	else:
		output = csv.writer(output)
		if args.labels:
			output.writerow(labels)

	# W tej pętli `for` odbywa się przetwarzanie danych wejściowych.
	# Zwróć uwagę, że jest dłuższa niż może się wydawać.
	tables: utils.TablesManager
	year: int|None = None
	for row in input:
		current_row += 1
		row_date: date
		if date_column_idx is not None:
			# Jeżeli mamy kolumnę z datą, próbujemy odczytać jej wartość.
			try:
				row_date = datetime.strptime(
					row[date_column_idx],
					args.date_format,
				).date()
			except ValueError as err:
				date_column_num = date_column_idx + 1
				raise exc.RowProcessingError(
					current_row,
					f"wartość kolumny {date_column_num!s} nie pasuje "
					"do formatu określonego w --date-format",
				) from err
		else:
			# Jeżeli nie mamy kolumny, sprawdzamy każde kolejne pole
			# w wierszu danych.
			for cell in row:
				try:
					row_date = datetime.strptime(cell, args.date_format).date()
				except ValueError:
					continue
				else:
					break
			if not row_date:
				raise exc.RowProcessingError(
					current_row,
					"nie podano parametru --date-column i żadna wartość "
					"nie pasuje do formatu określonego w --date-format.",
				)
		# Jeżeli data wypada w sobotę i niedzielę, zmieniamy ją na piątek.
		# Odjęcie 4 od numeru dnia tygodnia oznacza, że sobota będzie miałą
		# wartość 1, niedziela 2, pozostałe dni tygodnia - 0 i mniej.
		# Wywołanie `max()` ustawia 0 dla pozostałych dni tygodnia.
		# Następnie odejmujemy tyle dni, ile wynosi ta wartość, a więc
		# jeżeli była to sobota lub niedziela, uzyskujemy ostatni piątek.
		weekend_days: int = max(row_date.weekday() - 4, 0)
		week_date: date = row_date - timedelta(days=weekend_days)

		# Ustawiamy rok, ale tylko, jeżeli nie został jeszcze ustawiony.
		if year is None:
			year = week_date.year
			tables = utils.TablesManager(tmpdir, year)

		currency: str = get_currency(row)
		try:
			exchange: decimal.Decimal = tables.get_exchange_ratio(
				currency, week_date)
		except Exception as err:
			raise exc.RowProcessingError(current_row, str(err)) from err

		amount: str|decimal.Decimal
		if amount_column_idx:
			amount = row[amount_column_idx]
		else:
			# Jeżeli nie podano kolumny z wartością, przyjmujemy domyślnie,
			# że jest nią ostatnia kolumna w pliku wejściowym.
			amount = row[-1]

		# Obliczanie kwoty transakcji w PLN.
		try:
			amount = decimal.Decimal(amount)
			amount_pln: decimal.Decimal = (amount * exchange).quantize(
				decimal.Decimal('0.01'))
		except decimal.InvalidOperation as err:
			raise exc.RowProcessingError(
				current_row,
				f"kwota {amount!s} przekracza ustawioną precyzję "
				"działań arytmetycznych"
			) from err
		# Dodajemy uzyskany kurs i kwotę transakcji do wiersza danych...
		row.append(_str_from_decimal(exchange))
		row.append(_str_from_decimal(amount_pln))
		# ...i zapisujemy w pliku wyjściowym.
		try:
			output.writerow(row)
		except AttributeError:
			output.write(''.join(row))
	# Tutaj kończy się pętla `for`.

	if args.json:
		output.writeend()
	if args.output:
		args.output.close()
