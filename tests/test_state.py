import salabim as sim
import pytest


def test_wait():
    class X(sim.Component):
        def process(self):
            self.hold(1)
            s1.set(1)
            self.hold(1)
            s1.set(2)
            s2.set("red")
            self.hold(2)
            s1.set(30)

    class Z1(sim.Component):
        def process(self):
            while True:
                self.wait((s1, lambda x, component, state: x / 2 > self.env.now()))
                self.hold(1.5)

    class Z2(sim.Component):
        def process(self):
            while True:
                self.wait((s2, lambda x, *_: x in ("red", "yellow")))
                self.hold(1.5)

    def red_or_yellow(x, component, state):
        return x in component.ok_colors

    class Z3(sim.Component):
        def setup(self):
            self.ok_colors = ("red", "yellow")

        def process(self):
            while True:
                self.wait((s2, red_or_yellow))
                self.hold(1.5)

    env = sim.Environment(trace=False)
    s1 = sim.State(name="s.", value=0)
    s2 = sim.State(name="s.", value="green")
    s3 = sim.State(name="s.")

    q = sim.Queue("q.")

    x = X()

    Z1()

    Z2()
    Z3()
    env.run(10)


def trace_to_events(out):
    result = []
    for l in out.split("\n"):
        try:
            t = float(l[6:17])
            c = l[18:39].rstrip()
            result.append((t, c))
        except ValueError:
            pass
    return result


def test_urgent_and_priority(capsys):
    class X(sim.Component):
        def process(self):

            if self == x[8]:
                self.hold(0, priority=-6, urgent=True)
            if self == x[7]:
                self.hold(0, priority=-6)
            pass

    class Y(sim.Component):
        def process(self):
            pass

    env = sim.Environment(trace=True)
    x = [X(priority=-i) for i in range(10)]
    y = [Y(priority=-i, urgent=True) for i in range(10)]
    x[1].cancel()
    x[1].activate(priority=-8)
    env.run(till=0, priority=-5)
    for c in x:
        print(c.name(), c.scheduled_priority())
    out = capsys.readouterr()[0]    
    events = trace_to_events(out)
    assert [event[1] for event in events] == [
        "main",
        "y.9",
        "x.9",
        "y.8",
        "x.8",
        "x.1",
        "y.7",
        "x.7",
        "x.8",
        "y.6",
        "x.6",
        "x.7",
        "y.5",
        "x.5",
        "main",
    ]
    assert [c.scheduled_priority() for c in x] == [0, None, -2, -3, -4, None, None, None, None, None]
    with pytest.raises(TypeError):
        X(process="", priority=1)


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
