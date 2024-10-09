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
"""Testy głównego modułu programu.

Ponieważ większość kodu jest w pozostałych modułach, testujemy tutaj
jedynie wyświetlanie pomocy dotyczącej przyjmowanych argumentów.
Moduł zawiera jedną klasę:
`MainTestCase` -- Zawiera testy głównego modułu programu.
"""
import sys
import subprocess
from pathlib import Path
from unittest import TestCase


class MainTestCase(TestCase):
	"""Testy głównego modułu programu.

	Klasa ta udostępnia tylko jeden atrybut, metodę `test_help()`
	która sprawdza poprawność informacji zwracanych przez
	uruchomienie programu z argumentem `-h`.
	"""

	def test_help(self) -> None:
		"""Testuje, czy informacje zwracane przez uruchomienie programu
		z argumentem `-h` są zgodne z oczekiwanymi."""
		root_path = Path(__file__).parent.parent
		run_output: subprocess.CompletedProcess = subprocess.run(
			[sys.executable, '-m', 'transactions2pln', '-h'],
			cwd=root_path,
			capture_output=True,
		)
		# Ta linijka sprawdza, czy obecny jest argument pozycyjny `input`.
		self.assertRegex(run_output.stdout, br'  input {17}')
		self.assertIn(b'-o OUTPUT, --output OUTPUT', run_output.stdout)
		self.assertIn(b'-j, --json', run_output.stdout)
		self.assertIn(
			b'-a AMOUNT_COLUMN, --amount-column AMOUNT_COLUMN', run_output.stdout)
		self.assertIn(b'-c CURRENCY, --currency CURRENCY', run_output.stdout)
		self.assertIn(
			b'-d DATE_COLUMN, --date-column DATE_COLUMN', run_output.stdout)
		self.assertIn(
			b'-f DATE_FORMAT, --date-format DATE_FORMAT', run_output.stdout)
		self.assertIn(b'-l, --no-labels', run_output.stdout)
