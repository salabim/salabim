import salabim as sim
import pytest

class X(sim.Component):
    def setup(self, color='red'):
        self.color = color
        self.enter(components)
        
class Vehicle(sim.Component):
    def setup(self):
        self.enter(components)
    
class Car(Vehicle):
    pass
    
class Bus(Vehicle):
    pass
    
class Truck(Vehicle):
    pass
        
def exp(X, run_time=None, *args, **kwargs):
    global components

    env = sim.Environment()
    components = sim.Queue()
    sim.ComponentGenerator(X, *args, **kwargs)
    env.run(run_time)
    return components    
        
                
        
def test_iat():
    components = exp(X, iat=sim.Uniform(0, 2), at=500, till=1000, force_at=True)
    assert len(components) == pytest.approx(500, rel=1e-2)
    assert components[0].enter_time(components) == 500
    assert 998 <= components[-1].enter_time(components) <= 1000
    
    with pytest.raises(ValueError):
        components = exp(X, iat=sim.Uniform(0, 2), at=500, till=1000, force_at=True, force_till=True)
 
    components = exp(X, iat=sim.Uniform(0, 2), till=1000, force_at=True)
    assert len(components) == pytest.approx(1000, rel=1e-2)
    assert components[-1].enter_time(components) <= 1000
    
    components = exp(X, iat=20,at=10, till=111,force_at=True)
    assert len(components) == 6
    assert components[0].enter_time(components) == 10
    assert components[-1].enter_time(components) == 110
    
    components = exp(X, iat=20,at=10, till=111)
    assert len(components) == 5
    assert components[-1].enter_time(components) == 110  
    
    components = exp(X, iat=20,at=10,number=5,force_at=True)
    assert len(components) == 5
    assert components[0].enter_time(components) == 10
    assert components[-1].enter_time(components) == 90
        
    components = exp(X, iat=20,at=10,number=5)
    assert len(components) == 5
    assert components[0].enter_time(components) == 30
    assert components[-1].enter_time(components) == 110
    
    components = exp(X, run_time=110, iat=20, at=10)
    assert len(components) == 4
    assert components[0].enter_time(components) == 30
    assert components[-1].enter_time(components) == 90 
    
def test_spread():
    
    components = exp(X, at=100, till=200, number=10)
    assert len(components) == 10
    assert components[0].enter_time(components) > 100
    assert components[-1].enter_time(components) < 200
    
    components = exp(X, at=100, till=200, number=10, force_at=True)
    assert len(components) == 10
    assert components[0].enter_time(components) == 100
    assert components[-1].enter_time(components) < 200
    
    components = exp(X, at=100, till=200, number=10, force_till=True)
    assert len(components) == 10
    assert components[0].enter_time(components) > 100
    assert components[-1].enter_time(components) == 200
    
    components = exp(X, at=100, till=200, number=10, force_at=True, force_till=True)
    assert len(components) == 10
    assert components[0].enter_time(components) ==100
    assert components[-1].enter_time(components) == 200
                
    components = exp(X, at=100, till=200, number=1, force_till=True)
    assert len(components) == 1
    assert components[0].enter_time(components) == 200
        
    components = exp(X, at=100, till=200, number=1, force_at=True)
    assert len(components) == 1
    assert components[0].enter_time(components) == 100
    
    with pytest.raises(ValueError):
        components = exp(X, at=100, till=200, number=1, force_at=True, force_till=True)

    components = exp(X, at=100, till=200, number=0, force_till=True)
    assert len(components) == 0
    
def test_propagate():
    components = exp(X, number=1, iat=1)
    assert components[0].color == 'red'
    assert components[0].name() == 'x.0'

    components = exp(X, number=1, iat=1, color='blue', name='my name,')
    assert components[0].color == 'blue'      
    assert components[0].name() == 'my name.1'
                     
                 
def test_dis():
    components = exp(sim.Pdf((Car, Bus, Truck), (50, 30, 20)), iat=1, number=1000)

    names = sim.Monitor()
    for component in components:
        names.tally(component.name().split('.')[0])
#    names.print_histogram(values=True, sort_on_weight=True)
            
if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
