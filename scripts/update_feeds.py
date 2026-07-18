#!/usr/bin/env python3
"""
Calendar Queen – Täglicher Feed-Update-Agent
Läuft via GitHub Actions jeden Morgen um 7 Uhr.
Nutzt die Anthropic API um ICS-Feeds zu prüfen und zu aktualisieren.
"""

import os
import sys
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
import anthropic

# ── Konfiguration ──────────────────────────────────────────────────────────
FEEDS_DIR    = Path(__file__).parent.parent / "feeds"
TODAY        = date.today()
HORIZON_DAYS = 90          # Events der nächsten 90 Tage prüfen

FEED_CONFIGS = {
    "mondphasen.ics": {
        "name": "Mondphasen 2026",
        "description": "Mondphasen mit astronomisch korrekten Daten und Ritual-Impulsen",
        "type": "astronomical",
        "check_duplicates": True,
        "instructions": """
Prüfe die Mondphasen-Einträge auf astronomische Korrektheit.
Ergänze fehlende Mondphasen für die nächsten 90 Tage.
Mondphasen 2026 (UTC+2): 
- Aug: Vollmond 09.08, Neumond 23.08
- Sep: Vollmond 07.09, Neumond 21.09
- Okt: Vollmond 07.10, Neumond 21.10 (Sonnenfinsternis! – als EXTRA-Event)
- Nov: Vollmond 05.11, Neumond 20.11
- Dez: Vollmond 04.12, Neumond 20.12
Stil: Kurz, introspektiv, eine FRAGE DICH-Zeile am Ende.
"""
    },
    "berlin-events.ics": {
        "name": "Berlin Events",
        "description": "Flohmärkte und Berliner Veranstaltungen",
        "type": "events",
        "check_duplicates": True,
        "instructions": """
Prüfe den Berlin-Events-Feed. 
Flohmärkte (wöchentlich, verlässliche Termine):
- Mauerpark: jeden Sonntag 9-18 Uhr
- Boxhagener Platz: Sa+So 9-18 Uhr  
- RAW-Gelände Friedrichshain: Sa+So 9-18 Uhr
- Straße des 17. Juni: Sa+So 10-17 Uhr
- Arkonaplatz: jeden Sonntag 10-17 Uhr (! fehlt evtl)
Füge fehlende Sonntage für die nächsten 8 Wochen hinzu.
Entferne vergangene Events (vor heute).
"""
    },
    "krauter-berlin.ics": {
        "name": "Kräuter & Wildpflanzen Berlin",
        "description": "Saisonaler Foraging-Kalender",
        "type": "seasonal",
        "check_duplicates": False,
        "instructions": """
Prüfe ob die Saison-Fenster für die aktuelle Jahreszeit korrekt sind.
Ergänze saisonale Events für Herbst wenn wir uns September nähern:
- Sep-Nov: Pilzsaison Hauptsaison (Steinpilz, Marone, Pfifferling)
- Sep-Okt: Apfelernte, Schlehen, Sanddorn
- Okt-Nov: Hagebutten Hauptsaison, Weißdorn
Standorte immer mit angeben (Grunewald, Tempelhof, etc.)
"""
    },
    "astronomie.ics": {
        "name": "Astronomie & Himmel",
        "description": "Meteorschauer, Supermonde, Planetenkonstellationen",
        "type": "astronomical",
        "check_duplicates": True,
        "instructions": """
Ergänze fehlende Astronomie-Events für die nächsten 90 Tage:
- Oktoberdrachen/Draconiden: ca. 8. Oktober
- Orioniden Meteorschauer: Maximum 21.-22. Oktober
- Tauriden: November
- Leoniden: 17.-18. November
- Geminiden: 13.-14. Dezember (stärkster Schauer des Jahres!)
Astronomische Daten sind verlässlich – bitte exakte Daten angeben.
"""
    },
    "saisonkalender.ics": {
        "name": "Saisonkalender",
        "description": "Was hat gerade Saison",
        "type": "seasonal",
        "check_duplicates": False,
        "instructions": """
Prüfe ob die aktuellen Saison-Einträge zeitlich korrekt sind.
Ergänze Herbst-Saison-Events wenn relevant:
- Sep-Okt: Kürbissorten Hauptsaison, Äpfel, Birnen, Quitten
- Okt-Nov: Rosenkohl, Grünkohl (nach erstem Frost)
- Nov: Steckrüben, Feldsalat
Fokus: Was kauft man jetzt sinnvoll auf dem Wochenmarkt?
"""
    },
    "sale-kalender.ics": {
        "name": "Sale-Kalender",
        "description": "Sales und Shopping-Events",
        "type": "events",
        "check_duplicates": True,
        "instructions": """
Prüfe ob alle bekannten Sale-Termine für die nächsten 90 Tage drin sind.
Bekannte Termine:
- Amazon Prime Day: typisch Mitte Juli (wenn nicht schon vorbei)
- Back-to-School Sales: August
- Singles Day / 11.11.: 11. November
- Black Friday: 27. November 2026
- Cyber Monday: 30. November 2026
- Weihnachts-Sales: ab Dezember
Vergangene Events entfernen.
"""
    },
    "schulferien.ics": {
        "name": "Schulferien Berlin",
        "description": "Schulferien und Feiertage",
        "type": "official",
        "check_duplicates": False,
        "instructions": """
Prüfe die Schulferien-Einträge auf Vollständigkeit.
Berliner Schulferien 2026/2027 (offiziell laut berlin.de):
- Sommerferien 2026: 18. Juni – 31. Juli 2026
- Herbstferien 2026: 19. Oktober – 30. Oktober 2026
- Weihnachtsferien 2026/27: 21. Dezember 2026 – 2. Januar 2027
Feiertage Berlin 2026 die noch fehlen könnten:
- Tag der Deutschen Einheit: 3. Oktober
- Allerheiligen: KEIN Feiertag in Berlin
- Weihnachten: 25./26. Dezember
"""
    },
    "steuerfristen.ics": {
        "name": "Steuerfristen",
        "description": "Steuer- und Behördenfristen",
        "type": "official",
        "check_duplicates": False,
        "instructions": """
Prüfe ob alle relevanten Steuerfristen für die nächsten 90 Tage drin sind.
Wichtige Termine:
- 10. jedes Monats: USt-Voranmeldung Vormonat (monatliche Zahler)
- Q3 Gewerbesteuer: 15. September
- Q3 Körperschaftsteuer: 10. September  
- Q3 Einkommensteuer-Vorauszahlung: 10. September
- Lohnsteuer: 10. jedes Monats
Keine erfundenen Fristen – nur gesetzlich geregelte Termine.
"""
    },
    "kuendigungsfristen.ics": {
        "name": "Kündigungsfristen",
        "description": "Wechsel- und Kündigungsfristen",
        "type": "advisory",
        "check_duplicates": False,
        "instructions": """
Prüfe ob für die nächsten 90 Tage relevante Kündigugshinweise fehlen.
KFZ-Versicherung: Hauptfälligkeit 1. Januar – Kündigung bis 30. November.
Strom/Gas: Oft Jahreswechsel – Hinweis im Oktober/November.
Zeitschriften-Abos: Typisch zum Jahresende.
Gym-Verträge: Oft 3 oder 6 Monate Kündigungsfrist.
Formuliere als Erinnerung und Handlungsaufforderung.
"""
    },
    "babyjahr.ics": {
        "name": "Erstes Babyjahr",
        "description": "Wachstumsschübe und Meilensteine",
        "type": "advisory",
        "check_duplicates": False,
        "instructions": """
Der Babyjahr-Feed zeigt Demo-Einträge für ein Baby geb. 01.05.2026.
Prüfe ob die Events chronologisch korrekt sind und aktuell bleiben.
Wachstumsschübe nach Wonder Weeks: Woche 5, 8, 12, 19, 26, 37, 46, 55.
Für Demo-Baby (geb. 01.05.2026) entspricht das:
- Schub 1: ~5. Juni 2026
- Schub 2: ~26. Juni 2026  
- Schub 3: ~20. Juli 2026
- Schub 4: ~10. September 2026
- Schub 5: ~27. Oktober 2026
Ergänze fehlende Schübe wenn sie in den nächsten 90 Tagen liegen.
"""
    },
}


def read_ics(path: Path) -> str:
    """Liest eine ICS-Datei als Text."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Fehler beim Lesen von {path.name}: {e}")
        return ""


def validate_ics_basic(content: str) -> bool:
    """Prüft ob das ICS valide aussieht."""
    return (
        "BEGIN:VCALENDAR" in content
        and "END:VCALENDAR" in content
        and "BEGIN:VEVENT" in content
    )


def count_future_events(content: str) -> int:
    """Zählt Events in der Zukunft."""
    count = 0
    today_str = TODAY.strftime("%Y%m%d")
    for m in re.finditer(r"DTSTART[^:]*:(\d{8})", content):
        if m.group(1) >= today_str:
            count += 1
    return count


def update_feed_with_claude(client: anthropic.Anthropic, feed_file: str, config: dict) -> str | None:
    """Lässt Claude einen einzelnen Feed prüfen und aktualisieren."""
    path = FEEDS_DIR / feed_file
    current_content = read_ics(path)

    if not current_content:
        print(f"  Überspringe {feed_file} – Datei nicht lesbar")
        return None

    future_events = count_future_events(current_content)
    print(f"  {feed_file}: {future_events} zukünftige Events gefunden")

    today_formatted = TODAY.strftime("%d. %B %Y")
    horizon = (TODAY + timedelta(days=HORIZON_DAYS)).strftime("%d. %B %Y")

    prompt = f"""Du bist der Feed-Update-Agent von Calendar Queen (calendarqueen.de).
Heute ist der {today_formatted}. Prüfe den Kalender-Feed für die nächsten 90 Tage (bis {horizon}).

FEED: {config['name']}
BESCHREIBUNG: {config['description']}

AUFGABE:
{config['instructions']}

REGELN:
1. Vergangene Events (DTSTART vor heute {TODAY.strftime('%Y%m%d')}) ENTFERNEN
2. Fehlende Events für die nächsten 90 Tage ERGÄNZEN
3. Doppelte Events (gleicher Tag, gleicher Inhalt) ENTFERNEN
4. UIDs müssen eindeutig bleiben (Schema: cq-<feed>-<datum>@calendarqueen.de)
5. Nur VERLÄSSLICHE, verifiable Informationen – keine Erfindungen
6. DTSTART immer als DATE (nicht DATETIME) für ganztägige Events
7. PRODID, X-WR-CALNAME etc. unverändert lassen
8. Stil: Deutsche Sprache, informativ, kurz

AKTUELLER FEED-INHALT:
{current_content}

Antworte NUR mit dem vollständigen aktualisierten ICS-Inhalt, beginnend mit BEGIN:VCALENDAR.
Kein erklärender Text davor oder danach."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text.strip()

        # Extrahiere nur den ICS-Teil falls nötig
        if "BEGIN:VCALENDAR" in response:
            start = response.index("BEGIN:VCALENDAR")
            end   = response.rindex("END:VCALENDAR") + len("END:VCALENDAR")
            response = response[start:end]

        # Validierung
        if not validate_ics_basic(response):
            print(f"  WARNUNG: Ungültiges ICS für {feed_file} – überspringe")
            return None

        new_future = count_future_events(response)
        print(f"  → Aktualisiert: {new_future} zukünftige Events")
        return response

    except Exception as e:
        print(f"  FEHLER beim Update von {feed_file}: {e}")
        return None


def main():
    target_feed = os.environ.get("TARGET_FEED", "").strip()
    api_key     = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key:
        print("FEHLER: ANTHROPIC_API_KEY nicht gesetzt!")
        sys.exit(1)

    if not FEEDS_DIR.exists():
        print(f"FEHLER: feeds/-Verzeichnis nicht gefunden: {FEEDS_DIR}")
        sys.exit(1)

    client    = anthropic.Anthropic(api_key=api_key)
    updated   = 0
    unchanged = 0
    errors    = 0

    print(f"\n{'='*60}")
    print(f"Calendar Queen Feed-Update-Agent")
    print(f"Datum: {TODAY.strftime('%d.%m.%Y')}")
    print(f"Repo:  https://github.com/marejke/calendarqueen")
    print(f"{'='*60}\n")

    feeds_to_process = {}
    if target_feed:
        key = target_feed if target_feed.endswith(".ics") else f"{target_feed}.ics"
        if key in FEED_CONFIGS:
            feeds_to_process = {key: FEED_CONFIGS[key]}
        else:
            print(f"Unbekannter Feed: {target_feed}")
            sys.exit(1)
    else:
        feeds_to_process = FEED_CONFIGS

    for feed_file, config in feeds_to_process.items():
        print(f"\n── {config['name']} ({feed_file})")
        path = FEEDS_DIR / feed_file

        if not path.exists():
            print(f"  Datei existiert nicht – überspringe")
            errors += 1
            continue

        original = read_ics(path)
        updated_content = update_feed_with_claude(client, feed_file, config)

        if updated_content is None:
            errors += 1
            continue

        if updated_content.strip() == original.strip():
            print("  Keine Änderungen nötig")
            unchanged += 1
        else:
            path.write_text(updated_content, encoding="utf-8")
            print(f"  ✓ Gespeichert: {feed_file}")
            updated += 1

    print(f"\n{'='*60}")
    print(f"Ergebnis: {updated} aktualisiert, {unchanged} unverändert, {errors} Fehler")
    print(f"{'='*60}\n")

    if errors > 0 and updated == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
