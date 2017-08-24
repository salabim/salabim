# Example - bank, 3 clerks.py
import salabim as sim


class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            yield self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        self.enter(waitingline)
        yield self.passivate()


class Clerk(sim.Component):
    def process(self):
        while True:
            while len(waitingline) == 0:
                yield self.standby()
            self.customer = waitingline.pop()
            yield self.hold(30)
            self.customer.activate()


de = sim.Environment(random_seed=1234567, trace=False)
CustomerGenerator()
clerks = sim.Queue('clerks')
for i in range(3):
    Clerk().enter(clerks)
waitingline = sim.Queue('waitingline')

de.run(till=50000)
waitingline.length.print_histogram(30, 0, 1)
print()
waitingline.length_of_stay.print_histogram(30, 0, 10)
