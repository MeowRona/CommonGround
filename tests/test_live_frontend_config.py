from __future__ import annotations

import unittest

from configure_live_frontend import normalize_api_base


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


if __name__ == "__main__":
    unittest.main()
