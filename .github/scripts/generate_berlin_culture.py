#!/usr/bin/env python3
"""Merge authorized Berlin Bühnen and Museumsportal iCalendar exports.

The source URLs must be provided as GitHub Actions secrets after the source
owners have granted permission and supplied compatible ICS export URLs.
No scraping of public website pages is performed.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OUTPUT = Path("feeds/berlin-buehnen-museen.ics")
SOURCES = (
    ("BERLIN_BUEHNEN_ICS_URL", "Berlin Bühnen", "berlin-buehnen"),
    ("MUSEUMSPORTAL_ICS_URL", "Museumsportal Berlin", "museumsportal"),
)
USER_AGENT = "CalendarQueen/1.0 (+https://calendarqueen.de/)"


def unfold_lines(ics_text: str) -> list[str]:
    """Unfold RFC 5545 continuation lines into logical content lines."""
    physical = ics_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    logical: list[str] = []
    for line in physical:
        if not line:
            continue
        if line.startswith((" ", "\t")) and logical:
            logical[-1] += line[1:]
        else:
            logical.append(line)
    return logical


def extract_components(lines: list[str], component_name: str) -> list[list[str]]:
    """Extract complete VEVENT or VTIMEZONE blocks, including nested blocks."""
    wanted = component_name.upper()
    blocks: list[list[str]] = []
    current: list[str] | None = None
    depth = 0
    for line in lines:
        upper = line.upper()
        if upper.startswith("BEGIN:"):
            name = upper[6:].strip()
            if current is None and name == wanted:
                current = [line]
                depth = 1
            elif current is not None:
                current.append(line)
                depth += 1
        elif upper.startswith("END:") and current is not None:
            current.append(line)
            depth -= 1
            if depth == 0:
                blocks.append(current)
                current = None
        elif current is not None:
            current.append(line)
    if current is not None:
        raise ValueError(f"Unclosed {component_name} component in source calendar")
    return blocks


def property_value(block: list[str], property_name: str) -> str:
    """Return the value of a simple ICS property, ignoring parameters."""
    wanted = property_name.upper()
    for line in block:
        if ":" not in line:
            continue
        head, value = line.split(":", 1)
        if head.split(";", 1)[0].upper() == wanted:
            return value
    return ""


def property_line_index(block: list[str], property_name: str) -> int | None:
    wanted = property_name.upper()
    for index, line in enumerate(block):
        if ":" in line and line.split(":", 1)[0].split(";", 1)[0].upper() == wanted:
            return index
    return None


def event_start_date(event: list[str]) -> date | None:
    value = property_value(event, "DTSTART")
    match = re.match(r"(\d{4})(\d{2})(\d{2})", value)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def unescape_ics(value: str) -> str:
    return (value.replace(r"\n", " ").replace(r"\N", " ")
            .replace(r"\,", ",").replace(r"\;", ";").replace(r"\\", "\\"))


def normalized(value: str) -> str:
    return " ".join(unescape_ics(value).casefold().split())


def event_dedupe_key(event: list[str]) -> tuple[str, str, str]:
    start_value = property_value(event, "DTSTART")
    start_match = re.match(r"\d{8}(?:T\d{6}Z?)?", start_value)
    return (
        normalized(property_value(event, "SUMMARY")),
        start_match.group(0) if start_match else start_value,
        normalized(property_value(event, "LOCATION")),
    )


def namespace_uid(event: list[str], source_id: str) -> list[str]:
    uid_index = property_line_index(event, "UID")
    old_uid = property_value(event, "UID")
    identity = old_uid or "|".join(event_dedupe_key(event))
    digest = hashlib.sha256((source_id + "|" + identity).encode("utf-8")).hexdigest()[:24]
    new_uid = f"UID:cq-{source_id}-{digest}@calendarqueen.de"
    result = list(event)
    if uid_index is None:
        result.insert(1, new_uid)
    else:
        result[uid_index] = new_uid
    # A clear provenance marker helps future troubleshooting without copying imagery.
    result.insert(1, f"X-CALENDAR-QUEEN-SOURCE:{source_id}")
    return result


def parse_source_calendar(ics_text: str, source_id: str) -> tuple[list[list[str]], list[list[str]]]:
    lines = unfold_lines(ics_text)
    if not any(line.upper() == "BEGIN:VCALENDAR" for line in lines) or not any(
        line.upper() == "END:VCALENDAR" for line in lines
    ):
        raise ValueError("Source response is not a complete VCALENDAR file")
    timezones = extract_components(lines, "VTIMEZONE")
    events = extract_components(lines, "VEVENT")
    today = datetime.now(timezone.utc).date()
    future_events: list[list[str]] = []
    for event in events:
        start_date = event_start_date(event)
        if start_date is None:
            # Skip malformed events rather than publish misleading calendar items.
            continue
        if start_date < today:
            continue
        if not property_value(event, "SUMMARY"):
            continue
        future_events.append(namespace_uid(event, source_id))
    return timezones, future_events


def fetch_ics(url: str, source_name: str) -> str:
    if not url.startswith("https://"):
        raise RuntimeError(f"{source_name}: source URL must use HTTPS")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/calendar, text/plain, */*"})
    try:
        with urlopen(request, timeout=35) as response:
            raw = response.read(12_000_000 + 1)
    except HTTPError as exc:
        raise RuntimeError(f"{source_name}: source returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, OSError):
        # Avoid logging the URL because partner links may contain access tokens.
        raise RuntimeError(f"{source_name}: could not retrieve the source calendar") from None
    if len(raw) > 12_000_000:
        raise RuntimeError(f"{source_name}: source calendar is unexpectedly large")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise RuntimeError(f"{source_name}: source calendar is not UTF-8 text") from None


def fold_line(line: str, limit: int = 73) -> str:
    """Fold a logical ICS line at UTF-8 byte boundaries (RFC 5545)."""
    chunks: list[str] = []
    current = ""
    current_bytes = 0
    for char in line:
        size = len(char.encode("utf-8"))
        if current and current_bytes + size > limit:
            chunks.append(current)
            current = " " + char
            current_bytes = 1 + size
        else:
            current += char
            current_bytes += size
    chunks.append(current)
    return "\r\n".join(chunks)


def timezone_id(block: list[str]) -> str:
    return property_value(block, "TZID")


def build_merged_calendar(source_urls: dict[str, str], today: date | None = None) -> str:
    del today  # The real clock is used for the default upcoming-event filter.
    merged_timezones: list[list[str]] = []
    seen_timezones: set[str] = set()
    merged_events: list[list[str]] = []
    seen_event_keys: set[tuple[str, str, str]] = set()

    for env_name, source_name, source_id in SOURCES:
        url = source_urls[env_name]
        source_text = fetch_ics(url, source_name)
        timezones, events = parse_source_calendar(source_text, source_id)
        for zone in timezones:
            zone_id = timezone_id(zone)
            zone_key = zone_id or "\n".join(zone)
            if zone_key not in seen_timezones:
                merged_timezones.append(zone)
                seen_timezones.add(zone_key)
        for event in events:
            key = event_dedupe_key(event)
            if key in seen_event_keys:
                continue
            seen_event_keys.add(key)
            merged_events.append(event)

    if not merged_events:
        raise RuntimeError("Both source calendars were retrieved, but no valid upcoming events were found")

    merged_events.sort(key=lambda e: (event_start_date(e) or date.max, normalized(property_value(e, "SUMMARY"))))
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Calendar Queen//Berlin Buehnen und Museen//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Berlin: Bühnen & Museen | Calendar Queen",
        "X-WR-CALDESC:Berliner Bühnenveranstaltungen und Museumstermine. Änderungen werden regelmäßig übernommen.",
        f"X-WR-LAST-REFRESH:{now}",
    ]
    for zone in merged_timezones:
        output_lines.extend(zone)
    for event in merged_events:
        # Ensure each event has an updated timestamp for this published snapshot.
        dtstamp_index = property_line_index(event, "DTSTAMP")
        stamped_event = list(event)
        if dtstamp_index is None:
            stamped_event.insert(1, f"DTSTAMP:{now}")
        else:
            stamped_event[dtstamp_index] = f"DTSTAMP:{now}"
        output_lines.extend(stamped_event)
    output_lines.append("END:VCALENDAR")
    return "\r\n".join(fold_line(line) for line in output_lines) + "\r\n"


def main() -> int:
    configured = {env_name: os.environ.get(env_name, "").strip() for env_name, _, _ in SOURCES}
    if not all(configured.values()):
        missing = [env_name for env_name, value in configured.items() if not value]
        print(
            "Berlin culture feed skipped: approved ICS source URLs are not configured yet "
            f"({', '.join(missing)}). No placeholder calendar will be published."
        )
        return 0

    content = build_merged_calendar(configured)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=OUTPUT.parent, delete=False) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    os.replace(temp_path, OUTPUT)
    print(f"Wrote {OUTPUT} with {content.count('BEGIN:VEVENT')} upcoming events from the two approved sources.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
