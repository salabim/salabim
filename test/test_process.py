import salabim as sim
import pytest


def test_1(capsys):
    class X(sim.Component):
        def process(self):
            self.env.order.append(self)

    env = sim.Environment(trace=True)
    env.order = []
    x = [X(name="x.", process="") for _ in range(10)]
    x[0].activate()
    x[1].activate(at=10)
    x[2].activate(at=10, urgent=True)
    x[3].activate(delay=10)
    x[4].activate(at=10, urgent=True)
    x[5].activate(at=10)
    env.run()
    assert env.order == [x[0], x[4], x[2], x[1], x[3], x[5]]
    out, err = capsys.readouterr()
    assert "no events left" in out


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
