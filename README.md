# Koe – Todo

"Koe" ist japanisch und bedeutet ünersetzt "Stimme"

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

### Backend starten

```
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

(`backend/.env` muss existieren, siehe Kommentare darin für die nötigen Werte.)

`--host 0.0.0.0` ist wichtig, sonst ist der Server nur vom PC selbst erreichbar, nicht vom
Handy im WLAN. Falls Windows beim ersten Start eine Firewall-Eingabeaufforderung zeigt
(oder nicht erreichbar bleibt), muss eingehender Traffic auf Port 8000 erlaubt werden
(Windows-Firewall -> Eingehende Regeln -> für Python/uvicorn bzw. den Port freigeben).

Erreichbarkeit prüfen: `curl http://<LAN-IP-des-Rechners>:8000/health` sollte
`{"status":"ok"}` liefern - einmal vom Rechner selbst, einmal vom Handy-Browser aus.

### Android-App bauen und installieren

1. `android/local.properties.example` nach `android/local.properties` kopieren und ausfüllen:
   - `sdk.dir`: Pfad zum Android SDK
   - `koe.baseUrl`: `http://<LAN-IP-des-Rechners>:8000/` (Emulator: `http://10.0.2.2:8000/`)
   - `koe.apiToken`: muss zu `API_TOKEN` in `backend/.env` passen
2. Falls sich die LAN-IP ändert, auch
   `android/app/src/main/res/xml/network_security_config.xml` anpassen - dort ist
   Klartext-HTTP nur für die dort eingetragenen Adressen erlaubt.
3. Gerät per USB oder drahtlosem Debugging verbinden (`adb devices` muss es zeigen; bei
   WLAN-Debugging ggf. `adb mdns services` zur Fehlersuche, falls die Verbindung abreißt).
4. Bauen und installieren:
   ```
   cd android
   ./gradlew :app:assembleDebug
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```
   Oder einfach über Android Studio "Run" auf das verbundene Gerät.

Handy und Rechner müssen im selben WLAN sein (Thin Client - die App lädt bei jeder
Aktion frisch vom Backend, es gibt keinen Offline-Modus).

### Tests

```
cd android
./gradlew :app:testDebugUnitTest
```

## Status

In Entwicklung. Persönliches Projekt, eine Veröffentlichung als Open Source ist angedacht.

Umgesetzt: Ordner/Todos anzeigen (Hauptscreen mit Swipe, Dringend/Wiederkehrend/Einmalig),
Abhaken mit Rückgängig-Snackbar, Bearbeiten/Löschen-Formular, Ordnerverwaltung,
Sprachaufnahme über den Hinzufügen-Button (SpeechRecognizer de-DE -> `/voice-todos`).
Nicht umgesetzt: Home-Screen-Widgets (Slice 3), Kalender-Anbindung, `/settings`
(Backend liefert dafür bewusst `501`).
