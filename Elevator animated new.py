from __future__ import print_function  # compatibility with Python 2.x
from __future__ import division  # compatibility with Python 2.x

import salabim as sim
import random


class AnimateLED(sim.Animate):
    def __init__(self, x, y, floor, direction):
        self.floor = floor
        self.direction = direction

        b = xvisitor_dim / 2
        if direction == up:
            polygon = (-0.5 * b, 0, 0.5 * b, 0, 0, 1 * b)
        else:
            polygon = (-0.5 * b, b, 0.5 * b, b, 0, 0)

        sim.Animate.__init__(self, x0=x, y0=y, polygon0=polygon)

    def fillcolor(self, t):
        if (self.floor, self.direction) in requests:
            return direction_color(self.direction)
        else:
            return ''

def animation_pre_tick(self, t):
    for car in cars:
        if car.mode() == 'Move':
            y = sim.interpolate(
                t, car.mode_time(), car.scheduled_time(),
                car.floor.y, car.nextfloor.y)
        else:
            y = car.floor.y
        car.visitors.animate(x=xcar[car], y=y, direction='e')
        car.pic.update(y0=y)     

def do_animation():

    global xvisitor_dim
    global yvisitor_dim
    global xcar
    global capacity_last, ncars_last, topfloor_last
    
    sim.Environment.animation_pre_tick = animation_pre_tick

    xvisitor_dim = 30
    yvisitor_dim = xvisitor_dim
    yfloor0 = 20

    xcar = {}
    xled = {}

    x = env.width
    for car in cars:
        x -= (capacity + 1) * xvisitor_dim
        xcar[car] = x
    x -= xvisitor_dim
    xsign = x
    x -= xvisitor_dim / 2
    for direction in (up, down):
        x -= xvisitor_dim / 2
        xled[direction] = x
    x -= xvisitor_dim
    xwait = x

    for floor in floors.values():
        y = yfloor0 + floor.n * yvisitor_dim
        floor.y = y
        for direction in (up, down):
            if (direction == up and floor.n < topfloor) or (direction == down and floor.n > 0):
                AnimateLED(x=xled[direction], y=y + 6, floor=floor, direction=direction)
        sim.Animate(x0=0, y0=y, line0=(0, 0, xwait, 0), linecolor0='black')
        sim.Animate(x0=xsign, y0=y + yvisitor_dim / 2,
            text=str(floor.n), fontsize0=xvisitor_dim / 2, anchor='center')


        floor.visitors.animate(x=xwait-xvisitor_dim,y=floor.y,direction='w')
        
    for car in cars:
        x = xcar[car]
        car.pic=sim.Animate(x0=x,
           rectangle0=(0, 0, capacity * xvisitor_dim, yvisitor_dim), fillcolor0='lightblue')
        car.visitors.animate(x=xcar[car], y=600, direction='e')

    ncars_last = ncars
    sim.AnimateSlider(x=510, y=env.height, width=90, height=20,
        vmin=1, vmax=5, resolution=1, v=ncars, label='#elevators', action=set_ncars)

    topfloor_last = topfloor
    sim.AnimateSlider(x=610, y=env.height, width=90, height=20,
        vmin=5, vmax=20, resolution=1, v=topfloor, label='top floor', action=set_topfloor)

    capacity_last = capacity
    sim.AnimateSlider(x=710, y=env.height, width=90, height=20,
        vmin=2, vmax=6, resolution=1, v=capacity, label='capacity', action=set_capacity)

    sim.AnimateSlider(x=510, y=env.height - 50, width=90, height=25,
        vmin=0, vmax=400, resolution=25, v=load_0_n, label='Load 0->n', action=set_load_0_n)

    sim.AnimateSlider(x=610, y=env.height - 50, width=90, height=25,
        vmin=0, vmax=400, resolution=25, v=load_n_n, label='Load n->n', action=set_load_n_n)

    sim.AnimateSlider(x=710, y=env.height - 50, width=90, height=25,
        vmin=0, vmax=400, resolution=25, v=load_n_0, label='Load n->0', action=set_load_n_0)

    if make_video:
        env.animation_parameters(modelname='Elevator', speed=32, video='Elevator.mp4',
            show_speed=False, show_fps=False)
    else:
        env.animation_parameters(modelname='Elevator', speed=32)


def set_load_0_n(val):
    global load_0_n
    load_0_n = float(val)
    if vg_0_n.ispassive():
        vg_0_n.activate()


def set_load_n_n(val):
    global load_n_n
    load_n_n = float(val)
    if vg_n_n.ispassive():
        vg_n_n.activate()


def set_load_n_0(val):
    global load_n_0
    load_n_0 = float(val)
    if vg_n_0.ispassive():
        vg_n_0.activate()


def set_capacity(val):
    global capacity
    global capacity_last
    capacity = int(val)
    if capacity != capacity_last:
        capacity_last = capacity
        env.main().activate()


def set_ncars(val):
    global ncars
    global ncars_last
    ncars = int(val)
    if ncars != ncars_last:
        ncars_last = ncars
        env.main().activate()


def set_topfloor(val):
    global topfloor
    global topfloor_last
    topfloor = int(val)
    if topfloor != topfloor_last:
        topfloor_last = topfloor
        env.main().activate()


def direction_color(direction):
    if direction == 1:
        return 'red'
    if direction == -1:
        return 'green'
    return 'yellow'


class VisitorGenerator(sim.Component):
    def setup(self, from_, to, id):
        self.from_ = from_
        self.to = to
        self.id = id

    def process(self):
        while True:
            from_ = random.randint(self.from_[0], self.from_[1])
            while True:
                to = random.randint(self.to[0], self.to[1])
                if from_ != to:
                    break

            Visitor(from_=from_, to=to)
            if self.id == '0_n':
                load = load_0_n
            elif self.id == 'n_0':
                load = load_n_0
            else:
                load = load_n_n

            if load == 0:
                yield self.passivate()
            else:
                iat = 3600 / load
                r = random.uniform(0.5, 1.5)
                yield self.hold(r * iat)


class Visitor(sim.Component):
    def setup(self, from_, to):
        self.fromfloor = floors[from_]
        self.tofloor = floors[to]
        self.direction = getdirection(self.fromfloor, self.tofloor)
        
    def animation_objects(self, q):
        size_x = xvisitor_dim
        size_y = yvisitor_dim
        b = 0.1 * xvisitor_dim
        an1 = sim.Animate(rectangle0=(b, 2, xvisitor_dim - b, yvisitor_dim - b),
            linewidth0=0, fillcolor0=direction_color(self.direction))
        an2 = sim.Animate(text=str(self.tofloor.n), fontsize0=xvisitor_dim * 0.7,
            anchor='center', offsetx0=5 * b, offsety0=2 + 4 * b,
            textcolor0='white') 
        return size_x, size_y, an1, an2       
        
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
        self.visitors = sim.Queue(name='visitors in car')

    def process(self):
        dooropen = False
        self.floor = floors[0]
        self.direction = still
        dooropen = False
        while True:
            if self.direction == still:
                if not requests:
                    yield self.passivate(mode='Idle')
            if self.count_to_floor(self.floor) > 0:
                yield self.hold(dooropen_time, mode='Door open')
                dooropen = True
                for visitor in self.visitors:
                    if visitor.tofloor == self.floor:
                        visitor.leave(self.visitors)
                        visitor.activate()
                yield self.hold(exit_time, mode='Let exit')

            if self.direction == still:
                self.direction = up  # just random

            for self.direction in (self.direction, -self.direction):
                if (self.floor, self.direction) in requests:
                    del requests[self.floor, self.direction]

                    if not dooropen:
                        yield self.hold(dooropen_time, mode='Door open')
                        dooropen = True
                    for visitor in self.floor.visitors:
                        if visitor.direction == self.direction:
                            if len(self.visitors) < self.capacity:
                                visitor.leave(self.floor.visitors)
                                visitor.enter(self.visitors)
                        yield self.hold(enter_time, mode='Let in')
                    if (self.floor.count_in_direction(self.direction) > 0):
                        if not (self.floor, self.direction) in requests:
                            requests[self.floor,
                                     self.direction] = self.env.now()

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
                yield self.hold(doorclose_time, mode='Door close')
                dooropen = False

            if self.direction != still:
                self.nextfloor = floors[self.floor.n + self.direction]
                yield self.hold(move_time, mode='Move')
                self.floor = self.nextfloor

    def count_to_floor(self, tofloor):
        n = 0
        for visitor in self.visitors:
            if visitor.tofloor == tofloor:
                n += 1
        return n


class Floor():
    def __init__(self, n):
        self.n = n
        self.visitors = sim.Queue(name='visitors ' + str(n))

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

while True:
    env = sim.Environment()

    vg_0_n = VisitorGenerator(
        from_=(0, 0), to=(1, topfloor), id='0_n', name='vg_0_n')
    vg_n_0 = VisitorGenerator(
        from_=(1, topfloor), to=(0, 0), id='n_0', name='vg_n_0')
    vg_n_n = VisitorGenerator(
        from_=(1, topfloor), to=(1, topfloor), id='n_n', name='vg_n_n')

    requests = {}
    floors = {ifloor: Floor(ifloor) for ifloor in range(topfloor + 1)}

    cars = [Car(name='car ' + str(icar), capacity=capacity) for icar in range(ncars)]

    make_video = False

    do_animation()

    if make_video:
        env.run(1000)
        break
    else:
        env.run()
