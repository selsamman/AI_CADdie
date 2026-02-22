"""Per-scene geometry assertions for scene regression cases.

Each module in this package corresponds to a case file in scene_tests/cases.

Convention:
  - For a case named "foo.scene.json" (base name "foo"), create:
      scene_tests/assertions/foo.py
    which defines:
      def assert_scene(resolved_scene: dict) -> None

These assertions are executed by:
  - python -m scene_tests.run_all
  - the unittest wrapper tests/test_scene_regressions.py
"""
