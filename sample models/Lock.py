import salabim as sim

left = -1
right = +1


def sidename(side):
    return "l" if side == left else "r"


class Shipgenerator(sim.Component):
    def process(self):
        while True:
            self.hold(sim.Exponential(iat).sample())
            ship = Ship(name=sidename(self.side) + "ship.")
            ship.side = self.side
            ship.length = meanlength * sim.Uniform(2.0 / 3, 4.0 / 3).sample()
            if lock.mode() == "Idle":
                lock.activate()


class Ship(sim.Component):
    def process(self):
        self.arrivaltime = env.now()
        self.enter(wait[self.side])
        self.passivate(mode="Wait")
        self.hold(intime, mode="Sail in")
        self.leave(wait[self.side])
        self.enter(lockqueue)
        lock.activate()
        self.passivate(mode="In lock")
        self.hold(outtime, mode="Sail out")
        self.leave(lockqueue)
        lock.activate()
        lock.monitor_time_in_complex.tally(env.now() - self.arrivaltime)


class Lock(sim.Component):
    def setup(self):
        self.usedlength = 0
        self.side = left
        self.monitor_usedlength = sim.Monitor(level=True, name="used length")
        self.monitor_time_in_complex = sim.Monitor(name="time in complex")

    def get_usedlength(self):
        return self.usedlength

    def process(self):
        while True:
            if len(wait[left]) + len(wait[right]) == 0:
                self.passivate(mode="Idle")
            for ship in wait[self.side]:
                if self.usedlength + ship.length <= locklength:
                    self.usedlength += ship.length
                    self.monitor_usedlength.tally(self.usedlength)
                    ship.activate()
                    self.passivate("Wait for sail in")
            self.hold(switchtime, mode="Switch")
            self.side = -self.side
            for ship in lockqueue:
                ship.activate()
                self.passivate("Wait for sail out")
                # avoid rounding errors
                self.usedlength = max(self.usedlength - ship.length, 0)
                self.monitor_usedlength.tally(self.usedlength)


env = sim.Environment(trace=False)
locklength = 60
switchtime = 10
intime = 2
outtime = 2
meanlength = 30
iat = 30

lockqueue = sim.Queue("lockqueue")

shipcounter = 0
wait = {}

for side in (left, right):
    wait[side] = sim.Queue(name=sidename(side) + "Wait")
    shipgenerator = Shipgenerator(name=sidename(side) + "Shipgenerator")
    shipgenerator.side = side

lock = Lock(name="lock")

env.run(50000)

lockqueue.length.print_histogram(5, 0, 1)
lockqueue.length_of_stay.print_histogram(10, 10, 1)
for side in (left, right):
    wait[side].length.print_histogram(30, 0, 1)
    wait[side].length_of_stay.print_histogram(30, 0, 10)
lock.monitor_usedlength.print_histogram(20, 0, 5)
lock.monitor_time_in_complex.print_histogram(30, 0, 10)