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
"""Testy modułu `script`.

Zawiera następujące klasy:
`TemporaryDirectoryMockMixin` - Klasa domieszkowa dodająca mockowanie
katalogu tymczasowego do innych klas zawierających testy.
`BaseScriptTestCase` -- Klasa bazowa dla innych klas zawierających testy.
`RunScriptTestCase` -- Klasa zawierająca testy funkcji `script.run()`.
`Transactions2PLNTestCase` -- Klasa zawierająca testy funkcji
`script.transactions2pln()`.
`ScriptLocaleTestCase` -- Klasa zawierająca testy sprawdzające zachowanie
przy innym niż Polski języku systemowym.
"""
import json
import locale
import os
import typing
from unittest import TestCase
from unittest.mock import MagicMock, Mock, mock_open, patch

from transactions2pln import script


class TemporaryDirectoryMockMixin:
	"""Dodaje mockowanie katalogu tymczasowego w testach jednostkowych.

	Niniejsza klasa stanowi klasę domieszkową przewidzianą dla
	klas dziedziczących z `unittest.TestCase`. Dodaje ona w metodzie `setUp()`
	tworzenie atrybutu `_tmpdir`, którego wartością jest obiekt klasy `Mock`
	imitujący katalog tymczasowy tworzony przez moduł `tempfile` z biblioteki
	standardowej.
	"""

	def setUp(self) -> None:
		"""Przygotowuje środowisko testowe dla testów używających modułu
		`unittest`.

		Metoda ta jest wywoływana podczas wykonywania testów z użyciem klas
		`unittest.TestCase`. W klasach dziedziczących z tychże klas odpowiada ona
		za przygotowanie środowiska testowego. W niniejszej klasie tworzy ona
		obiekt klasy `Mock` imitujący katalog tymczasowy i przypisuje go
		do atrybutu `_tmpdir`.
		"""
		self._tmpdir: typing.Any = Mock(['name'])
		self._tmpdir.name = os.path.join(
			os.getcwd(),
			repr(self).replace('=', '')[-13:-1],
		)


class BaseScriptTestCase(TemporaryDirectoryMockMixin, TestCase):
	"""Klasa bazowa dla testów modułu `script`.

	Zawiera metody pomocnicze do przeprowadzania testów modułu `script`.
	Udostępnia następujące atrybuty:
	`setUp` -- Metoda przygotowująca środowisko testowe.
	`tearDown` -- Metoda czyszcząca środowisko testowe.
	`get_args_mock`-- Metoda zwracająca makietę obiektu `argparse.Namespace`.
	"""

	def setUp(self) -> None:
		"""Przygotowuje środowisko testowe.

		Ta metoda jest wywoływana przed każdym wykonaniem którejś z metod
		testujących. Przygotowuje środowisko do testowania modułu `script`.
		Ustawia następujące atrybuty publiczne:
		`maxDiff` -- Określa, jak długi fragment różnic wykrytych
		przy porównywaniu w testach rzeczywistego stanu z przewidywanym
		będzie wypisany w konsoli. Ta metoda ustawia ten atrybut na `None`,
		co oznacza nieograniczoną długość - w przypadku nieudanych testów
		wypisywane są wszystkie różnice.
		`mock_open` -- Makieta wbudowanej funkcji `open()` zwracająca dane
		z testowej tabeli kursów NBP.
		`test_file` -- Deskryptor pliku z testowymi danymi transakcji.
		"""
		super().setUp()
		self.maxDiff: None = None
		self._test_data_dir: str = os.path.join(os.path.dirname(__file__), 'data')
		self.test_file: typing.IO[str] = open(
			os.path.join(self._test_data_dir, 'transactions.csv'))
		with open(
			os.path.join(self._test_data_dir, 'nbp_table.csv'),
			'r',
			encoding='cp1250'
		) as f:
			self.mock_open: typing.IO[str] = mock_open(read_data=f.read())

	def tearDown(self) -> None:
		"""Czyści środowisko testowe.

		Ta metoda jest wywoływana po wykonaniu metody testującej. Odpowiada za
		usunięcie wszelkich efektów ubocznych, jakie mogło mieć wykonanie testu.

		Obecnie jej jedyne zadanie to zamknięcie deksryptora pliku `test_file`."""
		self.test_file.close()

	def get_args_mock(self) -> Mock:
		"""Tworzy makietę obiektu `argparse.Namespace` której można użyć
		jako argumentu funkcji `script.transactions2pln()`."""
		args_mock: Mock = Mock()
		args_mock.input = self.test_file
		args_mock.output = MagicMock()
		args_mock.date_format = '%Y/%m/%d'
		args_mock.date_column = '4'
		args_mock.currency = '5'
		args_mock.amount_column = '6'
		args_mock.json = False
		args_mock.labels = False
		return args_mock


class RunScriptTestCase(BaseScriptTestCase):
	"""Testy funkcji `script.run()`.

	Zawiera metody testujące i wspomagające testowanie funkcji
	`script.transactions2pln()`. Udostępnia następujące atrybuty:
	`test_error_file` -- Metoda testująca obsługę błędów związanych z plikami.
	`test_error_command` -- Metoda testująca obsługę błędów związanych z
	argumentami wiersza poleceń.
	`test_error_processing` -- Metoda testująca obsługę błędów
	przy przetwarzaniu danych.
	`test_success` -- Metoda testująca poprawność działania przy odpowiednim
	zestawie parametrów i środowisku.
	"""

	def test_error_file(self) -> None:
		"""Testuje obsługę błędów wywołanych problemami z plikami."""
		args_mock: Mock = Mock()
		args_mock.input = mock_open()()
		args_mock.labels = True

		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			with patch(
				'transactions2pln.script.TemporaryDirectory',
				return_value=self._tmpdir
			):
				# Patchujemy również metodę `parse_args()`
				# klasy `argparse.ArgumentParser` w module `script`,
				# gdyż to testowana funkcja `script.run()` ją wywołuje.
				with patch.object(
					script.ArgumentParser,
					'parse_args',
					return_value=args_mock,
				):
					self.assertEqual(3, script.run())

	def test_error_command(self) -> None:
		"""Testuje obsługę błędów wywołanych błędnymi argumentami
		wiersza poleceń."""
		args_mock: Mock = self.get_args_mock()
		args_mock.currency = ''

		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			with patch(
				'transactions2pln.script.TemporaryDirectory',
				return_value=self._tmpdir
			):
				# Patchujemy również metodę `parse_args()`
				# klasy `argparse.ArgumentParser` w module `script`,
				# gdyż to testowana funkcja `script.run()` ją wywołuje.
				with patch.object(
					script.ArgumentParser,
					'parse_args',
					return_value=args_mock,
				):
					self.assertEqual(4, script.run())

	@patch('transactions2pln.utils.urlretrieve')
	def test_error_processing(self, _) -> None:
		"""Testuje obsługę błędów przy przetwarzaniu danych."""
		args_mock: Mock = self.get_args_mock()
		args_mock.date_format = ''

		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			with patch(
				'transactions2pln.script.TemporaryDirectory',
				return_value=self._tmpdir
			):
				# Patchujemy również metodę `parse_args()`
				# klasy `argparse.ArgumentParser` w module `script`,
				# gdyż to testowana funkcja `script.run()` ją wywołuje.
				with patch.object(
					script.ArgumentParser,
					'parse_args',
					return_value=args_mock,
				):
					self.assertEqual(5, script.run())

	@patch('transactions2pln.utils.urlretrieve')
	def test_success(self, _) -> None:
		"""Testuje działanie przy poprawnych parametrach."""
		args_mock: Mock = self.get_args_mock()

		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			with patch(
				'transactions2pln.script.TemporaryDirectory',
				return_value=self._tmpdir
			):
				# Patchujemy również metodę `parse_args()`
				# klasy `argparse.ArgumentParser` w module `script`,
				# gdyż to testowana funkcja `script.run()` ją wywołuje.
				with patch.object(
					script.ArgumentParser,
					'parse_args',
					return_value=args_mock,
				):
					self.assertEqual(0, script.run())

		# Porównanie danych zapisanych do makiety pliku wynikowego z oczekiwanymi.
		with open(
			os.path.join(self._test_data_dir, 'transactions_output.csv'),
			newline='',
		) as f:
			self.assertEqual(
				''.join([c[0][0] for c in args_mock.output.write.call_args_list]),
				f.read(),
			)


class Transactions2PLNTestCase(BaseScriptTestCase):
	"""Testy funkcji `script.transactions2pln()`.

	Zawiera metody testujące i wspomagające testowanie funkcji
	`script.transactions2pln()`. Udostępnia następujące atrybuty:
	`test_json` -- Metoda testująca zapisywanie w formacie JSON.
	`test_amount_column_as_letter` -- Metoda testująca oznaczanie
	kolumny z kwotami literą.
	`test_amount_column_fallback` -- Metoda testująca używanie ostatniej kolumny
	jako kolumny z kwotami.
	`test_currency_as_code` -- Metoda testująca oznaczanie waluty kodem ISO.
	`test_date_column_as_letter` -- Metoda testująca oznaczanie
	kolumny z datami literą.
	`test_labels` -- Metoda testująca obsługę nagłówków.
	"""

	@patch('transactions2pln.utils.urlretrieve')
	def test_json(self, _) -> None:
		"""Testuje zapisywanie danych w formacie JSON."""
		args_mock: Mock = self.get_args_mock()
		args_mock.json = True

		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			# Przy prawidłowym wykonaniu, funkcja powinna zwrócić `None`.
			self.assertIsNone(script.transactions2pln(args_mock, self._tmpdir))

		# Porównanie danych zapisanych do makiety pliku wynikowego z oczekiwanymi.
		with open(
			os.path.join(self._test_data_dir, 'transactions_output.json'),
		) as transactions_output:
			self.assertEqual(
				json.loads(
					''.join([c[0][0] for c in args_mock.output.write.call_args_list])),
				json.load(transactions_output),
			)

	@patch('transactions2pln.utils.urlretrieve')
	def test_amount_column_as_letter(self, _) -> None:
		"""Testuje przyjmowanie litery jako oznaczenia kolumny z kwotami."""
		args_mock: Mock = self.get_args_mock()
		args_mock.amount_column = 'F'

		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			# Przy prawidłowym wykonaniu, funkcja powinna zwrócić `None`.
			self.assertIsNone(script.transactions2pln(args_mock, self._tmpdir))

		# Porównanie danych zapisanych do makiety pliku wynikowego z oczekiwanymi.
		with open(
			os.path.join(self._test_data_dir, 'transactions_output.csv'),
			newline='',
		) as f:
			self.assertEqual(
				''.join([c[0][0] for c in args_mock.output.write.call_args_list]),
				f.read(),
			)

	@patch('transactions2pln.utils.urlretrieve')
	def test_amount_column_fallback(self, _) -> None:
		"""Testuje działanie domyślnego odczytywania ostatniej kolumny
		jako kolumny z kwotami."""
		args_mock: Mock = self.get_args_mock()
		args_mock.amount_column = None

		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			# Przy prawidłowym wykonaniu, funkcja powinna zwrócić `None`.
			self.assertIsNone(script.transactions2pln(args_mock, self._tmpdir))

		# Porównanie danych zapisanych do makiety pliku wynikowego z oczekiwanymi.
		with open(
			os.path.join(self._test_data_dir, 'transactions_output.csv'),
			newline='',
		) as f:
			self.assertEqual(
				''.join([c[0][0] for c in args_mock.output.write.call_args_list]),
				f.read(),
			)

	@patch('transactions2pln.utils.urlretrieve')
	def test_currency_as_code(self, _) -> None:
		"""Testuje przyjmowanie kodu ISO 4217 jako oznaczenia kolumny z walutą."""
		args_mock: Mock = self.get_args_mock()
		args_mock.currency = 'USD'

		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			# Przy prawidłowym wykonaniu, funkcja powinna zwrócić `None`.
			self.assertIsNone(script.transactions2pln(args_mock, self._tmpdir))
		# Porównanie danych zapisanych do makiety pliku wynikowego z oczekiwanymi.
		self.assertEqual(
			''.join([c[0][0] for c in args_mock.output.write.call_args_list]),
			''.join((
				'34567,Global Innovations,CGLB,2023/04/18,CAD,6178.23,"4,2151","26041,86"\r\n',  # noqa: E501
				'90123,Acme Corp,AACM,2023/04/21,AUD,1563.87,"4,2006","6569,19"\r\n',
				'156890,Theta Corporation,THC,2023/04/26,USD,1893.65,"4,1557","7869,44"\r\n',  # noqa: E501
				'212456,Acme Corp,ACM,2023/05/02,USD,4356.12,"4,1823","18218,6"\r\n',
				'278012,Global Innovations,GLB,2023/05/08,GBP,947.21,"4,1384","3919,93"\r\n',  # noqa: E501
				'334678,Zenith Solutions,ZEN,2023/05/11,CHF,241.71,"4,1414","1001,02"\r\n',
			)),
		)

	@patch('transactions2pln.utils.urlretrieve')
	def test_date_column_as_letter(self, _) -> None:
		"""Testuje przyjmowanie litery jako oznaczenia kolumny z datami."""
		args_mock: Mock = self.get_args_mock()
		args_mock.date_column = 'D'

		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			# Przy prawidłowym wykonaniu, funkcja powinna zwrócić `None`.
			self.assertIsNone(script.transactions2pln(args_mock, self._tmpdir))

		# Porównanie danych zapisanych do makiety pliku wynikowego z oczekiwanymi.
		with open(
			os.path.join(self._test_data_dir, 'transactions_output.csv'),
			newline='',
		) as f:
			self.assertEqual(
				''.join([c[0][0] for c in args_mock.output.write.call_args_list]),
				f.read(),
			)

	@patch('transactions2pln.utils.urlretrieve')
	def test_labels(self, _) -> None:
		"""Testuje obsługę nagłówków."""
		args_mock: Mock = self.get_args_mock()
		args_mock.labels = True
		args_mock.amount_column = 'Value'
		args_mock.currency = 'Currency'
		args_mock.date_column = 'Date'

		# Testuje błąd na pustym pliku wejściowym.
		args_mock.input = mock_open()()
		# Po spatchowaniu, open() zwraca zawsze zawartość pliku data/nbp_table.csv
		with patch('builtins.open', self.mock_open):
			self.assertRaises(
				ValueError, script.transactions2pln, args_mock, self._tmpdir)

		# Testuje poprawne przetworzenie pliku z nagłówkami.
		args_mock.input = open(
			os.path.join(self._test_data_dir, 'transactions_with_labels.csv'))
		with patch('builtins.open', self.mock_open):
			self.assertIsNone(script.transactions2pln(args_mock, self._tmpdir))

		# Porównanie danych zapisanych do makiety pliku wynikowego z oczekiwanymi.
		labels_output: str = 'ID,Name,Symbol,Date,Currency,Value,kurs do PLN,kwota w PLN\r\n' # noqa: E501
		with open(
			os.path.join(self._test_data_dir, 'transactions_output.csv'),
			newline='',
		) as transactions_output:
			self.assertEqual(
				''.join([c[0][0] for c in args_mock.output.write.call_args_list]),
				labels_output + transactions_output.read(),
			)


class ScriptLocaleTestCase(TemporaryDirectoryMockMixin, TestCase):
	"""Testy zachowania modułu `script` przy niewspieranych ustawieniach języka.

	Testuje, czy funkcja `script.transactions2pln()` zwraca błąd
	przy uruchomieniu jej z innym językiem systemowym niż polski.
	Udostępnia następujące atrybuty:
	`setUp` -- Metoda przygotowująca środowisko testowe.
	`tearDown` -- Metoda czyszcząca środowisko testowe.
	`test_locale_not_polish` -- Metoda testująca zwracanie błędu.
	"""

	def setUp(self) -> None:
		"""Przygotowuje środowisko testowe.

		Ta metoda jest wywoływana przed każdym wykonaniem metody testującej.
		Przygotowuje środowisko testowe, zapisując obecne ustawienia językowe
		jako atrybut `saved_locale`.
		"""
		super().setUp()
		self.saved_locale = locale.getlocale(locale.LC_CTYPE)
		locale.setlocale(locale.LC_CTYPE, 'C')

	def tearDown(self) -> None:
		"""Czyści środowisko testowe.

		Ta metoda jest wywoływana po każdym wykonaniu metody testującej.
		Czyści środowisko testowe poprzez przywrócenie ustawień językowych
		zapisanych jako atrybut `saved_locale`.
		"""
		locale.setlocale(locale.LC_CTYPE, self.saved_locale)

	@patch.object(script.ArgumentParser, 'parse_args')
	def test_locale_not_polish(self, _) -> None:
		"""Testuje błędy przy wykonywaniu z językiem innym niż polski.

		Sprawdza, czy funkcja `script.run()` zwraca kod błędu 2
		a `script.transactions2pln()` błąd `RuntimeError` przy próbie wykonania
		z językiem systemowym innym niż polski.
		"""
		with patch(
			'transactions2pln.script.TemporaryDirectory',
			return_value=self._tmpdir
		):
			self.assertEqual(2, script.run())
			self.assertRaises(
				RuntimeError, script.transactions2pln, Mock(), self._tmpdir)
