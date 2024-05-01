import salabim as sim
import pytest
import datetime

import collections

def test_environment():
    import dateutil.parser

    env=sim.Environment()
    env.run(1)
    assert env.now() == 1

    env=sim.Environment(datetime0=True)
    env.run(1)
    assert env.now() == 1
    assert env.time_to_str(env.now()) == "Thu 1970-01-01 00:00:01"    

    env=sim.Environment(datetime0="23-02-01")
    env.run(1)
    assert env.now() == 1
    assert env.time_to_str(env.now()) == "Wed 2023-02-01 00:00:01"   
     
    org_dateutil_parse=sim.Environment.dateutil_parse  
    sim.Environment.dateutil_parse = lambda self, spec: dateutil.parser.parse(spec, dayfirst=True, yearfirst=False) 
    env=sim.Environment(datetime0="01-02-23")
    env.run(1)
    assert env.now() == 1
    assert env.time_to_str(env.now()) == "Wed 2023-02-01 00:00:01"   

    sim.Environment.dateutil_parse = org_dateutil_parse 
    
def test_component0():
    import datetime
    class X(sim.Component):
        def process(self):
            assert env.now() == env.datetime_to_t(datetime.datetime(year=2023, month=1, day=15))
            self.hold(till="2023-02-01")
            self.hold("12:00:00")
            self.hold(datetime.timedelta(hours=12))
            assert env.now() == env.datetime_to_t(datetime.datetime(year=2023, month=2, day=2))
            self.hold(till="2023-03-01")
            assert env.now() == env.datetime_to_t(datetime.datetime(year=2023, month=3, day=1))
    env=sim.Environment(datetime0="23-01-01")
    X(at="2023-01-15")
    env.run()

def test_component1():
    class X(sim.Component):
        def process(self):
            assert env.now() == 1
            self.hold(till="20")
            self.hold("0.5")
            self.hold("0.5")
            assert env.now() == 21
            self.hold(till="30")
            assert env.now() == 30
    env=sim.Environment()
    X(at="1")
    env.run()

def test_component2():
    def sequence():
        sequence.n += 1
        return str(sequence.n)
    sequence.n=0

    class X(sim.Component):
        def process(self):
            assert env.now() == 1
            self.hold(sequence)
            assert env.now() == 2
            self.hold(sequence)
            assert env.now() == 4

    env=sim.Environment()
    with pytest.raises(ValueError):
        X(at="abc")
    X(at="1")
    env.run()

def test_no_dateutils():
    import sys
    for s in sys.modules.copy():
        if s.startswith("dateutil"):
            del sys.modules[s]

    import builtins
    orig_import = builtins.__import__

    def mock_import(*args, **kwargs):
        if args[0]=='dateutil.parser':
            raise ImportError(args[0])
        else:
            return orig_import(*args, **kwargs)

    builtins.__import__ = mock_import

    env=sim.Environment()

    with pytest.raises(ImportError):
        env=sim.Environment(datetime0="23-02-01")

    builtins.__import__ = orig_import


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
