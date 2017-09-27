# Example - bank, 3 clerks (resources).py
import salabim as sim


class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            yield self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        yield self.request(clerks)
        yield self.hold(30)
        self.release()


env = sim.Environment(trace=False)
CustomerGenerator()
clerks = sim.Resource('clerk', 3)

env.run(till=50000)

clerks.requesters().length.print_histogram(30, 0, 1)
print()
clerks.requesters().length_of_stay.print_histogram(30, 0, 10)

clerks.print_statistics()
clerks.print_info()
print(clerks.claimed_quantity())

