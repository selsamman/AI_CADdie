from __future__ import annotations

from scene_tests.assertions._util import assert_almost_equal, assert_has_object


def _centroid(fp: list[list[float]]) -> tuple[float, float]:
    xs = [float(p[0]) for p in fp]
    ys = [float(p[1]) for p in fp]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def assert_scene(resolved_scene: dict) -> None:
    a = assert_has_object(resolved_scene, "A")
    b = assert_has_object(resolved_scene, "B")

    ax, ay = _centroid(a["geom"]["footprint"])
    bx, by = _centroid(b["geom"]["footprint"])

    # Expect 3 studs at 25%, 50%, 75% between centroids.
    for i, t in enumerate((0.25, 0.5, 0.75), start=1):
        sid = f"Stud_{i}"
        stud = assert_has_object(resolved_scene, sid)
        start = (stud.get("params", {}) or {}).get("placement", {}).get("start")
        if not (isinstance(start, list) and len(start) == 2):
            raise AssertionError(f"Expected {sid}.params.placement.start to exist")
        sx, sy = float(start[0]), float(start[1])

        ex = ax + (bx - ax) * t
        ey = ay + (by - ay) * t

        assert_almost_equal(sx, ex, tol=1e-6)
        assert_almost_equal(sy, ey, tol=1e-6)
