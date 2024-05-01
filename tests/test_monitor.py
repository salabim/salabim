import salabim as sim
import pytest
import tempfile
import pickle
from array import array
import math
import datetime


def compare_output(out0, out1):
    lines0 = out0.split("\n")
    lines1 = out1.split("\n")
    if len(lines0) != len(lines1):
        return False

    for line0, line1 in zip(lines0, lines1):
        if line0.rstrip() != line1.rstrip():
            return False
    return True


def test_monitor1():
    class X(sim.Component):
        def setup(self, stats_only=False):
            self.ml = sim.Monitor("ml", level=True, stats_only=stats_only)
            self.m = sim.Monitor("m", stats_only=stats_only)

        def process(self):
            for v in range(0, 101):
                self.ml.tally(v)
                self.m.tally(v)
                self.hold(1)
                env.ended = True

    class Controller(sim.Component):
        def process(self):
            while not env.ended:
                self.hold(sim.Uniform(10, 20)())
                for i in (False, True):
                    env.x[i].ml.monitor(False)
                    env.x[i].interrupt()
                self.hold(sim.Uniform(1000, 2000)())
                for i in (False, True):
                    env.x[i].ml.monitor(True)
                    env.x[i].resume()

    env = sim.Environment()
    env.ml = sim.Monitor("ml", level=True)
    env.m = sim.Monitor("m")
    env.ended = False
    env.x = {}
    for i in (False, True):
        env.x[i] = X(stats_only=i)
    Controller()
    env.run()
    assert env.x[False].ml.mean() == pytest.approx(50)
    assert env.x[False].ml.percentile(95) == 95
    assert env.x[False].ml.maximum() == 100
    assert env.x[False].ml.minimum() == 0
    assert env.x[False].ml.duration() == pytest.approx(101)
    assert env.x[False].ml.duration(ex0=True) == pytest.approx(100)
    assert env.x[False].ml.duration_zero() == pytest.approx(1)

    assert env.x[False].m.mean() == 50
    assert env.x[False].m.percentile(95) == 95
    assert env.x[False].m.maximum() == 100
    assert env.x[False].m.minimum() == 0
    assert env.x[False].m.number_of_entries() == 101
    assert env.x[False].m.number_of_entries(ex0=True) == 100
    assert env.x[False].m.number_of_entries_zero() == 1

    assert env.x[True].ml.mean() == pytest.approx(50)
    assert env.x[True].ml.maximum() == 100
    with pytest.raises(NotImplementedError):
        env.x[True].ml.percentile(95)
    assert env.x[True].ml.minimum() == 0
    assert env.x[True].ml.duration() == pytest.approx(101)
    assert env.x[True].ml.duration(ex0=True) == pytest.approx(100)
    assert env.x[True].ml.duration_zero() == pytest.approx(1)

    assert env.x[True].m.mean() == 50
    assert env.x[True].m.maximum() == 100
    with pytest.raises(NotImplementedError):
        env.x[True].m.percentile(95)
    assert env.x[True].m.minimum() == 0
    assert env.x[True].m.number_of_entries() == 101
    assert env.x[True].m.number_of_entries(ex0=True) == 100
    assert env.x[True].m.number_of_entries_zero() == 1

    assert env.x[False].m.std() == pytest.approx(env.x[True].m.std())
    assert env.x[False].ml.std() == pytest.approx(env.x[True].ml.std())


def test_monitor2():
    env = sim.Environment()
    env.m = sim.Monitor("m")
    env.m.tally(0)
    env.m.tally(0)
    env.m.tally(1, 2)

    assert env.m.mean() == 0.5
    assert env.m.percentile(50) == pytest.approx(0.5)
    assert env.m.percentile(50, interpolation="lower") == pytest.approx(0)
    assert env.m.percentile(50, interpolation="higher") == pytest.approx(1)

    assert env.m.percentile(95) == pytest.approx(1)

    assert env.m.maximum() == 1
    assert env.m.minimum() == 0

    env.m = sim.Monitor("m")
    env.m.tally(0)
    env.m.tally(0)
    env.m.tally(1)
    env.m.tally(1)

    assert env.m.mean() == 0.5
    assert env.m.percentile(50) == pytest.approx(0.5)
    assert env.m.percentile(50, interpolation="lower") == pytest.approx(0)
    assert env.m.percentile(50, interpolation="higher") == pytest.approx(1)

    assert env.m.percentile(95) == pytest.approx(1)

    assert env.m.maximum() == 1
    assert env.m.minimum() == 0

    env.m = sim.Monitor("m")
    env.m.tally(0)
    env.m.tally(1)

    assert env.m.mean() == 0.5
    assert env.m.percentile(95) == pytest.approx(0.95)
    assert env.m.maximum() == 1
    assert env.m.minimum() == 0
    env.m = sim.Monitor("m")

    env.m.tally("red")
    env.m.tally("blue")
    env.m.tally("blue")
    env.m.tally("green")
    env.m.tally("green")
    env.m.tally("green")
    env.m.tally("green")
    env.m.tally("green")

    env.m.tally("yellow")
    env.m.tally(2)
    env.m.tally(8)

    assert env.m.mean() == pytest.approx(10 / 11)
    assert env.m.percentile(95) == pytest.approx(5)
    assert env.m.maximum() == 8
    assert env.m.minimum() == 0

    assert env.m.value_weight("blue") == 2
    assert env.m.value_weight(("blue", "green")) == 7
    assert env.m.value_weight("purple") == 0

    assert env.m.value_number_of_entries("blue") == 2
    assert env.m.value_number_of_entries(("blue", "green")) == 7
    assert env.m.value_number_of_entries("purple") == 0


def test_monitor_3():
    env = sim.Environment()
    for i in (False, True):
        m = sim.Monitor("m", level=False, stats_only=True)
        m.tally(1)
        m.tally(2)
        m.tally("3")
        m.tally("?")
        m.tally(None)
        assert m.mean() == 1.2
        assert m.number_of_entries() == 5
        assert m.number_of_entries(ex0=True) == 3
        assert m.number_of_entries_zero() == 2


def test_monitor4():
    class X(sim.Component):
        def setup(self, stats_only=False):
            self.ml = sim.Monitor("ml", level=True, initial_tally=10, stats_only=stats_only)

        def process(self):
            self.hold(till=5)
            self.ml.tally(5)
            self.hold(till=6)
            self.ml.monitor(False)
            self.ml.tally(6)
            self.hold(till=7)
            self.ml.tally(7)
            self.hold(till=7.5)
            assert self.ml() == 7
            self.hold(till=8)
            self.ml.tally(8)
            self.ml.monitor(True)
            self.hold(till=9)
            self.ml.tally(9)
            self.hold(1000)

    env = sim.Environment()
    env.ml = sim.Monitor("ml", level=True)
    env.x = {}
    for i in (False, True):
        env.x[i] = X(stats_only=i)
    env.run()
    assert env.x[False].ml.get() == 9
    assert env.x[False].ml() == 9
    assert env.x[False].ml(env.now()) == 9
    assert env.x[False].ml(0.5) == 10
    assert env.x[False].ml(8.5) == 8
    assert env.x[False].ml(6.5) == -sim.inf

    assert env.x[True].ml.get() == 9
    assert env.x[True].ml() == 9
    assert env.x[True].ml(env.now()) == 9
    with pytest.raises(NotImplementedError):
        env.x[True].ml(0.5)


def test_monitor_5():
    env = sim.Environment()
    r = sim.Resource()
    s = sim.State()
    q = sim.Queue()
    all_monitors = r.all_monitors() + s.all_monitors() + q.all_monitors()
    assert len(all_monitors) == 8 + 3 + 2
    for m in all_monitors:
        assert not m.stats_only()
    r.reset_monitors(stats_only=True)
    s.reset_monitors(stats_only=True)
    q.reset_monitors(stats_only=True)

    for m in all_monitors:
        assert m.stats_only()


def test_percentile():
    class X(sim.Component):
        def process(self):
            for value in (4, 1, 1, 3, 6, 3, 0, 7, 2, 2):
                env.ml.tally(value)
                env.m.tally(value)
                self.hold(1)

    env = sim.Environment()

    env.m = sim.Monitor()
    assert math.isnan(env.m.percentile(0))
    env.ml = sim.Monitor(level=True)
    assert env.ml.percentile(0) == 0
    env.ml = sim.Monitor(level=True, initial_tally=7)
    assert env.ml.percentile(0) == 7
    env.m.tally(1)
    assert env.m.percentile(0) == env.m.percentile(50) == env.m.percentile(100) == env.m.percentile(-1) == env.m.percentile(101) == 1
    env.ml.tally(1)
    assert env.ml.percentile(0) == env.ml.percentile(50) == env.ml.percentile(100) == env.ml.percentile(-1) == env.ml.percentile(101) == 1

    env.m = sim.Monitor()
    env.ml = sim.Monitor(level=True)
    X()
    env.run(10)
    env.m.tally(15)
    assert env.m.mean() == 4
    assert env.ml.mean() == 2.9
    assert env.m.percentile(10) == 1
    assert env.m.percentile(5) == 0.5
    assert env.m.percentile(5, interpolation="lower") == 0
    assert env.m.percentile(5, interpolation="higher") == 1
    assert env.m.percentile(5, interpolation="midpoint") == 0.5
    assert env.m.percentile(5, interpolation="linear") == 0.5
    assert env.m.percentile(5, interpolation="nearest") == 0
    assert env.m.percentile(4, interpolation="nearest") == 0
    assert env.m.percentile(6, interpolation="nearest") == 1
    with pytest.raises(ValueError):
        env.m.percentile(5, interpolation="closest") == 1

    assert env.ml.percentile(5) == 0
    assert env.ml.percentile(15) == 1
    assert env.ml.percentile(95) == 7
    assert env.ml.percentile(10) == 0.5
    assert env.ml.percentile(10, interpolation="lower") == 0
    assert env.ml.percentile(10, interpolation="higher") == 1
    assert env.ml.percentile(10, interpolation="midpoint") == 0.5
    assert env.ml.percentile(10, interpolation="linear") == 0.5
    with pytest.raises(ValueError):
        env.ml.percentile(10, interpolation="nearest") == 1


def test_pickle():
    class X(sim.Component):
        def process(self):
            for v in range(101):
                env.ml.tally(v)
                env.m.tally(v)
                self.hold(1)
                env.ended = True

    class Controller(sim.Component):
        def process(self):
            while not env.ended:
                self.hold(sim.Uniform(10, 20)())
                env.ml.monitor(False)
                env.x.interrupt()
                self.hold(sim.Uniform(1000, 2000)())
                env.ml.monitor(True)
                env.x.resume()

    env = sim.Environment()
    env.ml = sim.Monitor("ml", level=True)
    env.m = sim.Monitor("m")
    env.ended = False

    env.x = X()
    Controller()
    env.run()
    with tempfile.TemporaryDirectory() as tmp_path:
        pickle.dump(env.ml.freeze(), open(tmp_path + "ml.pickle", "wb"))
        pickle.dump(env.m.freeze(), open(tmp_path + "m.pickle", "wb"))

        env = sim.Environment()  # to reset env
        env.ml = pickle.load(open(tmp_path + "ml.pickle", "rb"))
        env.m = pickle.load(open(tmp_path + "m.pickle", "rb"))
    assert env.ml.mean() == pytest.approx(50)
    assert env.ml.percentile(95) == 95
    assert env.ml.maximum() == 100

    assert env.m.mean() == pytest.approx(50)
    assert env.m.median() == pytest.approx(50)
    assert env.m.percentile(95) == 95
    assert env.m.maximum() == 100
    assert env.m.minimum() == 0


def test_values():
    env = sim.Environment()
    env.m = sim.Monitor("m")
    values = [1, 2, 3, "one", "two", "three", 1, 1, 1, 1.1]
    for value in values:
        env.m.tally(value)
    assert compare_output(
        env.m.print_histogram(as_str=True),
        """\
Histogram of m
                        all    excl.zero         zero
-------------- ------------ ------------ ------------
entries              10            7            3
mean                  1.010        1.443
std.deviation         0.895        0.721

minimum               0            1
median                1            1
90% percentile        2.100        2.400
95% percentile        2.550        2.700
maximum               3            3

           <=       entries     %  cum%
        0             3      30    30   ************************|
        1             4      40    70   ********************************                        |
        2             2      20    90.0 ****************                                                        |
        3             1      10   100.0 ********                                                                       |
          inf         0       0   100.0                                                                                |
""",
    )

    assert compare_output(
        env.m.print_histogram(values=True, as_str=True),
        """\
Histogram of m
entries             10

value               entries     %
1                         4  40   ********************************
1.1                       1  10   ********
2                         1  10   ********
3                         1  10   ********
one                       1  10   ********
three                     1  10   ********
two                       1  10   ********
""",
    )
    set_values_in = set(values)
    set_values_out = set(env.m.values())
    assert set_values_in == set_values_out


def test_level_values():
    class X(sim.Component):
        def process(self):
            self.set_mode("abc")
            self.hold(0)
            self.request(r, mode="def")
            self.hold(10.1, mode="ghi")
            self.release()
            self.passivate(mode="jkl")

    class Interrupter(sim.Component):
        def process(self):
            self.hold(6)
            x0.interrupt()
            x1.interrupt()
            x2.interrupt()
            self.hold(4)
            x0.resume()
            x1.resume()
            x2.resume()

    def status_map(status):
        return sim.statuses().index(status)

    modes = "abc def ghi jkl".split()

    env = sim.Environment(trace=False)

    r = sim.Resource("r")
    x0 = X(process="", mode="abc")
    x1 = X(process="")
    x2 = X(process="")
    Interrupter()

    env.run(4.3)
    x0.activate()
    x1.activate()
    x2.activate()

    env.run(till=50)

    assert x1.status.value_duration("requesting") == pytest.approx(10.1)

    assert x0.mode.xt(force_numeric=None) == (["abc", "ghi", "jkl", "jkl"], array("d", [0.0, 4.3, 18.4, 50.0]))
    assert x0.status.xt(force_numeric=None) == (
        ["data", "scheduled", "interrupted", "scheduled", "passive", "passive"],
        array("d", [0.0, 4.3, 6.0, 10.0, 18.4, 50.0]),
    )
    assert x0.status.values() == ["data", "interrupted", "passive", "scheduled"]
    assert x0.mode.values() == ["abc", "ghi", "jkl"]

    assert compare_output(
        x0.mode.print_histogram(values=True, ex0=True, as_str=True),
        """\
Histogram of x.0.mode[ex0]
duration            50

value                     duration     %
abc                          4.300   8.6 ******
ghi                         14.100  28.2 **********************
jkl                         31.600  63.2 **************************************************
""",
    )
    assert compare_output(
        x0.status.print_histogram(values=True, as_str=True),
        """\
Histogram of x.0.status
duration            50

value                     duration     %
data                         4.300   8.6 ******
interrupted                  4       8   ******
passive                     31.600  63.2 **************************************************
scheduled                   10.100  20.2 ****************
""",
    )
    assert compare_output(
        x0.status.print_histogram(values=["scheduled", "current", "passive"], as_str=True),
        """\
Histogram of x.0.status
duration            50

value                     duration     %
scheduled                   10.100  20.2 ****************
current                      0       0
passive                     31.600  63.2 **************************************************
<rest>                       8.300  16.6 *************
""",
    )
    assert compare_output(
        x0.status.print_histogram(values=["scheduled", "current", "passive"], as_str=True, sort_on_duration=True),
        """\
Histogram of x.0.status
duration            50

value                     duration     %
passive                     31.600  63.2 **************************************************
scheduled                   10.100  20.2 ****************
current                      0       0
<rest>                       8.300  16.6 *************
""",
    )

    assert compare_output(
        x0.status.print_histogram(values=True, as_str=True),
        """\
Histogram of x.0.status
duration            50    

value                     duration     %
data                         4.300   8.6 ******
interrupted                  4       8   ******
passive                     31.600  63.2 **************************************************
scheduled                   10.100  20.2 ****************
""",
    )

    assert compare_output(
        x0.status.print_histogram(values=True, sort_on_duration=True, as_str=True),
        """\
Histogram of x.0.status
duration            50    

value                     duration     %
passive                     31.600  63.2 **************************************************
scheduled                   10.100  20.2 ****************
data                         4.300   8.6 ******
interrupted                  4       8   ******
""",
    )


def test_map():
    class X1(sim.Component):
        def process(self):
            m1.tally("x1.0")
            self.hold(2)
            m1.tally("x1.2")
            self.hold(2)
            m1.tally("x1.4")

    class X2(sim.Component):
        def process(self):
            self.hold(1)
            m2.tally("x2.1")
            self.hold(1)
            m2.tally("x2.3")
            self.hold(1)
            m2.tally("x2.4")

    class M2Spoiler(sim.Component):
        def process(self):
            self.hold(1.5)
            m2.monitor(False)
            self.hold(2)
            m2.monitor(True)

    inf = sim.inf
    env = sim.Environment()
    X1()
    X2()
    M2Spoiler()
    m = sim.Monitor("m", level=False)
    m.tally(45.6)
    m.tally(6)
    m.tally(5.8)
    m1 = sim.Monitor("m1", level=True, initial_tally="x1.0")
    m2 = sim.Monitor("m2", level=True, initial_tally="x2.0")
    env.run(10)
    m3 = m1.x_map(lambda x1, x2: f"({x1},{x2})", [m2])
    assert m3.xt(force_numeric=False) == (
        ["(x1.0,x2.0)", "(x1.0,x2.1)", -inf, -inf, "(x1.2,x2.4)", "(x1.4,x2.4)", -inf, -inf],
        array("d", [0.0, 1.0, 1.5, 2.0, 3.5, 4.0, 10.0, 10.0]),
    )
    assert m.x_map(int).x() == [45, 6, 5]
    
def test_as_dataframe():
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("could not import pandas")

    env = sim.Environment()
    level_monitor0 = env.Monitor("level monitor0", level=True)
    level_monitor1 = env.Monitor("level monitor1", level=True)
    non_level_monitor = env.Monitor("non level monitor")
    
    env.run(till=1)
    level_monitor0.tally(11)
    non_level_monitor.tally(11)
    env.run(till=2)
    level_monitor0.tally(12)
    non_level_monitor.tally(12)
    env.run(till=3)
    level_monitor1.tally(13)
    non_level_monitor.tally(13)
    env.run(till=4.5)
    level_monitor0.tally(14.5)
    level_monitor1.tally(14.5)
    non_level_monitor.tally(14.5)
    env.run(till=5)
    level_monitor0.tally(15)
    non_level_monitor.tally(15)
    env.run(till=10)
    level_monitor0.tally(20)
    non_level_monitor.tally(20)
    
    df = level_monitor0.as_resampled_dataframe(delta_t=1, extra_monitors=[level_monitor1], min_t=-1, max_t=22)
    df0 = pd.DataFrame(
        {
            "t": list(sim.arange(-1, 22)),
            "level monitor0.x": [pd.NA, 0, 11, 12, 12, 12, 15, 15, 15, 15, 15, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20],
            "level monitor1.x": [pd.NA, 0, 0, 0, 13, 13, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5],
        }
    )
    assert df.equals(df0)
    
    df = non_level_monitor.as_dataframe(include_t=False)
    df0 = pd.DataFrame({"non level monitor.x": [11, 12, 13, 14.5, 15, 20]})
    assert df.equals(df0)
    
    df = non_level_monitor.as_dataframe()
    df0 = pd.DataFrame({"t": [1, 2, 3, 4.5, 5, 10], "non level monitor.x": [11, 12, 13, 14.5, 15, 20]})
    assert df.equals(df0)    

def test_as_dataframe_use_datetime0():
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("could not import pandas")

    env = sim.Environment(datetime0=datetime.datetime(2023,1,1), time_unit="days")
    level_monitor0 = env.Monitor("level monitor0", level=True)
    level_monitor1 = env.Monitor("level monitor1", level=True)
    non_level_monitor = env.Monitor("non level monitor")

    env.run(till=1.3)
    level_monitor0.tally(11)
    env.run(till=2.5)
    level_monitor0.tally(12)
    env.run(till=3.1)
    level_monitor1.tally(14)
    env.run(till=4.8)
    level_monitor0.tally(14.5)
    env.run(till=5)
    env.datetime0(datetime.datetime(2023,1,1))
    df = level_monitor0.as_resampled_dataframe(delta_t=datetime.timedelta(days=2), min_t=datetime.datetime(2023,1,3), use_datetime0=True)
    d=datetime.datetime
    df0=pd.DataFrame({"t": [d(2023,1,3),d(2023,1,5)], "level monitor0.x":[11,12]})
    assert df0.equals(df)
    df = level_monitor0.as_dataframe(use_datetime0=True)
    df0=pd.DataFrame({"t":[d(2023,1,1), d(2023,1,2,7,12),d(2023,1,3,12),d(2023,1,5,19,12)], "level monitor0.x": [0,11,12,14.5]})
    assert df0.equals(df)
    df = level_monitor0.as_dataframe()
    df0=pd.DataFrame({"t":[0,1.3,2.5,4.8], "level monitor0.x": [0,11,12,14.5]})
    assert df0.equals(df)    
if __name__ == "__main__":
    pytest.main(["-vv", "-s", "-x", __file__])
