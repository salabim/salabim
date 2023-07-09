import salabim as sim
sim.yieldless(False)



class VisitorGenerator(sim.Component):
    def setup(self, from_, to, id, *args, **kwargs):
        self.from_ = from_
        self.to = to
        self.id = id

    def process(self):
        while True:
            from_ = sim.random.randint(self.from_[0], self.from_[1])
            while True:
                to = sim.random.randint(self.to[0], self.to[1])
                if from_ != to:
                    break

            Visitor(from_=from_, to=to)
            if self.id == "0_n":
                load = load_0_n
            elif self.id == "n_0":
                load = load_0_n
            else:
                load = load_n_n

            if load == 0:
                yield self.passivate()
            else:
                iat = 3600 / load
                r = sim.random.uniform(0.5, 1.5)
                yield self.hold(r * iat)


class Visitor(sim.Component):
    def setup(self, from_, to, *args, **kwargs):
        self.fromfloor = floors[from_]
        self.tofloor = floors[to]
        self.direction = getdirection(self.fromfloor, self.tofloor)

    def process(self):
        self.enter(self.fromfloor.visitors)
        if not (self.fromfloor, self.direction) in requests:
            requests[self.fromfloor, self.direction] = self.env.now()
        for car in cars:
            if car.ispassive():
                car.activate()

        yield self.passivate()


class Car(sim.Component):
    def setup(self, capacity):
        self.capacity = capacity
        self.direction = still
        self.floor = floors[0]
        self.visitors = sim.Queue(name="visitors in car")

    def process(self):
        dooropen = False
        self.floor = floors[0]
        self.direction = still
        dooropen = False
        while True:
            if self.direction == still:
                if not requests:
                    yield self.passivate(mode="Idle")
            if self.count_to_floor(self.floor) > 0:
                yield self.hold(dooropen_time, mode="Door open")
                dooropen = True
                for visitor in self.visitors:
                    if visitor.tofloor == self.floor:
                        visitor.leave(self.visitors)
                        visitor.activate()
                yield self.hold(exit_time, mode="Let exit")

            if self.direction == still:
                self.direction = up  # just random

            for self.direction in (self.direction, -self.direction):
                if (self.floor, self.direction) in requests:
                    del requests[self.floor, self.direction]

                    if not dooropen:
                        yield self.hold(dooropen_time, mode="Door open")
                        dooropen = True
                    for visitor in self.floor.visitors:
                        if visitor.direction == self.direction:
                            if len(self.visitors) < self.capacity:
                                visitor.leave(self.floor.visitors)
                                visitor.enter(self.visitors)
                        yield self.hold(enter_time, mode="Let in")
                    if self.floor.count_in_direction(self.direction) > 0:
                        if not (self.floor, self.direction) in requests:
                            requests[self.floor, self.direction] = self.env.now()

                if self.visitors:
                    break
            else:
                if requests:
                    earliest = sim.inf
                    for (floor, direction) in requests:
                        if requests[floor, direction] < earliest:
                            self.direction = getdirection(self.floor, floor)
                            earliest = requests[floor, direction]
                else:
                    self.direction = still
            if dooropen:
                yield self.hold(doorclose_time, mode="Door close")
                dooropen = False

            if self.direction != still:
                self.nextfloor = floors[self.floor.n + self.direction]
                yield self.hold(move_time, mode="Move")
                self.floor = self.nextfloor

    def count_to_floor(self, tofloor):
        n = 0
        for visitor in self.visitors:
            if visitor.tofloor == tofloor:
                n += 1
        return n


class Floor:
    def __init__(self, n):
        self.n = n
        self.visitors = sim.Queue(name="visitors " + str(n))

    def count_in_direction(self, dir):
        n = 0
        for visitor in self.visitors:
            if visitor.direction == dir:
                n += 1
        return n


def getdirection(fromfloor, tofloor):
    if fromfloor.n < tofloor.n:
        return +1
    if fromfloor.n > tofloor.n:
        return -1
    return 0


env = sim.Environment(random_seed=1234567)
up = 1
still = 0
down = -1

move_time = 10
dooropen_time = 3
doorclose_time = 3
enter_time = 3
exit_time = 3

load_0_n = 50
load_n_n = 100
load_n_0 = 100
capacity = 4
ncars = 3
topfloor = 15

VisitorGenerator(from_=(0, 0), to=(1, topfloor), id="0_n", name="vg_0_n")
VisitorGenerator(from_=(1, topfloor), to=(0, 0), id="n_0", name="vg_n_0")
VisitorGenerator(from_=(1, topfloor), to=(1, topfloor), id="n_n", name="vg_n_n")

requests = {}
floors = {ifloor: Floor(ifloor) for ifloor in range(topfloor + 1)}
cars = [Car(capacity=capacity) for icar in range(ncars)]

env.trace(True)
env.run(1000)
env.trace(False)
for floor in floors.values():
    floor.visitors.reset_monitors()
env.run(50000)

print("Floor    n         length length_of_stay")
for floor in floors.values():
    print(
        "{:5d}{:5d}{:15.3f}{:15.3f}".format(
            floor.n,
            floor.visitors.length_of_stay.number_of_entries(),
            floor.visitors.length.mean(),
            floor.visitors.length_of_stay.mean(),
        )
    )
