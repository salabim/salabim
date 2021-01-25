import salabim as sim
import pytest
import tempfile
import pickle
from array import array


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
            for v in range(0, 100):
                self.ml.tally(v)
                self.m.tally(v)
                yield self.hold(1)
                env.ended = True

    class Controller(sim.Component):
        def process(self):
            while not env.ended:
                yield self.hold(sim.Uniform(10, 20)())
                for i in (False, True):
                    env.x[i].ml.monitor(False)
                    env.x[i].interrupt()
                yield self.hold(sim.Uniform(1000, 2000)())
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
    assert env.x[False].ml.mean() == pytest.approx(49.5)
    assert env.x[False].ml.percentile(95) == 94
    assert env.x[False].ml.maximum() == 99
    assert env.x[False].ml.minimum() == 0
    assert env.x[False].ml.duration() == pytest.approx(100)
    assert env.x[False].ml.duration(ex0=True) == pytest.approx(99)
    assert env.x[False].ml.duration_zero() == pytest.approx(1)

    assert env.x[False].m.mean() == 49.5
    assert env.x[False].m.percentile(95) == 94
    assert env.x[False].m.maximum() == 99
    assert env.x[False].m.minimum() == 0
    assert env.x[False].m.number_of_entries() == 100
    assert env.x[False].m.number_of_entries(ex0=True) == 99
    assert env.x[False].m.number_of_entries_zero() == 1

    assert env.x[True].ml.mean() == pytest.approx(49.5)
    assert env.x[True].ml.maximum() == 99
    with pytest.raises(NotImplementedError):
        env.x[True].ml.percentile(95)
    assert env.x[True].ml.minimum() == 0
    assert env.x[True].ml.duration() == pytest.approx(100)
    assert env.x[True].ml.duration(ex0=True) == pytest.approx(99)
    assert env.x[True].ml.duration_zero() == pytest.approx(1)

    assert env.x[True].m.mean() == 49.5
    assert env.x[True].m.maximum() == 99
    with pytest.raises(NotImplementedError):
        env.x[True].m.percentile(95)
    assert env.x[True].m.minimum() == 0
    assert env.x[True].m.number_of_entries() == 100
    assert env.x[True].m.number_of_entries(ex0=True) == 99
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
    assert env.m.percentile(95) == pytest.approx(0.9)
    assert env.m.maximum() == 1
    assert env.m.minimum() == 0

    env.m = sim.Monitor("m")
    env.m.tally(0)
    env.m.tally(1)

    assert env.m.mean() == 0.5
    assert env.m.percentile(95) == pytest.approx(0.9)
    assert env.m.maximum() == 1
    assert env.m.minimum() == 0
    env.m = sim.Monitor("m")

    env.m.tally("red", 1)
    env.m.tally("blue", 2)
    env.m.tally("green", 1)
    env.m.tally("green", 3)
    env.m.tally("yellow")
    env.m.tally(2)
    env.m.tally(8)

    assert env.m.mean() == 1
    assert env.m.percentile(95) == pytest.approx(5)
    assert env.m.maximum() == 8
    assert env.m.minimum() == 0

    assert env.m.value_weight("blue") == 2
    assert env.m.value_weight(("blue", "green")) == 6
    assert env.m.value_weight("purple") == 0

    assert env.m.value_number_of_entries("blue") == 1
    assert env.m.value_number_of_entries(("blue", "green")) == 3
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
            yield self.hold(till=5)
            self.ml.tally(5)
            yield self.hold(till=6)
            self.ml.monitor(False)
            self.ml.tally(6)
            yield self.hold(till=7)
            self.ml.tally(7)
            yield self.hold(till=7.5)
            assert self.ml() == 7
            yield self.hold(till=8)
            self.ml.tally(8)
            self.ml.monitor(True)
            yield self.hold(till=9)
            self.ml.tally(9)
            yield self.hold(1000)

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
    q=sim.Queue()
    all_monitors = r.all_monitors() + s.all_monitors() + q.all_monitors()
    assert len(all_monitors) == 8 + 3 + 2
    for m in all_monitors:
        assert not m.stats_only()
    r.reset_monitors(stats_only=True)
    s.reset_monitors(stats_only=True)
    q.reset_monitors(stats_only=True)

    for m in all_monitors:
        assert m.stats_only()

def test_pickle():
    class X(sim.Component):
        def process(self):
            for v in range(1, 101):
                env.ml.tally(v)
                env.m.tally(v)
                yield self.hold(1)
                env.ended = True

    class Controller(sim.Component):
        def process(self):
            while not env.ended:
                yield self.hold(sim.Uniform(10, 20)())
                env.ml.monitor(False)
                env.x.interrupt()
                yield self.hold(sim.Uniform(1000, 2000)())
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
    assert env.ml.mean() == pytest.approx(50.5)
    assert env.ml.percentile(95) == 95
    assert env.ml.maximum() == 100
    assert env.ml.minimum() == 1

    assert env.m.mean() == 50.5
    assert env.m.percentile(95) == 95
    assert env.m.maximum() == 100
    assert env.m.minimum() == 1


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
90% percentile        2            2.300
95% percentile        2.500        2.650
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
            yield self.hold(0)
            yield self.request(r, mode="def")
            yield self.hold(10.1, mode="ghi")
            self.release()
            yield self.passivate(mode="jkl")

    class Interrupter(sim.Component):
        def process(self):
            yield self.hold(6)
            x0.interrupt()
            x1.interrupt()
            x2.interrupt()
            yield self.hold(4)
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


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
