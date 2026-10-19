# Koe – Todo

Eine persönliche, ADHS-freundliche Todo-App für Android, bei der Todos vor allem per Sprache angelegt werden sollen.

## Warum

Todos festzuhalten scheitert oft am Moment selbst: Der Gedanke ist da, aber App öffnen, tippen und einsortieren sind dann doch zu viele Schritte
Koe reduziert das auf einen Handgriff: Button gedrückt halten, reden, loslassen. Den Rest übernimmt die App. Sie zerlegt das Gesagte in einzelne Todos, sortiert sie in Ordner ein und erkennt Deadlines und Wiederholungen.
Bei der App spielen die Widgets eine besondere Rolle. Todos einsehen zu können, soll der Schritt, in die App zu gehen gemieden werden, in dem die Todos direkt auf dem Homescreen angezeigt werdne können.
Geplant ist auch ein Widget für das anlegen der Todos via Sprachaufnahme.

Koe ist außerdem ein eigenständiges Lernprojekt, um native Android-Entwicklung mit Kotlin und Jetpack Compose zu lernen.

## Funktionen (v1)

- **Todos per Sprache anlegen:** gedrückt halten zum Aufnehmen, hochschieben zum Fixieren, loslassen zum Absenden. Ein Sprachmodell macht aus dem Gesagten strukturierte Todos.
- **Manuell anlegen und bearbeiten** über ein Formular
- **Ordner** mit eigener Farbe, z. B. Allgemein, Wunschliste, IT-Ideen, Einkaufsliste
- **Wiederkehrende Todos** (täglich, wöchentlich, monatlich), die sich automatisch wieder öffnen und angezeigt werden
- **Einmalige Todos**, optional mit Deadline
- **Wichtige Todos** werden farbig hervorgehoben
- **Dringend-Bereich** für wichtige Todos, deren Deadline bald fällig oder schon überschritten ist
- **Home-Screen-Widgets:** Todo-Liste zum Abhaken und ein Aufnahme-Button
- **Light und Dark Mode**

## Geplant

- Feste Termine direkt in den Kalender eintragen
- Aufnahme über die Seitentaste des Handys (Eventuell nicht nötig durch Aufnahme Widget)
- Unteraufgaben, Bearbeiten per Sprache (unklar ob notwendig), weitere Wiederholungsmuster (z. B. bestimmte Wochentage)
- anlegen von Ordnern auch via Sprache sowie das zu ordnen der Todos in Ordner via Sprache

## Tech-Stack

- **Android:** Kotlin, Jetpack Compose, Jetpack Glance (Widgets)
- **Backend:** FastAPI (Python), PostgreSQL, Docker Compose auf einem Raspberry Pi 5
- **Sprache zu Todos:** Android SpeechRecognizer + Claude API

## Projektstruktur

```
backend/   FastAPI-Server, Datenbank, Docker-Setup
android/   Android-App und Widgets
```

## Setup

Folgt, sobald das Grundgerüst steht.

## Status

In Entwicklung. Persönliches Projekt, eine Veröffentlichung als Open Source ist angedacht.
