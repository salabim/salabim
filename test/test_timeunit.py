import salabim as sim
import pytest
import datetime

import collections


def collect(dis, n=10000):
    m = sim.Monitor()
    for _ in range(n):
        m.tally(dis())
    return m


def test_time_unit():
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


def test_datetime0t():
    class X(sim.Component):
        ...

    env = sim.Environment()
    assert env.datetime0() == False
    assert env.time_to_str(1) == "     1.000"
    assert env.duration_to_str(1) == "1.000"

    env = sim.Environment(datetime0=False)
    assert env.datetime0() == False
    assert env.time_to_str(1) == "     1.000"
    assert env.duration_to_str(1) == "1.000"

    env = sim.Environment(datetime0=None)
    assert env.datetime0() == False
    assert env.time_to_str(1) == "     1.000"
    assert env.duration_to_str(1) == "1.000"

    with pytest.raises(ValueError):
        env = sim.Environment(datetime0=12)

    env = sim.Environment(datetime0=True)
    assert env.datetime0() == datetime.datetime(1970, 1, 1)

    assert env.time_to_str(1) == "Thu 1970-01-01 00:00:01"
    assert env.duration_to_str(1) == "00:00:01"

    env = sim.Environment(datetime0=datetime.datetime(2022, 4, 29))
    assert env.datetime0() == datetime.datetime(2022, 4, 29)

    assert env.time_to_str(1) == "Fri 2022-04-29 00:00:01"
    assert env.duration_to_str(1) == "00:00:01"

    env = sim.Environment(datetime0=datetime.datetime(2022, 4, 29), time_unit="days")
    assert env.datetime0() == datetime.datetime(2022, 4, 29)

    assert env.time_to_str(1) == "Sat 2022-04-30 00:00:00"
    assert env.duration_to_str(1) == "1 00:00:00"

    env = sim.Environment()
    assert env.get_time_unit() == "n/a"
    env.datetime0(True) == datetime.datetime(1970, 1, 1)
    assert env.get_time_unit() == "seconds"

    env = sim.Environment(time_unit="minutes")
    assert env.get_time_unit() == "minutes"
    env.datetime0(True) == datetime.datetime(1970, 1, 1)
    assert env.get_time_unit() == "minutes"
    env.datetime0(datetime.datetime(2022, 4, 29)) == datetime.datetime(2022, 4, 29)

    env = sim.Environment(datetime0=datetime.datetime(2022, 4, 29), time_unit="days")
    assert env.t_to_datetime(0.5) == datetime.datetime(2022, 4, 29, 12, 0)
    assert env.duration_to_timedelta(0.5) == datetime.timedelta(hours=12)
    assert env.datetime_to_t(datetime.datetime(2022, 4, 28)) == -1
    assert env.timedelta_to_duration(datetime.timedelta(hours=-12)) == -0.5

    env = sim.Environment(datetime0=True)
    assert env.datetime0() == datetime.datetime(1970, 1, 1)
    x0 = X()
    assert x0.creation_time() == 0
    assert env.time_to_str(x0.creation_time()) == "Thu 1970-01-01 00:00:00"
    env.run(3600)
    env.reset_now()
    assert x0.creation_time() == -3600
    assert env.datetime0() == datetime.datetime(1970, 1, 1, 1)
    assert env.time_to_str(x0.creation_time()) == "Thu 1970-01-01 00:00:00"
    x1 = X()
    assert x1.creation_time() == 0
    assert env.time_to_str(x1.creation_time()) == "Thu 1970-01-01 01:00:00"
    env.datetime0(datetime.datetime(2022, 4, 29))
    assert env.time_to_str(x0.creation_time()) == "Thu 2022-04-28 23:00:00"
    assert env.time_to_str(x1.creation_time()) == "Fri 2022-04-29 00:00:00"


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
