# Example - bank, 3 clerks (state).py
import salabim as sim
sim.yieldless(False)



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
    def setup(self, product):
        self.product = product

    def process(self):
        while True:
            if len(waitingline) == 0:
                yield self.wait((worktodo, True, self.product))
            self.customer = waitingline.pop()
            yield self.hold(30)
            self.customer.activate()


env = sim.Environment()
CustomerGenerator()
for product in ("B", "A", "C"):
    Clerk(name=product, product=product)
waitingline = sim.Queue("waitingline")
worktodo = sim.State("worktodo")

env.run(till=50000)
waitingline.print_histograms()
worktodo.print_histograms()
