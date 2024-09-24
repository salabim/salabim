# Example - bank, 3 clerks, reneging.py
import salabim as sim


class Customer(sim.Component):
    def process(self):
        if len(waitingline) >= 5:
            env.number_balked += 1
            env.print_trace("", "", "balked")
            print(env.now(), "balked", self.name())
            self.cancel()
        self.enter(waitingline)
        for clerk in clerks:
            if clerk.ispassive():
                clerk.activate()
                break  # activate only one clerk
        event = sim.Event(action=lambda: self.activate(), delay=50)
        self.passivate()  # if not serviced within this time, renege
        event.cancel()  # cancel also if action is already taken

        if self in waitingline:
            self.leave(waitingline)
            env.number_reneged += 1
            env.print_trace("", "", "reneged")
        else:
            self.passivate()  # wait for service to be completed


class Clerk(sim.Component):
    def process(self):
        while True:
            while len(waitingline) == 0:
                self.passivate()
            self.customer = waitingline.pop()
            self.customer.activate()  # get the customer out of it's passivate()
            self.hold(30)
            self.customer.activate()  # signal the customer that's all's done


env = sim.Environment()
sim.ComponentGenerator(Customer, iat=sim.Uniform(5, 15))
env.number_balked = 0
env.number_reneged = 0
clerks = [Clerk() for _ in range(3)]

waitingline = sim.Queue("waitingline")
env.run(duration=300000)
waitingline.length.print_histogram(30, 0, 1)
waitingline.length_of_stay.print_histogram(30, 0, 10)
print("number reneged", env.number_reneged)
print("number balked", env.number_balked)
