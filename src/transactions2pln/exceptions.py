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
"""Klasy wyjątków do obsługi powtarzalnych błędów.

Zawiera następujące klasy:
`ColumnParameterError` -- Oznacza błędną wartość parametru wiersza poleceń
mającego wskazać kolumnę w pliku wejściowym.
`RowProcessingError` -- Oznacza napotkanie innego błędu przy przetwarzaniu
pliku wejściowego.
"""


class ColumnParameterError(ValueError):
	"""Błąd informujący o niewłaściwej wartości parametru wiersza poleceń
	wskazującego na kolumnę w pliku wejściowym.
	"""

	def __init__(self, param_name: str, param_value: str):
		"""Metoda inicjalizująca obiekty klasy `ColumnParameterError`.

		Przyjmuje następujące parametry:
		`param_name` -- Łańcuch zawierający nazwę błędnego parametru.
		`param_value` -- Łańcuch zawierający błędną wartość.
		"""
		return super().__init__(
			f"Błąd parametru --{param_name}: podana wartość '{param_value}'"
			"nie odpowiada nagłówkowi żadnej kolumny."
		)


class RowProcessingError(RuntimeError):
	"""Generyczny błąd przetwarzania danego wiersza w pliku wejściowym.

	Umożliwia podanie numeru wiersza w komunikacie błędu.
	"""

	def __init__(self, row_number: int, message: str):
		"""Metoda inicjalizująca obiekty klasy `RowProcessingError`.

		Przyjmuje następujące parametry:
		`row_number` -- Liczba całkowita oznaczająca numer wiersza
		w którym wystąpił błąd.
		`message` -- Łańcuch zawierający komunikat błędu który wystąpił
		w podanym wierszu.
		"""
		return super().__init__(
			f"Błąd podczas przetwarzania wiersza {row_number!s}: " + message
		)
