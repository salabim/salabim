# Example - bank, 3 clerks (standby).py
import salabim as sim


class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        self.enter(waitingline)
        self.passivate()


class Clerk(sim.Component):
    def process(self):
        while True:
            while len(waitingline) == 0:
                self.standby()
            self.customer = waitingline.pop()
            self.hold(30)
            self.customer.activate()


env = sim.Environment(trace=True)
CustomerGenerator()
for _ in range(3):
    Clerk()
waitingline = sim.Queue("waitingline")

env.run(till=50000)
waitingline.length.print_histogram(30, 0, 1)
print()
waitingline.length_of_stay.print_histogram(30, 0, 10)