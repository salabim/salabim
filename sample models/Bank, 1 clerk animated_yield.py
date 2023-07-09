# Bank, 1 clerk.py
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
        if clerk.ispassive():
            clerk.activate()
        yield self.passivate()


class Clerk(sim.Component):
    def process(self):
        while True:
            while len(waitingline) == 0:
                yield self.passivate()
            self.customer = waitingline.pop()
            self.customer.enter(in_service)
            yield self.hold(sim.Exponential(10).sample())
            self.customer.leave(in_service)
            self.customer.activate()


sim.reset()
env = sim.Environment(trace=False)

CustomerGenerator()
clerk = Clerk()
waitingline = sim.Queue("waitingline")
in_service = sim.Queue("in_service")
sim.AnimateQueue(waitingline, x=700, y=100)
sim.AnimateQueue(in_service, x=1000, y=100)
sim.AnimateMonitor(waitingline.length, x=20, y=200, width=1000)
sim.AnimateMonitor(in_service.length, x=20, y=400, width=1000)
env.animate(True)
env.speed(50)  # one second in wall time is 50 time units in the animation
env.run(till=2000)
