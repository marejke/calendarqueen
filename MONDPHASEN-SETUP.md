# Calendar Queen: automatische Mondphasen

## Was hinzugefügt wurde

- `.github/scripts/generate_moon_phases.py`: ruft die primären Mondphasen von der USNO-API ab und erzeugt `feeds/mondphasen.ics`.
- `.github/scripts/test_generate_moon_phases.py`: prüft grundlegende Kalender- und Datumsfunktionen ohne Internetzugriff.
- `.github/workflows/jekyll-gh-pages.yml`: testet und erzeugt den Feed vor dem GitHub-Pages-Build; zusätzlich läuft der Workflow monatlich.

## Verhalten

- Datenquelle: U.S. Naval Observatory, https://aa.usno.navy.mil/data/api
- Enthalten: Neumond, erstes Viertel, Vollmond und letztes Viertel.
- Zeitraum: ab dem aktuellen Datum bis 24 Monate in die Zukunft.
- Aktualisierung: automatisch am 1. eines Monats um 05:17 UTC; zusätzlich bei Pushes nach `main` und manuell über GitHub Actions.
- Veröffentlichte URL: `https://calendarqueen.de/feeds/mondphasen.ics` (vorausgesetzt, die Domain zeigt auf das veröffentlichte GitHub-Pages-Projekt).
- Die Datei wird beim Build erzeugt und nicht in Git committet. Wenn Abruf oder Validierung fehlschlagen, schlägt der Build fehl und die bisher veröffentlichte Website bleibt bestehen.
- Ereignisse nutzen UTC-Zeitstempel. Kalender-Apps zeigen den Zeitpunkt normalerweise in der lokalen Zeitzone der Nutzer:innen an.

## Vor dem Produktivbetrieb

Die API-Dokumentation wurde geprüft; die Nutzungsbedingungen und eine eventuell gewünschte Quellen-/Attributionsformulierung sollten vor dem kommerziellen Produktivbetrieb noch bestätigt werden. Der Feed ist zunächst ein technischer Prototyp. Nach dem Merge: GitHub → Actions öffnen, den Workflow manuell starten und prüfen, dass der Build erfolgreich ist und die `.ics`-URL erreichbar ist.
