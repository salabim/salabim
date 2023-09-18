import salabim as sim

left = -1
right = +1


def sidename(side):
    return "l" if side == left else "r"


def shipcolor(side):
    return "blue" if side == left else "red"


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


def do_animation():
    global ylevel, xdoor, waterdepth

    lockheight = 5
    waterdepth = 2
    ylevel = {left: 0, right: lockheight}
    xdoor = {left: -0.5 * locklength, right: 0.5 * locklength}
    xbound = {left: -1.2 * locklength, right: 1.2 * locklength}

    env.animation_parameters(animate=True, x0=xbound[left], y0=-waterdepth, x1=xbound[right], modelname="Lock", speed=8, background_color="20%gray")

    for side in [left, right]:
        sim.AnimateQueue(queue=wait[side], x=xdoor[side], y=10 + ylevel[side], direction="n", title="", screen_coordinates=False)

    sim.AnimateRectangle(spec=(xbound[left], ylevel[left] - waterdepth, xdoor[left], ylevel[left]), fillcolor="aqua")
    sim.AnimateRectangle(spec=(xdoor[right], ylevel[right] - waterdepth, xbound[right], ylevel[right]), fillcolor="aqua")
    sim.AnimateRectangle(spec=lock_water_rectangle, fillcolor="aqua")
    sim.AnimateRectangle(spec=lock_door_left_rectangle)
    sim.AnimateRectangle(spec=lock_door_right_rectangle)

    sim.AnimateSlider(x=520, y=0, width=100, height=20, vmin=16, vmax=60, resolution=4, v=iat, label="iat", action=set_iat, xy_anchor="nw")
    sim.AnimateSlider(
        x=660, y=0, width=100, height=20, vmin=10, vmax=60, resolution=5, v=meanlength, label="mean length", action=set_meanlength, xy_anchor="nw"
    )
    sim.AnimateMonitor(
        wait[left].length,
        linecolor="orange",
        fillcolor="",
        x=512 - 225,
        y=768 - 200,
        horizontal_scale=1,
        width=450,
        linewidth=2,
        labels=[5, 10, 15],
        label_linecolor="40% gray",
        title=lambda: "Number of waiting ships left. Mean={:10.2f}".format(wait[left].length.mean()),
        screen_coordinates=True,
    )
    sim.AnimateMonitor(
        wait[right].length,
        linecolor="orange",
        fillcolor="",
        x=512 - 225,
        y=768 - 300,
        horizontal_scale=1,
        width=450,
        linewidth=2,
        labels=[5, 10, 15],
        label_linecolor="40% gray",
        title=lambda: "Number of waiting ships right. Mean={:10.2f}".format(wait[right].length.mean()),
    )
    sim.AnimateMonitor(
        wait[left].length_of_stay,
        linecolor="white",
        fillcolor="",
        x=512 - 225,
        y=768 - 400,
        vertical_scale=0.5,
        horizontal_scale=1,
        width=450,
        height=75,
        linewidth=4,
        labels=[50, 100, 150],
        label_linecolor="40% gray",
        title=lambda: "Waiting time of ships left. Mean={:10.2f}".format(wait[left].length_of_stay.mean()),
    )
    sim.AnimateMonitor(
        wait[right].length_of_stay,
        linecolor="white",
        fillcolor="",
        x=512 - 225,
        y=768 - 500,
        vertical_scale=0.5,
        horizontal_scale=1,
        width=450,
        height=75,
        linewidth=4,
        labels=[50, 100, 150],
        label_linecolor="40% gray",
        title=lambda: "Waiting time of ships left. Mean={:10.2f}".format(wait[right].length_of_stay.mean()),
    )

    sim.AnimateQueue(queue=lockqueue, x=lambda: xdoor[-lock.sideq], y=lock_y, direction=lambda: "w" if lock.sideq == left else "e", title="")


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
        an0 = sim.AnimatePolygon(
            spec=ship_polygon(self),
            fillcolor=shipcolor(self.side),
            linewidth=0,
            text=" " + self.name(),
            textcolor="white",
            layer=1,
            fontsize=2.6,
            text_anchor=("e" if self.side == left else "w"),
        )
        return (size_x, size_y, an0)

    def process(self):
        self.enter(wait[self.side])
        self.passivate(mode="Wait")
        self.hold(intime, mode="Sail in")
        self.leave(wait[self.side])
        self.enter(lockqueue)
        lock.activate()
        self.passivate(mode="In lock")
        self.leave(lockqueue)
        self.hold(outtime, mode="Sail out")
        lock.activate()


def lock_y(t):
    if lock.mode() == "Switch":
        y = sim.interpolate(t, lock.mode_time(), lock.scheduled_time(), ylevel[lock.side], ylevel[-lock.side])
    else:
        y = ylevel[lock.side]
    return y


class Lock(sim.Component):
    def process(self):
        while True:
            if len(wait[left]) + len(wait[right]) == 0:
                self.passivate(mode="Idle")

            usedlength = 0

            for ship in wait[self.side]:
                if usedlength + ship.length <= locklength:
                    usedlength += ship.length
                    ship.activate()
                    self.passivate("Wait for sail in")

            self.hold(switchtime, mode="Switch")
            self.side = -self.side
            for ship in lockqueue:
                ship.activate()
                self.passivate("Wait for sail out")
            self.sideq = -self.sideq


env = sim.Environment()

locklength = 60
switchtime = 10
intime = 2
outtime = 2
meanlength = 30
iat = 20

lockqueue = sim.Queue("lockqueue")

wait = {}

for side in (left, right):
    wait[side] = sim.Queue(name=sidename(side) + "Wait")
    shipgenerator = Shipgenerator(name=sidename(side) + "Shipgenerator")
    shipgenerator.side = side

lock = Lock(name="lock")
lock.side = left
lock.sideq = left
env.show_fps(True)
do_animation()
env.run()
