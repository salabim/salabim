from salabim import *


class CustomerGenerator(Component):
    def process(self):
        while True:
            Customer()
            self.hold(Uniform(5, 15).sample())


class Customer(Component):
    def process(self):
        self.enter(waitingline)
        for clerk in clerks:
            if clerk.ispassive():
                clerk.activate()
        self.passivate()


class Clerk(Component):
    def process(self):
        while True:
            while len(waitingline) == 0:
                self.passivate()
            customer = waitingline.pop()
            self.hold(30)
            customer.activate()


env = Environment()
CustomerGenerator()
clerks = [Clerk() for _ in range(3)]
waitingline = Queue("waitingline")
env.run(till=50000)
waitingline.print_histograms()