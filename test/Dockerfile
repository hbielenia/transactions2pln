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

FROM python:3.12-bullseye@sha256:4da4396d9fa63e3f2014b56275ed261eba14b9c6ba51883f81341ee170e64103
WORKDIR /usr/src/app
RUN apt-get update \
	&& apt-get install -y locales=2.31-13+deb11u11 \
	&& rm -rf /var/lib/apt/lists/* \
	&& localedef -i pl_PL -c -f UTF-8 -A /usr/share/locale/locale.alias pl_PL.UTF-8
ENV LANG pl_PL.utf8
