import salabim as sim
import pytest


def test_interpolate():
    assert sim.interpolate(0.5, 0, 1, 0, 100) == 50
    assert sim.interpolate(-1, 0, 1, 0, 100) == 0
    assert sim.interpolate(2, 0, 1, 0, 100) == 100
    assert sim.interpolate(1, 0, sim.inf, 0, 100) == 0
    assert sim.interpolate(0.5, 1, 1, 0, 100) == 100

    assert sim.interpolate(0.5, 1, 0, 100, 0) == 50
    assert sim.interpolate(-1, 1, 0, 100, 0) == 0
    assert sim.interpolate(2, 1, 0, 100, 0) == 100
    assert sim.interpolate(1, sim.inf, 0, 100, 0) == 0


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
