import salabim as sim
import pytest


def test_define():
    env = sim.Environment()
    class X(sim.Component):
        def process(self):
            with pytest.raises(ValueError):
                self.from_store(())

    store0 = sim.Store("store")
    X()
    env.run()

if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
