import salabim as sim
import pytest


def test(capsys):
    env = sim.Environment(trace=True)
    env.run(1)
    out = capsys.readouterr()[0]
    assert "0.000 main" in out
    assert "+1.000" in out
    save_time_to_str = sim.Environment.time_to_str
    save_duration_to_str = sim.Environment.duration_to_str

    sim.Environment.time_to_str = lambda self, t: f"t={t:4.1f}"
    sim.Environment.duration_to_str = lambda self, duration: f"d={duration:4.1f}"
    env.run(1)
    out = capsys.readouterr()[0]
    assert "t= 2.0" in out
    assert "+d= 1.0" in out

    sim.Environment.time_to_str = save_time_to_str
    sim.Environment.duration_to_str = save_duration_to_str


def test_interp():
    env = sim.Environment()
    with pytest.raises(ValueError):
        sim.interp(0, [], [])
    with pytest.raises(ValueError):
        sim.interp(0, [1, 2], [3])
    assert sim.interp(5, [5], [10]) == 10
    assert sim.interp(5, [0, 10], [0, 20]) == 10
    assert sim.interp(0, [0, 10], [0, 20]) == 0
    assert sim.interp(10, [0, 10], [0, 20]) == 20
    assert sim.interp(-1, [0, 10], [0, 20]) == 0
    assert sim.interp(11, [0, 10], [0, 20]) == 20

def test_env_prefixing():
    env1 = sim.Environment()
    env = sim.Environment()
    assert sim.Component().env == env
    assert sim.Component(env=env).env == env
    assert sim.Component(env=env1).env == env1
    assert env.Component().env == env
    assert env.Component(env=env).env == env
    assert env.Component(env=env1).env == env1
    assert env1.Component().env == env1
    assert env1.Component(env=env).env == env
    assert env1.Component(env=env1).env == env1


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
