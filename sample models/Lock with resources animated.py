import salabim as sim

left = -1
right = +1


def sidename(side):
    return "l" if side == left else "r"


def shortname(ship):
    s = ""
    for c in ship.name():
        if c != ".":
            s = s + c
    return s


def shipcolor(side):
    if side == left:
        return "blue"
    else:
        return "red"


def ship_polygon(ship):
    return (ship.side * (ship.length - 2), 0, ship.side * 3, 0, ship.side * 2, 3, ship.side * (ship.length - 2), 3)


def lock_water_rectangle(t):
    if lock.mode() == "Switch":
        y = sim.interpolate(t, lock.mode_time(), lock.scheduled_time(), ylevel[lock.side], ylevel[-lock.side])
    else:
        y = ylevel[lock.side]
    return (xdoor[left], -waterdepth, xdoor[right], y)


def lock_door_left_rectangle(t):
    if lock.mode() == "Switch" or lock.side == right:
        y = ylevel[right] + 2
    else:
        y = ylevel[left] - waterdepth
    return (xdoor[left] - 1, -waterdepth, xdoor[left] + 1, y)


def lock_door_right_rectangle(t):
    if lock.mode() == "Switch" or lock.side == left:
        y = ylevel[right] + 2
    else:
        y = ylevel[right] - waterdepth
    return (xdoor[right] - 1, -waterdepth, xdoor[right] + 1, y)


def animation_pre_tick(self, t):
    if lock.mode() == "Switch":
        y = sim.interpolate(t, lock.mode_time(), lock.scheduled_time(), ylevel[lock.side], ylevel[-lock.side])
    else:
        y = ylevel[lock.side]
    lockqueue.animate(x=xdoor[-lock.side], y=y, direction="w" if lock.side == left else "e")


def do_animation():
    global ylevel, xdoor, waterdepth
    lockheight = 5
    waterdepth = 2
    ylevel = {left: 0, right: lockheight}
    xdoor = {left: -0.5 * locklength, right: 0.5 * locklength}
    xbound = {left: -1.2 * locklength, right: 1.2 * locklength}

    sim.Environment.animation_pre_tick = animation_pre_tick
    env.animation_parameters(animate=True,
        x0=xbound[left], y0=-waterdepth, x1=xbound[right], modelname="Lock", speed=8, background_color="20%gray"
    )

    for side in [left, right]:
        wait[side].animate(x=xdoor[side], y=10 + ylevel[side], direction="n")

    sim.Animate(rectangle0=(xbound[left], ylevel[left] - waterdepth, xdoor[left], ylevel[left]), fillcolor0="aqua")
    sim.Animate(rectangle0=(xdoor[right], ylevel[right] - waterdepth, xbound[right], ylevel[right]), fillcolor0="aqua")
    a = sim.Animate(rectangle0=(0, 0, 0, 0), fillcolor0="aqua")
    a.rectangle = lock_water_rectangle
    a = sim.Animate(rectangle0=(0, 0, 0, 0))
    a.rectangle = lock_door_left_rectangle
    a = sim.Animate(rectangle0=(0, 0, 0, 0))
    a.rectangle = lock_door_right_rectangle

    a = sim.Animate(text="", x0=10, y0=650, screen_coordinates=True, fontsize0=15, font="narrow", anchor="w")
    a.text = lambda t: "mean waiting left : {:5.1f} (n={})".format(
        wait[left].length_of_stay.mean(), wait[left].length_of_stay.number_of_entries()
    )
    a = sim.Animate(text="", x0=10, y0=630, screen_coordinates=True, fontsize0=15, font="narrow", anchor="w")
    a.text = lambda t: "mean waiting right: {:5.1f} (n={})".format(
        wait[right].length_of_stay.mean(), wait[right].length_of_stay.number_of_entries()
    )
    a = sim.Animate(text="xx=12.34", x0=10, y0=610, screen_coordinates=True, fontsize0=15, font="narrow", anchor="w")
    a.text = lambda t: "  nr waiting left : {:3d}".format(wait[left].length())
    a = sim.Animate(text="xx=12.34", x0=10, y0=590, screen_coordinates=True, fontsize0=15, font="narrow", anchor="w")
    a.text = lambda t: "  nr waiting right: {:3d}".format(wait[right].length())

    sim.AnimateSlider(
        x=520,
        y=0,
        width=100,
        height=20,
        vmin=16,
        vmax=60,
        resolution=4,
        v=iat,
        label="iat",
        action=set_iat,
        xy_anchor="nw",
    )
    sim.AnimateSlider(
        x=660,
        y=0,
        width=100,
        height=20,
        vmin=10,
        vmax=60,
        resolution=5,
        v=meanlength,
        label="mean length",
        action=set_meanlength,
        xy_anchor="nw",
    )


def set_iat(val):
    global iat
    iat = float(val)


def set_meanlength(val):
    global meanlength
    meanlength = float(val)


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
    def animation_objects(self, q):
        size_x = self.length
        size_y = 5
        if self.side == left:
            anchor = "se"
        else:
            anchor = "sw"
        an1 = sim.Animate(polygon0=ship_polygon(self), fillcolor0=shipcolor(self.side), anchor=anchor, linewidth0=0)
        an2 = sim.Animate(
            text=shortname(self), textcolor0="white", anchor=anchor, fontsize0=2.4, offsetx0=self.side * 5, offsety0=0.7
        )
        return (size_x, size_y, an1, an2)

    def process(self):
        self.enter(wait[self.side])
        if lock.ispassive():
            lock.activate()
        self.request((lockmeters[self.side], self.length), key_in[self.side])
        self.leave(wait[self.side])
        self.enter(lockqueue)
        self.hold(intime)
        self.release(key_in[self.side])
        self.request(key_out)
        self.leave(lockqueue)
        self.hold(outtime)
        self.release(key_out)


class Lock(sim.Component):
    def process(self):
        self.request(key_in[left])
        self.request(key_in[right])
        self.request(key_out)

        while True:
            if len(key_in[self.side].requesters()) == 0:
                if len(key_in[-self.side].requesters()) == 0:
                    self.passivate()
            self.release(key_in[self.side])
            self.request((key_in[self.side], 1, 1000))
            lockmeters[self.side].release()
            self.hold(switchtime, mode="Switch")
            self.side = -self.side
            self.release(key_out)
            self.request((key_out, 1, 1000), mode=None)


env = sim.Environment()

locklength = 60
switchtime = 10
intime = 2
outtime = 2
meanlength = 30
iat = 30

lockmeters = {}
key_in = {}
wait = {}
lockqueue = sim.Queue("lockqueue")
key_out = sim.Resource(name=" key_out")

for side in (left, right):
    wait[side] = sim.Queue(name=sidename(side) + "Wait")
    lockmeters[side] = sim.Resource(capacity=locklength, name=sidename(side) + " lock meters", anonymous=True)
    key_in[side] = sim.Resource(name=sidename(side) + " key in")
    shipgenerator = Shipgenerator(name=sidename(side) + "Shipgenerator")
    shipgenerator.side = side

lock = Lock(name="lock")
lock.side = left

do_animation()
env.run()