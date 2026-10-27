import unittest
from datetime import date, timedelta

from generate_moon_phases import add_months, build_calendar, PHASE_NAMES


class MoonPhaseFeedTests(unittest.TestCase):
    def test_add_months_clamps_month_end(self):
        self.assertEqual(add_months(date(2027, 1, 31), 1), date(2027, 2, 28))
        self.assertEqual(add_months(date(2028, 1, 31), 1), date(2028, 2, 29))

    def test_build_calendar_generates_valid_events_with_stable_uids(self):
        start = date(2026, 1, 1)
        end = date(2028, 1, 1)
        phases = []
        phase_names = list(PHASE_NAMES)
        day = start
        index = 0
        while day <= end and index < 100:
            phases.append({
                "year": day.year,
                "month": day.month,
                "day": day.day,
                "time": "12:34",
                "phase": phase_names[index % len(phase_names)],
            })
            day += timedelta(days=7)
            index += 1

        calendar_text = build_calendar(phases, start, end)
        self.assertTrue(calendar_text.startswith("BEGIN:VCALENDAR\r\n"))
        self.assertTrue(calendar_text.endswith("END:VCALENDAR\r\n"))
        self.assertEqual(calendar_text.count("BEGIN:VEVENT"), 100)
        self.assertIn("UID:moonphase-20260101T123400Z@calendarqueen.de", calendar_text)
        self.assertIn("SUMMARY:Neumond", calendar_text)
        self.assertIn("https://aa.usno.navy.mil/data/api", calendar_text)


if __name__ == "__main__":
    unittest.main()
