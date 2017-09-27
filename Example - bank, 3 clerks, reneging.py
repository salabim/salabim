# Example - bank, 3 clerks, reneging.py
import salabim as sim


class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            yield self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        if len(waitingline) >= 5:
            env.number_balked += 1
            env.print_trace('', '', 'balked')
            yield self.cancel()
        self.enter(waitingline)
        for clerk in clerks:
            if clerk.ispassive():
                clerk.activate()
                break  # activate only one clerk
        yield self.hold(50)  # if not serviced within this time, renege
        if self in waitingline:
            self.leave(waitingline)
            env.number_reneged += 1
            env.print_trace('', '', 'reneged')
        else:
            yield self.passivate()  # wait for service to be completed


class Clerk(sim.Component):
    def process(self):
        while True:
            while len(waitingline) == 0:
                yield self.passivate()
            self.customer = waitingline.pop()
            self.customer.activate()
            yield self.hold(30)
            self.customer.activate()


env = sim.Environment(trace=False)
CustomerGenerator()
env.number_balked = 0
env.number_reneged = 0
clerks = sim.Queue('clerks')
for i in range(3):
    Clerk().enter(clerks)

waitingline = sim.Queue('waitingline')
waitingline.length.monitor(False)
env.run(duration=1500)
waitingline.length.monitor(True)
env.run(duration=1500)
waitingline.length.print_histogram(30, 0, 1)
print()
waitingline.length_of_stay.print_histogram(30, 0, 10)
print('number reneged', env.number_reneged)
print('number balked', env.number_balked)
import matplotlib.pyplot as plt
plt.plot(*waitingline.length.tx(exoff=True), 'bo')
plt.ylabel('length of ' + waitingline.name())
plt.show()
