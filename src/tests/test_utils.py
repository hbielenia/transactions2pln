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
"""Testy modułu `utils`.

Zawiera następujące klasy:
`JSONWrapperTestCase` -- Testy obiektów klasy `utils.JSONWrapper`.
`TablesManagerTestCase` -- Testy obiektów klasy `utils.TablesManager`.
`GetColumnIndexTestCase` -- Testy funkcji `utils.get_column_index`.
"""
import json
import locale
import os
import typing
from datetime import date
from decimal import Decimal
from unittest import TestCase
from unittest.mock import Mock, mock_open, patch

from transactions2pln import utils


class JSONWrapperTestCase(TestCase):
	"""Testy obiektów klasy `utils.JSONWrapper`.

	Zawiera metody testujące i wspomagające testowanie poprawności
	obiektów klasy `utils.JSONWrapper`. Udostępnia następujące atrybuty:
	`setUp` -- Metoda przygotowująca środowisko testowe.
	`test_initial_bracket` -- Metoda testująca zapisywanie znaku otwierającego
	tablicę JSON w pliku wyjściowym.
	`test_attributes` -- Metoda testująca udostępniane atrybuty.
	`test_writerow` -- Metoda testująca metodę `writerow()`.
	`test_writeend` -- Metoda testująca metodę `writeend()`.
	"""

	def setUp(self) -> None:
		"""Przygotowuje środowisko testowe.

		Ta metoda jest wywoływana przed każdym wywołaniem którejś z metod
		testujących. Przygotowuje środowisko do testowania obiektów klasy
		`utils.JSONWrapper`. Ustawia następujące atrybuty publiczne:
		`wrapper` -- Obiekt klasy `utils.JSONWrapper` z minimalnym zestawem
		parametrów.
		`wrapper_with_labels` -- Obiekt klasy `utils.JSONWrapper` z testowym
		zestawem nagłówków podanym w argumencie `labels`.
		"""
		self._file: typing.IO[str] = mock_open()()
		self._labels: list[str] = ['a', 'b', 'c']
		self.wrapper: utils.JSONWrapper = utils.JSONWrapper(self._file)
		self.wrapper_with_labels: utils.JSONWrapper = utils.JSONWrapper(
			self._file, self._labels)

	def test_initial_bracket(self) -> None:
		"""Testuje zapisanie znaku otwierającego tablicę.

		Sprawdza, czy utworzony obiekt zapisał w pliku wyjściowym
		znak otwierający tablicę JSON.
		"""
		self.assertEqual(self._file.write.call_args[0][0], '[')

	def test_attributes(self) -> None:
		"""Testuje obecność i zachowanie atrybutów udostępnianych przez
		obiekty klasy `utils.JSONWrapper`.
		"""
		# Zachowanie atrybutu `labels` zależy od tego, czy przy inicjalizacji
		# obiektu podano nagłówki.
		self.assertIsNone(self.wrapper.labels)
		self.assertEqual(self.wrapper_with_labels.labels, self._labels)
		# Atrybuty `writerow()` i `writeend()` powinny być obecne zawsze.
		for wrapper in (self.wrapper, self.wrapper_with_labels):
			with self.subTest(labels=bool(wrapper.labels)):
				self.assertTrue(wrapper.writerow)
				self.assertTrue(wrapper.writeend)

	def test_writerow(self) -> None:
		"""Testuje zapisywanie wiersza danych metodą `writerow()`."""
		testrow: list[str] = ['x', 'y', 'z']
		self.assertIsNone(self.wrapper.writerow(testrow))
		# Weryfikacja zapisu dla obiektu bez nagłówków.
		self.assertIn(
			json.dumps(testrow),
			[i[0][0] for i in self._file.write.call_args_list[-2:]],
		)
		self.assertIsNone(self.wrapper_with_labels.writerow(testrow))
		# Weryfikacja zapisu dla obiektu z nagłówkami.
		self.assertIn(
			json.dumps(dict(zip(self._labels, testrow))),
			[i[0][0] for i in self._file.write.call_args_list[-2:]],
		)

	def test_writeend(self) -> None:
		"""Testuje zapisanie znaku końca tablicy metodą `writeend()`."""
		for wrapper in (self.wrapper, self.wrapper_with_labels):
			with self.subTest(labels=bool(wrapper.labels)):
				self.assertIsNone(wrapper.writeend())
				self.assertEqual(self._file.write.call_args[0][0], ']')


class TablesManagerTestCase(TestCase):
	"""Testy obiektów klasy `utils.TablesManager`.

	Zawiera metody testujące i wspomagające testowanie poprawności
	obiektów klasy `utils.JSONWrapper`. Udostępnia następujące atrybuty:
	`setUp` -- Metoda przygotowująca środowisko testowe.
	`tearDown` -- Metoda czyszcząca środowisko testowe.
	`test_attributes` -- Metoda testująca udostępniane atrybuty.
	`test_get_table` -- Metoda testująca metodę `get_table()`.
	`test_get_nonexistent_table` -- Metoda testująca metodę `get_table()`
	dla nieistniejącej tabeli.
	`test_get_exchange_ratio` -- Metoda testująca metodę `get_exchange_ratio()`.
	`test_get_exchange_ratio_for_incorrect_date` -- Metoda testująca metodę
	`get_exchange_ratio()` dla daty nieobecnej w tabeli testowej.
	`test_get_exchange_ratio_for_nonexistent_currency` -- Metoda testująca
	metodę `get_exchange_ratio()` dla nieistniejącej waluty.
	"""

	def setUp(self) -> None:
		"""Przygotowuje środowisko testowe.

		Ta metoda jest wywoływana przed każdym wykonaniem którejś z metod
		testujących. Przygotowuje środowisko do testowania obiektów klasy
		`utils.TablesManager`. Ustawia następujące atrybuty publiczne:
		`table_path` - Łańcuch zawierający ścieżkę do pliku z testową tabelą
		kursów dziennych NBP.
		`manager` - Testowy obiekt klasy `utils.TablesManager`.
		"""
		# Chcemy nadpisać ustawienia języka, więc zapisujemy obecne
		# żeby potem móc je przywrócić.
		self._locale = locale.getlocale(locale.LC_NUMERIC)
		self._date: date = date(2023, 4, 28) # Testowa data
		# Testowa tabela
		self._table: utils.ExchangeTable = {self._date: [
			'4,1753', '2,7483', '3,0565', '2,5590', '4,5889',
			'4,6619', '5,2005', '83', '083/A/NBP/2023',
		]}
		# Ten obiekt jest normalnie wypełniany przy parsowaniu pliku z tabelą.
		# Ponieważ mockujemy całą metodę `_download_table()`, musimy go również
		# wypełnić danymi.
		self._currency_lookup = {
			k: v for v, k
			in enumerate(('USD', 'AUD', 'CAD', 'NZD', 'EUR', 'CHF', 'GBP'))
		}
		# Mockowanie katalogu tymczasowego, żeby testy nie wchodziły w niechciane
		# interakcje z systemem plików.
		self._tmpdir: typing.Any = Mock(['name'])
		self._tmpdir.name = os.path.join(os.getcwd(), repr(self)[-13:-1])

		# Ustawiamy język na polski.
		locale.setlocale(locale.LC_NUMERIC, 'pl_PL.UTF-8')
		self.manager: utils.TablesManager = utils.TablesManager(
			self._tmpdir, self._date.year) # Testowa instancja `TablesManager`.
		self.manager._download_table = Mock(return_value=self._table)

	def tearDown(self) -> None:
		"""Czyści środowisko testowe po wykonaniu testów.

		Ta metoda jest wywoływana po wykonaniu metody testującej. Odpowiada za
		usunięcie wszelkich efektów ubocznych, jakie mogło mieć wykonanie testu.

		Obecnie jedyne, co robi ta metoda, to przywrócenie ustawień językowych
		zapisanych przez metodę `setUp()` które na czas testów były ustawione
		na język polski.
		"""
		locale.setlocale(locale.LC_NUMERIC, self._locale)

	def test_attributes(self) -> None:
		"""Testuje obecność i wartości atrybutów udostępnianych przez
		obiekty klasy `utils.TablesManager`.
		"""
		self.assertTrue(self.manager.year)
		self.assertEqual(self.manager.year, self._date.year)
		self.assertTrue(self.manager.DOWNLOAD_URL)
		self.assertTrue(self.manager.CURRENCY_MAP)
		self.assertTrue(self.manager.get_table)
		self.assertTrue(self.manager.get_exchange_ratio)

	def test_get_table(self) -> None:
		"""Testuje odczyt danych z tabeli NBP za pomocą metody `get_table()`."""
		self.assertEqual(self.manager.get_table('a'), self._table)

	def test_get_nonexistent_table(self) -> None:
		"""Testuje, czy próba odczytu danych z nieistniejącej tabeli NBP
		zakończy się przewidzianym błędem."""
		self.assertRaises(ValueError, self.manager.get_table, 'x')

	def test_get_exchange_ratio(self) -> None:
		"""Testuje uzyskiwanie kursu wymiany za pomocą metody
		`get_exchange_ratio()`."""
		with patch.object(
			self.manager, '_currency_lookup', self._currency_lookup
		):
			self.assertEqual(
				self.manager.get_exchange_ratio('CHF', self._date),
				Decimal('4.6619'),
			)

	def test_get_exchange_ratio_for_incorrect_date(self) -> None:
		"""Testuje, czy próba uzyskania kursu wymiany dla daty
		której nie ma w tabeli zakończy się przewidzianym błędem."""
		with patch.object(
			self.manager, '_currency_lookup', self._currency_lookup
		):
			self.assertRaises(
				ValueError, self.manager.get_exchange_ratio, 'CHF', date(2024, 4, 28))

	def test_get_exchange_ratio_for_nonexistent_currency(self) -> None:
		"""Testuje, czy próba uzyskania kursu wymiany dla nieistniejącej waluty
		zakończy się przewidzianym błędem."""
		self.assertRaises(
			ValueError, self.manager.get_exchange_ratio, 'T2P', self._date)


class GetColumnIndexTestCase(TestCase):
	"""Testy funkcji `utils.get_column_index`.

	Zawiera metody testujące poprawność działania
	funkcji `get_column_index()` z modułu `utils`.
	Udostępnia następujące atrybuty:
	`test_index_by_label` -- Metoda testująca użycie nagłówka.
	`test_index_by_digit` -- Metoda testująca użycie cyfry.
	`test_index_by_letter` -- Metoda testująca użycie litery.
	`test_empty_input` -- Metoda testująca zachowanie przy podaniu
	pustego łańcucha.
	"""

	def test_index_by_label(self) -> None:
		"""Testuje uzyskiwanie indeksu kolumny poprzez podanie nagłówka."""
		self.assertEqual(utils.get_column_index(
			'sit', ['lorem', 'ipsum', 'dolor', 'sit', 'amet']), 3)

	def test_index_by_digit(self) -> None:
		"""Testuje uzyskiwanie indeksu kolumny poprzez podanie cyfry."""
		self.assertEqual(utils.get_column_index('4', []), 3)

	def test_index_by_letter(self) -> None:
		"""Testuje uzyskiwanie indeksu kolumny poprzez podanie litery."""
		self.assertEqual(utils.get_column_index('F', []), 5)

	def test_empty_input(self) -> None:
		"""Testuje zachowanie funkcji `get_column_index() przy podaniu
		pustego łańcucha."""
		self.assertIsNone(utils.get_column_index('', []))
