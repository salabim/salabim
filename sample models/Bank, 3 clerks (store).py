# Bank, 3 clerks (store).py
import salabim as sim


class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer().enter(waiting_room)
            self.hold(sim.Uniform(5, 15))


class Clerk(sim.Component):
    def process(self):
        while True:
            customer = self.from_store(waiting_room)
            self.hold(30)


class Customer(sim.Component):
    ...


env = sim.Environment(trace=False)
CustomerGenerator()
for _ in range(3):
    Clerk()
waiting_room = sim.Store("waiting_room")


env.run(till=50000)

waiting_room.print_statistics()
waiting_room.print_info()