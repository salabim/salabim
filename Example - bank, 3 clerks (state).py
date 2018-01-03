# Example - bank, 3 clerks (state).py
import salabim as sim


class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            yield self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        self.enter(waitingline)
        worktodo.trigger(max=1)
        yield self.passivate()


class Clerk(sim.Component):
    def process(self):
        while True:
            if len(waitingline) == 0:
                yield self.wait(worktodo)
            self.customer = waitingline.pop()
            yield self.hold(30)
            self.customer.activate()


env = sim.Environment(trace=False)
CustomerGenerator(name='customergenerator')
for i in range(3):
    Clerk()
waitingline = sim.Queue('waitingline')
worktodo = sim.State('worktodo')

env.run(till=50000)
waitingline.length.print_histogram(30, 0, 1)
print()
waitingline.length_of_stay.print_histogram(30, 0, 10)
