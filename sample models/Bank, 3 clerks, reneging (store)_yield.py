# Bank, 3 clerks (store, reneging).py
import salabim as sim
sim.yieldless(False)



class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            customer = Customer()
            yield self.to_store(waiting_room, customer, fail_at=env.now())
            if self.failed():
                customer.cancel()
                env.number_balked += 1
                print(env.now(), "balked",customer.name())
                env.print_trace("", "", "balked",customer.name())
            yield self.hold(sim.Uniform(5, 15))


class Clerk(sim.Component):
    def process(self):
        while True:
            customer = yield self.from_store(waiting_room)
            yield self.hold(30)


class Customer(sim.Component):
    def process(self):
        yield self.hold(50)
        if self in waiting_room:
            self.leave(waiting_room)
            env.number_reneged += 1
            env.print_trace("", "", "reneged")

env = sim.Environment(trace=False)
env.number_balked = 0
env.number_reneged = 0
CustomerGenerator()
for _ in range(3):
    Clerk()
waiting_room = sim.Store("waiting_room", capacity=5)

env.run(till=30000)

waiting_room.length.print_histogram(30, 0, 1)
waiting_room.length_of_stay.print_histogram(30, 0, 10)
print("number reneged", env.number_reneged)
print("number balked", env.number_balked)