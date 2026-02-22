import unittest


class TestSceneRegressions(unittest.TestCase):
    def test_scene_cases_match_golden_and_assertions(self):
        # This wraps the existing scene_tests runner so it is enforced in CI.
        # The runner:
        #   - generates SCAD outputs into ./tmp/scene_tests_out
        #   - compares against scene_tests/golden/*.scad
        #   - writes resolved scene JSON alongside the SCAD
        #   - runs per-scene assertions from scene_tests/assertions/*.py
        from scene_tests.run_all import main as run_all

        rc = run_all([])
        self.assertEqual(rc, 0, "scene_tests.run_all reported failures")


if __name__ == "__main__":
    unittest.main()
