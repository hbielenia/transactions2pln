**Note to English-speaking users**: Contrary to widely established practice,
this program doesn't communicate with user in English. All user-facing
messages, as well as internal and external documentation, are written
in Polish and currently have no translations to other languages available.
This is because this program is assumed to be useful mostly for
Polish speakers. If you are an English language user who nonetheless thinks
it would be useful for this program to support other languages than Polish,
please raise an issue and describe your use case there.

================
transactions2pln
================
Niniejszy program przyjmuje plik wejściowy zawierający listę
transakcji finansowych w formacie CSV, odczytuje z niego dane i zwraca je
w formacie CSV lub JSON, wzbogacone o wartość każdej transakcji
w polskich złotych (PLN) i kurs wymiany NBP obowiązujący w dniu transakcji.

Podstawowe użycie
=================
::

	transactions2pln -o <PLIK WYJŚCIOWY> <PLIK WEJŚCIOWY>

To polecenie odczyta dane z pliku wejściowego i zapisze je w pliku wyjściowym,
wraz z danymi o wartości i kursie wymiany w PLN. Jako kwota transakcji
zostanie przyjęta ostatnia kolumna w pliku wejściowym, jako waluta
zostanie przyjęty dolar amerykański a data transakcji będzie wyszukana
automatycznie w każdym wierszu danych.

W większości przypadków użytkownik będzie chciał zmienić te domyślne
założenia. Opis wszystkich opcji, jakie na to pozwalają, można uzyskać
poleceniem ``transactions2pln -h``.

Zgłaszanie błędów
=================
Jeżeli zauważysz błędne lub niezgodne z opisem działanie programu,
możesz je zgłosić pod adresem https://github.com/hbielenia/transactions2pln/issues.
Kliknij przycisk "New issue" i opisz w formularzu zauważony problem
tak dokładnie, jak to możliwe. Językiem używanym do komunikacji
jest polski.

Nie używaj zgłoszeń błędów do pytań o pomoc lub działanie programu. Służy do
tego sekcja "Discussions_".

Udział w tworzeniu
==================
Jeśli znasz język programowania Python i chcesz zaproponować zmianę lub
poprawkę, możesz to zrobić zgodnie z instrukcjami w pliku
``DEVELOPMENT.rst``.

Prawa autorskie
===============
Program ``transactions2pln`` jest udostępniony na warunkach
Licencji Publicznej Unii Europejskiej w wersji 1.2. Pełen tekst licencji
w języku polskim znajduje się w pliku ``LICENCE.txt``. Równoważny tekst
w każdym oficjalnym języku Unii Europejskiej można znaleźć na stronie
https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12.

Jeśli zauważysz, że powyższy link nie działa, zgłoś to proszę jako błąd
zgodnie z opisem w sekcji `Zgłaszanie błędów`_.

.. _Discussions: https://github.com/hbielenia/transactions2pln/discussions
