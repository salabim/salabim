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
        for clerk in worktodo.waiters():
            if self.sequence_number() % 2:
                clerk.priority(
                    worktodo.waiters(), clerk.enter_time(worktodo.waiters())
                )  # even customers want longest waiting clerk
            else:
                clerk.priority(
                    worktodo.waiters(), -clerk.enter_time(worktodo.waiters())
                )  # odd customers want shortest waiting clerk

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


env = sim.Environment()
CustomerGenerator()
for _ in range(3):
    Clerk()
waitingline = sim.Queue("waitingline")
worktodo = sim.State("worktodo")

env.run(till=50000)
waitingline.print_histograms()
worktodo.print_histograms()
