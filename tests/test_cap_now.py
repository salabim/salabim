import salabim as sim
import pytest

def test():
    class X(sim.Component):
        def process(self):
            with pytest.raises(ValueError):
                yield self.hold(-1)
            assert env.now() == 0
            yield self.hold(-1, cap_now=True)
            assert env.now() == 0

    class Y(sim.Component):
        def process(self):
            now = env.now()
            yield self.hold(-1)
            assert env.now() == now

    env = sim.Environment(yieldless=False)    
    X()
    
    env.run(-1, cap_now=True)
    with sim.cap_now():
        Y()
        env.run(1)
            
if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
