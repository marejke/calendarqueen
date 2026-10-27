import unittest
from datetime import date

from generate_berlin_culture import (
    event_dedupe_key,
    parse_source_calendar,
    property_value,
    unfold_lines,
)


SAMPLE = """BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Fixture//EN\r\nBEGIN:VTIMEZONE\r\nTZID:Europe/Berlin\r\nEND:VTIMEZONE\r\nBEGIN:VEVENT\r\nUID:example-1\r\nDTSTAMP:20260101T120000Z\r\nDTSTART;TZID=Europe/Berlin:29990102T193000\r\nSUMMARY:Eine schöne Vorstellung\r\nLOCATION:Testtheater, Berlin\r\nURL:https://example.org/event\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nUID:old-event\r\nDTSTAMP:20200101T120000Z\r\nDTSTART:19990102T193000Z\r\nSUMMARY:Vergangene Vorstellung\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"""


class BerlinCultureTests(unittest.TestCase):
    def test_unfolds_continuation_lines(self):
        self.assertEqual(unfold_lines("SUMMARY:Eine \r\n schöne Vorstellung\r\n"), ["SUMMARY:Eine schöne Vorstellung"])

    def test_keeps_future_events_and_timezone(self):
        zones, events = parse_source_calendar(SAMPLE, "berlin-buehnen")
        self.assertEqual(len(zones), 1)
        self.assertEqual(len(events), 1)
        self.assertTrue(any(line.startswith("UID:cq-berlin-buehnen-") for line in events[0]))
        self.assertEqual(property_value(events[0], "SUMMARY"), "Eine schöne Vorstellung")
        self.assertEqual(property_value(events[0], "X-CALENDAR-QUEEN-SOURCE"), "berlin-buehnen")

    def test_dedupe_key_includes_start_and_place(self):
        event_a = ["BEGIN:VEVENT", "DTSTART:29990102T193000Z", "SUMMARY:Stage show", "LOCATION:Place A", "END:VEVENT"]
        event_b = ["BEGIN:VEVENT", "DTSTART:29990102T193000Z", "SUMMARY:Stage show", "LOCATION:Place B", "END:VEVENT"]
        self.assertNotEqual(event_dedupe_key(event_a), event_dedupe_key(event_b))

    def test_rejects_non_calendar_text(self):
        with self.assertRaises(ValueError):
            parse_source_calendar("This isn't an ICS file", "source")


if __name__ == "__main__":
    unittest.main()
