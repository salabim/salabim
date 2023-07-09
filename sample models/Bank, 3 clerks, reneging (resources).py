# Example - bank, 3 clerks, reneging (resources).py
import salabim as sim


class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        if len(clerks.requesters()) >= 5:
            env.number_balked += 1
            env.print_trace("", "", "balked")
            self.cancel()
        self.request(clerks, fail_delay=50)
        if self.failed():
            env.number_reneged += 1
            env.print_trace("", "", "reneged")
        else:
            self.hold(30)
            self.release()


env = sim.Environment()
CustomerGenerator()
env.number_balked = 0
env.number_reneged = 0
clerks = sim.Resource("clerks", 3)

env.run(till=50000)

clerks.requesters().length.print_histogram(30, 0, 1)
print()
clerks.requesters().length_of_stay.print_histogram(30, 0, 10)
print("number reneged", env.number_reneged)
print("number balked", env.number_balked)