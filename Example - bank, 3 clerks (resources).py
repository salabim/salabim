#Example - bank, 3 clerks (resources).py
import salabim as sim

class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            yield self.hold(sim.Uniform(5,15).sample())
        
class Customer(sim.Component):
    def process(self):
        yield self.request(clerks)
        yield self.hold(30)
        self.release()
        
de=sim.Environment(random_seed=1234567,trace=False)
CustomerGenerator()
clerks=sim.Resource('clerk',3)

de.run(till=50000)
clerks.requesters().print_statistics()
