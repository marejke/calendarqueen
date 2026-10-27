#!/usr/bin/env python3
"""Generate Calendar Queen's rolling 24-month moon-phase ICS feed from USNO data.

The USNO API returns primary phase times in UT1 to minute precision. ICS event
instants are serialized in UTC (the UT1/UTC difference is below one second).
No third-party Python packages are required.
"""

from __future__ import annotations

import calendar
import json
import os
import sys
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://aa.usno.navy.mil/api/moon/phases/year?year={year}"
SOURCE_URL = "https://aa.usno.navy.mil/data/api"
OUTPUT = Path("feeds/mondphasen.ics")
HORIZON_MONTHS = 24
MIN_EXPECTED_EVENTS = 70
PHASE_NAMES = {
    "New Moon": "Neumond",
    "First Quarter": "Erstes Viertel",
    "Full Moon": "Vollmond",
    "Last Quarter": "Letztes Viertel",
}


def add_months(day: date, months: int) -> date:
    month_index = day.year * 12 + (day.month - 1) + months
    year, month_zero_based = divmod(month_index, 12)
    month = month_zero_based + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def fetch_year(year: int) -> list[dict]:
    url = API_URL.format(year=year)
    request = Request(url, headers={"User-Agent": "CalendarQueen-MoonPhaseFeed/1.0"})
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload.get("error"):
                raise RuntimeError(f"USNO API returned an error for {year}: {payload['error']}")
            phases = payload.get("phasedata")
            if not isinstance(phases, list) or not phases:
                raise RuntimeError(f"USNO API returned no phase data for {year}")
            return phases
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Could not fetch moon phases for {year}: {last_error}")


def escape_ics(value: str) -> str:
    return (value.replace("\\", "\\\\").replace(";", r"\;")
            .replace(",", r"\,").replace("\r\n", r"\n")
            .replace("\n", r"\n").replace("\r", r"\n"))


def fold_ics_line(line: str) -> str:
    """Fold long lines at 75 UTF-8 octets as required by RFC 5545."""
    chunks: list[str] = []
    current = ""
    current_bytes = 0
    for char in line:
        char_bytes = len(char.encode("utf-8"))
        if current_bytes + char_bytes > 73 and current:
            chunks.append(current)
            current = " " + char
            current_bytes = 1 + char_bytes
        else:
            current += char
            current_bytes += char_bytes
    chunks.append(current)
    return "\r\n".join(chunks)


def build_calendar(phases: list[dict], start_date: date, end_date: date) -> str:
    events: list[tuple[datetime, str, str]] = []
    seen: set[str] = set()
    for phase in phases:
        phase_name = phase.get("phase")
        if phase_name not in PHASE_NAMES:
            continue
        try:
            moment = datetime(
                int(phase["year"]), int(phase["month"]), int(phase["day"]),
                int(str(phase["time"]).split(":")[0]),
                int(str(phase["time"]).split(":")[1]), tzinfo=timezone.utc,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Invalid phase record from USNO: {phase!r}") from exc
        if not (start_date <= moment.date() <= end_date):
            continue
        uid = moment.strftime("moonphase-%Y%m%dT%H%M00Z@calendarqueen.de")
        if uid in seen:
            continue
        seen.add(uid)
        events.append((moment, PHASE_NAMES[phase_name], uid))

    events.sort(key=lambda item: item[0])
    if len(events) < MIN_EXPECTED_EVENTS:
        raise RuntimeError(
            f"Only {len(events)} moon phases found for the requested period; "
            "refusing to publish a possibly incomplete calendar."
        )

    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Calendar Queen//Mondphasen//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Mondphasen | Calendar Queen",
        "X-WR-CALDESC:Neu- und Vollmond sowie die beiden Viertelphasen. Datenquelle: U.S. Naval Observatory.",
    ]
    for moment, phase_de, uid in events:
        stamp = moment.strftime("%Y%m%dT%H%M00Z")
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now}",
            f"DTSTART:{stamp}",
            f"SUMMARY:{escape_ics(phase_de)}",
            f"DESCRIPTION:{escape_ics('Astronomischer Zeitpunkt laut U.S. Naval Observatory. Quelle: ' + SOURCE_URL)}",
            f"URL:{SOURCE_URL}",
            "CATEGORIES:Mondphasen",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold_ics_line(line) for line in lines) + "\r\n"


def main() -> int:
    today = datetime.now(timezone.utc).date()
    end_date = add_months(today, HORIZON_MONTHS)
    years = range(today.year, end_date.year + 1)
    all_phases: list[dict] = []
    for year in years:
        print(f"Fetching USNO moon phases for {year}...")
        all_phases.extend(fetch_year(year))

    content = build_calendar(all_phases, today, end_date)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Replace atomically only after the source data and calendar passed validation.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=OUTPUT.parent, delete=False) as handle:
        handle.write(content)
        temporary_path = Path(handle.name)
    os.replace(temporary_path, OUTPUT)
    event_count = content.count("BEGIN:VEVENT")
    print(f"Wrote {OUTPUT} with {event_count} events ({today} through {end_date}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
