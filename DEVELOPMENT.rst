========================
Ustawienia developerskie
========================
Ten dokument opisuje konfigurację środowiska programistycznego
do pracy nad programem ``transactions2pln``.

Wymagania systemowe
===================
Praca nad ``transactions2pln`` wymaga następujących programów:

- Docker_,
- Git_,
- Python_ w wersji 3.11.

Ułatwieniem w pracy nad ``transactions2pln`` jest też program Task_,
ale nie jest on niezbędny.

Repozytorium kodu źródłowego
============================
``transactions2pln`` jest rozwijany w serwisie GitHub_. Aby móc zgłaszać
poprawki lub zmiany do oficjalnego wydania programu, niezbędne jest konto
użytkownika w tym serwisie. Kod źródłowy dostępny jest jednakże
bez konieczności posiadania konta pod adresem
https://github.com/hbielenia/transactions2pln - jest to tzw. repozytorium,
wykorzystujące system kontroli wersji Git_.

Aby uzyskać lokalną kopię repozytorium należy je sklonować, zgodnie z
`tą instrukcją <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository>_`.
Jeżeli chcesz zgłaszać poprawki lub zmiany, musisz wykonać także kopię
repozytorium w serwisie GitHub, tzw. fork. Instrukcja, jak ro zrobić,
znajduje się `tutaj <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo>_`.

Praca z kodem
=============
``transactions2pln`` nie jest skomplikowanym programem - cały kod źródłowy
mieści się w katalogu ``src/transactions2pln``. Po wprowadzeniu pożądanych
zmian, program można uruchomić wykonując w katalogu ``src/`` polecenie
``python -m transactions2pln``.

To i inne używane podczas pracy z kodem polecenia widnieją w pliku
``Taskfile.yaml``. Służy on do wykonywania tych poleceń przez program Task_,
ale ma prostą strukturę i jeśli ktoś nie chce instalować bądź używać tego
programu, może traktować ten plik jako spis używanych komend i wykonywać je
samemu. Każda komenda w tym dokumencie zaczynająca się od ``task``
odpowiada jakiejś komendzie zdefiniowanej w ``Taskfile.yaml``.

Testy automatyczne
==================
Kod programu ``transactions2pln`` zawiera testy jednostkowe i funkcjonalne
w katalogu ``src/tests/``, których celem jest testowanie poprawności działania
wewnętrznych i zewnętrznych interfejsów programu. Testy te można wykonać
za pomocą komendy ``task test``.

Ponadto, kod zawiera też adnotacje wskazujące na używane typy danych,
zgodnie ze specyfikacjami PEP-483_, PEP-484_ i PEP-526_. Ich poprawność
można sprawdzić wykonując komendę ``task typecheck``.

Budowanie artefaktów
====================
Paczka wheel
------------
Specyfikacja "`binarny format dystrybucji`_" opisuje format paczek dla
bibliotek i programów w języku Python, których instalacja pozwala importować
je jako moduły. Taką paczkę zawierającą moduły i skrypt programu
``transactions2pln`` można utworzyć za pomocą komendy ``task build``.
Paczka zostanie utworzona w katalogu ``dist/``.

Plik wykonywalny
----------------
Główne polecenie programu ``transactions2pln`` można zbudować jako plik
wykonywalny systemu Windows, co umożliwia jego dystrybucję na urządzenia
z tym systemem bez konieczności instalowania języka Python
czy innych zależności. Służy do tego komenda ``task build_exe`` która
aby zadziałała poprawnie musi być wykonywana na systemie Windows.
Po jej wykonaniu, w katalogu ``build/`` znajdzie się katalog
wykonana, w nim zaś - plik wykonywalny ``transactions2pln`` i katalog z jego
zależnościami. Aby móc uruchamiać ten plik, musi on znajdować się obok
katalogu z zależnościami, a więc należy je dystrybuować razem.

Styl kodu
=========
Przyjęty styl kodu odpowiada temu opisanemu w PEP-8_, z następującymi
modyfikacjami:

- wcięcia są oznaczane za pomocą tabulatorów, nie spacji;
- długość linii powinna niezależnie od jej zawartości wynosić najwyżej
  79 znaków, chyba, że ostatnim wyrażeniem jest łańcuch o długości co najmniej
  40 znaków;
- relatywne importowanie jest całkowicie zakazane;
- łańcuchy są zapisywane pojedynczymi cudzysłowami, jeśli nie mają być
  zwrócone (wyświetlone) użytkownikowi; analogicznie, podwójne cudzysłowy
  oznaczają łańcuch, który jest zwracany (wyświetlany);
- komentarze są w języku polskim; komentarze w linii są oddzielone
  jedną spacją a nie dwiema;
- ``None`` jako domyślna zwracana wartość jest zawsze niejawna; zawsze używany
  jest zapis ``return`` zamiast ``return None``;
- adnotacje typów danych są zawsze wymagane, zarówno przy funkcjach
  jak i przy zmiennych.

Zgodność kodu z większością tych zasad można sprawdzić komendą
``task lint`` - wykonanie bez komunikatów o błędach oznacza, że styl kodu
odpowiada zdefiniowanym zasadom.

Dla plików nie zawierających kodu w języku Python obowiązuje jedynie zasada
dotycząca długości linii - wprowadzając w nich zmiany należy zasadniczo
trzymać się już istniejącego formatowania.

Proponowanie zmian w kodzie
===========================
Każda zmiana lub poprawka musi dotyczyć zgłoszonego błędu lub propozycji
nowej funkcji programu. Informacja, jak to zrobić, znajduje się w sekcji
`Zgłaszanie błędów <https://github.com/hbielenia/transactions2pln/blob/main/README.md>`_
w pliku ``README.rst``. Jeżeli już istnieje zgłoszenie i zostało ono
zaakceptowane, stosowne zmiany w kodzie źródłowym można proponować za pomocą
mechanizmu "`pull requests`_" (PR).

PR powinien być nazwany tak, by opisywał całość zgłoszonych zmian, gdyż
po jego zaakceptowaniu zostanie włączony do głównej gałęzi kodu jako
pojedynczy zestaw zmian (tzw. commit). Składając PR podlinkuj zgłoszenie,
którego dotyczy, pamiętaj też o dopisaniu siebie do listy autorów
w pliku ``pyproject.toml`` (jeżeli usuwasz czyjś kod - sprawdź, czy jego autor
nie powinien być usunięty z listy). Zgłaszając PR zgadzasz się na
opublikowanie swoich zmian na warunkach licencji opisanych w pliku
``LICENCE.txt``.

Przed zaakceptowaniem, PR musi przejść
wszystkie testy automatyczne.

.. _Docker: https://www.docker.com
.. _Git: https://git-scm.com
.. _Python: https://www.python.org
.. _Task: https://taskfile.dev
.. _GitHub: https://github.com
.. _wiersz poleceń: https://pl.wikipedia.org/wiki/Wiersz_polece%C5%84
.. _binarny format dystrybucji: https://packaging.python.org/en/latest/specifications/binary-distribution-format/
.. _PEP-483: https://peps.python.org/pep-0483/
.. _PEP-484: https://peps.python.org/pep-0484/
.. _PEP-526: https://peps.python.org/pep-0526/
.. _PEP-8: https://peps.python.org/pep-0008/
.. _pull requests: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request
