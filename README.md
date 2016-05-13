# Osiris-Stalker
Stalk osiris om nieuwe cijfers binnen te harken.

## Waarom Osiris-Stalker?
Osiris-Stalker biedt de mogelijkheid om cijfers op te halen van Osiris (cijfersysteem Hogeschool Leiden) en deze met de vorige keer te vergelijken.

## Changelog

Versie 1.0:

* Complete rewrite van Osiris-Stalker.
* Argparse geïntergreerd.
* Mogelijkheid om vanuit een config file te lezen.

## Cronjob

Dit is waar het uiteindelijk onder moet gaan draaien (om het geautomatiseerd te gaan laten lopen).

1. Maak een cronjob aan onder Linux: ``crontab -e``.
2. Voeg deze regel toe:
    ``*/10 * * * * python /<PATH TO DIRECTORY OF OSIRIS STALKER>/osiris_stalker.py [params]``

Tip: Niet vaker dan 3x per 10 minuten.

## TODO

* Email support :) -> Jeah. Dropped, ugly PHP script.
* Whatsapp support? :)
* PHP (Laravel) versie, geschreven door Mathijs (@duckson).