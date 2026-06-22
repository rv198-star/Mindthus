import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def iter_test_cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_test_cases(item)
        else:
            yield item


class TplanDiscoveryContractTests(unittest.TestCase):
    def test_root_unittest_discovery_includes_tplan_tests(self):
        suite = unittest.defaultTestLoader.discover(str(REPO / "tests"), pattern="test_*.py")
        test_ids = [test.id() for test in iter_test_cases(suite)]
        joined = "\n".join(test_ids)

        self.assertIn("test_mission_pulse.MissionPulseTests", joined)
        self.assertIn("test_survey_and_packet.SurveyAndPacketTests", joined)


if __name__ == "__main__":
    unittest.main()
