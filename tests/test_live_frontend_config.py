from __future__ import annotations

import unittest

from configure_live_frontend import normalize_api_base
from live_smoke import comparable_name as smoke_comparable_name
from submission_preflight import comparable_name as preflight_comparable_name


class LiveFrontendConfigTests(unittest.TestCase):
    def test_https_origin_is_normalized(self):
        self.assertEqual(
            normalize_api_base("https://commonground.onrender.com/"),
            "https://commonground.onrender.com",
        )

    def test_non_https_or_path_is_rejected(self):
        for value in ("http://example.com", "https://example.com/api", "example.com"):
            with self.assertRaises(ValueError):
                normalize_api_base(value)

    def test_smoke_name_matching_ignores_diacritics_and_punctuation(self):
        for normalize in (smoke_comparable_name, preflight_comparable_name):
            self.assertEqual(normalize("Amélie"), normalize("Amelie"))
            self.assertEqual(normalize("Spider-Man"), normalize("Spider Man"))


if __name__ == "__main__":
    unittest.main()
