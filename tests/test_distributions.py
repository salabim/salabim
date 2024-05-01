import salabim as sim
import pytest
import collections


def collect(dis, n=10000):
    m = sim.Monitor()
    for _ in range(n):
        m.tally(dis())
    return m


def test_randomseeds():
    env = sim.Environment()
    sim.random_seed(123)
    m123_0 = collect(sim.Uniform(1, 2), n=10)
    sim.random_seed(123)
    m123_1 = collect(sim.Uniform(1, 2), n=10)
    sim.random_seed(345)
    m345_0 = collect(sim.Uniform(1, 2), n=10)
    sim.random_seed("*")
    mr_0 = collect(sim.Uniform(1, 2), n=10)
    sim.random_seed("*")
    mr_1 = collect(sim.Uniform(1, 2), n=10)
    assert m123_0.x() == m123_1.x()
    assert m123_0.x() != m345_0.x()
    assert mr_0.x() != mr_1.x()


def test_constant():
    env = sim.Environment()
    m = collect(sim.Constant(1))
    assert m.mean() == 1


def test_uniform():
    m = collect(sim.Uniform(1, 2))
    assert m.mean() == pytest.approx(1.5, rel=1e-2)


def test_bounded():
    env = sim.Environment()
    m = collect(sim.Bounded(sim.Uniform(-2, 4), 0, 2), n=100)
    assert m.mean() == pytest.approx(1, rel=1e-1)
    assert m.minimum() >= 0
    assert m.maximum() <= 2

    m = collect(sim.Bounded(sim.Uniform(-2, 4), 5, fail_value=sim.inf), n=100)
    assert m.mean() == sim.inf

    m = sim.Monitor()
    for _ in range(100):
        m.tally(sim.Uniform(-2, 4).bounded_sample(0, 2))
    assert m.mean() == pytest.approx(1, rel=1e-1)
    assert m.minimum() >= 0
    assert m.maximum() <= 2

    m = sim.Monitor()
    for _ in range(100):
        m.tally(sim.Uniform(-2, 4).bounded_sample(5, fail_value=sim.inf))
    assert m.mean() == sim.inf

    m = collect(sim.Bounded(sim.Normal(4, 3), 0))
    assert m.mean() > 4
    assert m.minimum() >= 0


def test_triangular():
    env = sim.Environment()
    m = collect(sim.Triangular(1, 6, 2))
    assert m.mean() == pytest.approx(3, rel=1e-2)


def test_normal():
    env = sim.Environment()
    m = collect(sim.Normal(4, 3))
    assert m.mean() == pytest.approx(4, rel=1e-2)
    assert m.std() == pytest.approx(3, rel=1e-2)


def test_int_uniform():
    env = sim.Environment()
    m = collect(sim.IntUniform(1, 6))
    assert m.mean() == pytest.approx(3.5, rel=1e-2)
    assert set(m.x()) == {1, 2, 3, 4, 5, 6}
    count = collections.Counter(m.x())
    for v, n in count.items():
        assert n == pytest.approx(10000 / 6, rel=1e-1)


def test_pdf():
    env = sim.Environment()
    m = collect(sim.Pdf((1,10,2,70,3,20)))
    assert m.mean() == pytest.approx(2.1, rel=1e-2)
    m = collect(sim.Pdf((1,2,3),(10,70,20)))
    assert m.mean() == pytest.approx(2.1, rel=1e-2)
    d = {1:10, 2:70, 3:20}
    m = collect(sim.Pdf(d.keys(),d.values()))
    assert m.mean() == pytest.approx(2.1, rel=1e-2)
    m = collect(sim.Pdf(d))
    assert m.mean() == pytest.approx(2.1, rel=1e-2)

def test_scipy_distribution():
    try:
        import scipy.stats as st
    except ModuleNotFoundError:
        pytest.skip("could not import scipy")

    env = sim.Environment()

    m = collect(sim.External(st.norm, loc=5, scale=1))
    assert m.mean() == pytest.approx(5, rel=1e-2)

    m = collect(sim.External(st.norm, loc=1, scale=1, size=4))
    assert m.mean() == pytest.approx(1, rel=1e-2)


def test_numpy_distribution():
    try:
        import numpy as np
    except ImportError:
        pytest.skip("could not import numpy")

    env = sim.Environment(time_unit="hours")

    m = collect(sim.External(np.random.laplace, loc=5, scale=1, size=None, time_unit="days"))
    assert m.mean() == pytest.approx(env.days(5), rel=1e-2)


def test_random_distribution():
    import random
    import math

    env = sim.Environment()

    dis = sim.External(random.lognormvariate, mu=5, sigma=1)
    m = sim.Monitor()
    for _ in range(10000):
        m.tally(math.log(dis()))
    assert m.mean() == pytest.approx(5, rel=1e-2)


def test_Distribution_distribution():
    env = sim.Environment()
    m = collect(sim.Distribution("Uniform(1,2)"))
    assert m.mean() == pytest.approx(1.5, rel=1e-2)
    m = collect(sim.Distribution("U(1,2)"))
    assert m.mean() == pytest.approx(1.5, rel=1e-2)
    m = collect(sim.Distribution("UNIFORM(1,2)"))
    assert m.mean() == pytest.approx(1.5, rel=1e-2)
    with pytest.raises(NameError):
        m = collect(sim.Distribution("Unusual(1,2)"))
    with pytest.raises(NameError):
        m = collect(sim.Distribution("Uniformdistribution(1,2)"))
    with pytest.raises(AttributeError):
        m = collect(sim.Distribution("uniform(1)", time_unit="minutes"))
    env = sim.Environment(time_unit="seconds")
    m = collect(sim.Distribution('uniform(0,2, "minutes")', time_unit="hours"))
    assert m.mean() == pytest.approx(60, rel=1e-2)
    m = collect(sim.Distribution("0,2", time_unit="minutes"))
    assert m.mean() == pytest.approx(60, rel=1e-2)
    m = collect(sim.Distribution("uniform(1, time_unit='hours')", time_unit="minutes"))
    assert m.mean() == 60 * 60
    m = collect(sim.Distribution("uniform(1, time_unit='hours')"))
    assert m.mean() == 60 * 60
    m = collect(sim.Distribution("uniform(1, 1, 'hours')", time_unit="minutes"))
    assert m.mean() == 60 * 60
    m = collect(sim.Distribution("uniform(1, 1, 'hours')"))
    assert m.mean() == 60 * 60
    with pytest.raises(SyntaxError):
        m = collect(sim.Distribution("uniform(1, 1, ,'hours')", time_unit="minutes"))
    assert m.mean() == 60 * 60
    m = collect(sim.Distribution("1"))
    assert m.mean() == 1
    m = collect(sim.Distribution("1,2"))
    assert m.mean() == pytest.approx(1.5, rel=1e-2)
    m = collect(sim.Distribution("1,6,2"))
    assert m.mean() == pytest.approx(3, rel=1e-2)
    m = collect(sim.Distribution("(1,6,2)"))
    assert m.mean() == pytest.approx(3, rel=1e-2)


def test_expressions():
    c1 = sim.Uniform(1)
    c2 = sim.Uniform(2)
    c3 = sim.Uniform(3)
    c4 = sim.Uniform(4)
    dis = (c1 + c3) / c4 + 2 * c2 - (c4 - c1) * 5 / 3
    m = collect(dis, n=10)
    assert m.mean() == 0
    assert not any(x for x in m.x())  # all 0


def test_map():
    m = collect(sim.Map(sim.Uniform(-1, 1), lambda x: x if x > 0 else 0))
    assert m.minimum() == 0
    assert m.mean() == pytest.approx(0.25, rel=1e-1)
    assert m.number_of_entries() == pytest.approx(2 * m.number_of_entries(ex0=True), rel=1e-1)


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
