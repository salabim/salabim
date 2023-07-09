# Bank, 3 clerks (resources).py
import salabim as sim


class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        self.request(clerks)
        self.hold(30)
        self.release()  # not really required


env = sim.Environment(trace=False)
CustomerGenerator()
clerks = sim.Resource("clerks", capacity=3)

env.run(till=50000)

clerks.print_statistics()
clerks.print_info()