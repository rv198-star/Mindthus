"""One normal-input smoke check for the unchanged legacy canary."""
import unittest

from normalize_record import normalize_record


class LegacyCanarySmokeTest(unittest.TestCase):
    def test_normal_record(self):
        value = {"weight": 7, "enabled": True, "label": "Sample", "id": "record-1"}
        before = value.copy()
        result = normalize_record(value)
        self.assertEqual(result, before)
        self.assertIsNot(result, value)
        self.assertEqual(list(result), ["id", "label", "enabled", "weight"])
        self.assertEqual(value, before)


if __name__ == "__main__":
    unittest.main()
