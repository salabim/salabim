# Bank, 3 clerks (data components).py
import salabim as sim
sim.yieldless(False)



class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer().enter(waitingline)
            for clerk in clerks:
                if clerk.ispassive():
                    clerk.activate()
                    break  # activate only one clerk
            yield self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    pass


class Clerk(sim.Component):
    def process(self):
        while True:
            while len(waitingline) == 0:
                yield self.passivate()
            waitingline.pop()
            yield self.hold(30)


env = sim.Environment(trace=False)
CustomerGenerator()
clerks = [Clerk() for _ in range(3)]
waitingline = sim.Queue("waitingline")

env.run(till=50000)
waitingline.print_statistics()
