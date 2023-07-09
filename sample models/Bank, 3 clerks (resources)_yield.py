# Bank, 3 clerks (resources).py
import salabim as sim
sim.yieldless(False)



class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            yield self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        yield self.request(clerks)
        yield self.hold(30)
        self.release()  # not really required


env = sim.Environment(trace=False)
CustomerGenerator()
clerks = sim.Resource("clerks", capacity=3)

env.run(till=50000)

clerks.print_statistics()
clerks.print_info()
