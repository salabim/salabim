import salabim as sim
import pytest

import collections


def collect(dis, n=10000):
    m = sim.Monitor()
    for _ in range(n):
        m.tally(dis())
    return m


def test():
    env = sim.Environment()
    with pytest.raises(AttributeError):
        env.hours(1)
    env = sim.Environment()
    with pytest.raises(AttributeError):
        env.years(1)
    env = sim.Environment(time_unit="days")
    assert env.years(1 / 365) == pytest.approx(1)
    assert env.weeks(1 / 7) == pytest.approx(1)
    assert env.days(1) == pytest.approx(1)
    assert env.hours(24) == pytest.approx(1)
    assert env.minutes(24 * 60) == pytest.approx(1)
    assert env.seconds(24 * 60 * 60) == pytest.approx(1)
    assert env.milliseconds(24 * 60 * 60 * 1000) == pytest.approx(1)
    assert env.microseconds(24 * 60 * 60 * 1e6) == pytest.approx(1)

    assert env.to_years(365) == pytest.approx(1)
    assert env.to_weeks(7) == pytest.approx(1)
    assert env.to_days(1) == pytest.approx(1)
    assert env.to_hours(1 / 24) == pytest.approx(1)
    assert env.to_minutes(1 / (24 * 60)) == pytest.approx(1)
    assert env.to_seconds(1 / (24 * 60 * 60)) == pytest.approx(1)
    assert env.to_milliseconds(1 / (24 * 60 * 60 * 1000)) == pytest.approx(1)
    assert env.to_microseconds(1 / (24 * 60 * 60 * 1e6)) == pytest.approx(1)
    assert env.to_time_unit("days", 1) == pytest.approx(1)

    m = collect(sim.Uniform(0, 48, time_unit="hours"))
    assert m.mean() == pytest.approx(1, rel=1e-2)


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
