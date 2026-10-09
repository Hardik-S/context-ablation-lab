import unittest

from src.label_count import count_labels


class CountLabelsTests(unittest.TestCase):
    def test_trims_ignores_blanks_preserves_case_and_sorts_keys(self):
        rows = [
            {"label": " beta "},
            {"label": "Alpha"},
            {"label": "beta"},
            {"label": "   "},
            {},
            {"label": None},
            {"label": 7},
        ]
        result = count_labels(rows)
        self.assertEqual(result, {"Alpha": 1, "beta": 2})
        self.assertEqual(list(result), ["Alpha", "beta"])


if __name__ == "__main__":
    unittest.main()
