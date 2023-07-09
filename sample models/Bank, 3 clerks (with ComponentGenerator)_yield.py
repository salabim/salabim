# Bank, 3 clerks (with ComponentGenerator).py
import salabim as sim
sim.yieldless(False)



class Customer(sim.Component):
    def process(self):
        self.enter(waitingline)
        for clerk in clerks:
            if clerk.ispassive():
                clerk.activate()
                break  # activate at most one clerk
        yield self.passivate()


class Clerk(sim.Component):
    def process(self):
        while True:
            while len(waitingline) == 0:
                yield self.passivate()
            self.customer = waitingline.pop()
            yield self.hold(30)
            self.customer.activate()


env = sim.Environment(trace=True)
env.ComponentGenerator(Customer, iat=env.Uniform(5, 15), force_at=True)
clerks = [Clerk() for _ in range(3)]

waitingline = env.Queue("waitingline")

env.run(till=50000)
waitingline.print_histograms()

waitingline.print_info()
