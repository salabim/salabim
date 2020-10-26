import salabim as sim


class X(sim.Component):
    def setup(self):
        self.set_mode("abc")

    def process(self):
        yield self.hold(0)
        yield self.request(r, mode="def")
        yield self.hold(10.1, mode="ghi")
        self.release()
        yield self.passivate(mode="jkl")


class Interrupter(sim.Component):
    def process(self):
        yield self.hold(6)
        x0.interrupt()
        x1.interrupt()
        x2.interrupt()
        yield self.hold(4)
        x0.resume()
        x1.resume()
        x2.resume()


def status_map(status):
    return sim.statuses().index(status)


env = sim.Environment(trace=False)

modes = "abc def ghi jkl".split()

r = sim.Resource("r")
x0 = X(process="")
x1 = X(process="")
x2 = X(process="")
Interrupter()

sim.AnimateMonitor(
    monitor=x0.status,
    labels=sim.statuses(),
    x=100,
    y=10,
    linewidth=3,
    horizontal_scale=10,
    width=890,
    height=100,
    vertical_scale=12,
    vertical_map=status_map,
    vertical_offset=10,
)
sim.AnimateMonitor(
    monitor=x1.status,
    labels=sim.statuses(),
    x=100,
    y=210,
    linewidth=3,
    horizontal_scale=10,
    width=890,
    height=100,
    vertical_scale=12,
    vertical_map=status_map,
    vertical_offset=10,
)
sim.AnimateMonitor(
    monitor=x2.status,
    title="x2.status",
    titlecolor="red",
    labels=sim.statuses(),
    x=100,
    y=410,
    linewidth=3,
    linecolor="red",
    label_color="red",
    horizontal_scale=10,
    width=890,
    height=100,
    vertical_scale=12,
    vertical_map=status_map,
    vertical_offset=10,
)
sim.AnimateMonitor(
    monitor=x2.mode,
    title="                       x2.mode",
    labels=modes,
    label_offsetx=893,
    label_anchor="w",
    x=100,
    y=410,
    linewidth=3,
    borderlinewidth=0,
    titlecolor="blue",
    linecolor="blue",
    label_color="blue",
    horizontal_scale=10,
    width=890,
    height=100,
    vertical_scale=12,
    vertical_map=lambda x: 4 + modes.index(x),
    vertical_offset=10,
)

env.animate(True)
env.run(4.3)
x0.activate()
x1.activate()
x2.activate()

env.run(till=50)
