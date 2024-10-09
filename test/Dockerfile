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

FROM python:3.11-bullseye@sha256:c927121ba6f075a139438db25b22e0c21df8ecae790958f5f3764c32e3c25834
WORKDIR /usr/src/app
RUN apt-get update \
	&& apt-get install -y locales==2.31-13+deb11u10 \
	&& rm -rf /var/lib/apt/lists/* \
	&& localedef -i pl_PL -c -f UTF-8 -A /usr/share/locale/locale.alias pl_PL.UTF-8
ENV LANG pl_PL.utf8
