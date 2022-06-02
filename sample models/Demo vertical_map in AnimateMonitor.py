import salabim as sim
import math


class X(sim.Component):
    def setup(self):
        self.set_mode("four")

    def process(self):
        yield self.hold(5)
        yield self.request(r, mode="one")
        yield self.hold(10.1, mode="two")
        self.release()
        yield self.passivate(mode="three")


class Interrupter(sim.Component):
    def process(self):
        yield self.hold(6)
        for x in xs:
            x.interrupt()
        yield self.hold(4)
        for x in xs:
            x.resume()


def status_map(status):
    return sim.statuses().index(status)


class Sampler(sim.Component):
    def process(self):
        while True:
            sample = sim.Map(sim.Uniform(0, 10), math.exp)()
            m_log.tally(sample)
            yield self.hold(1)


env = sim.Environment(trace=False)

modes = "one two three four".split()

r = sim.Resource("r")
xs = [X(process="") for _ in range(3)]

m_log = sim.Monitor("m_log", level=True)
sim.AnimateMonitor(
    m_log,
    labels=[1, 10, 100, 1000, 10000, 100000],
    vertical_map=math.log,
    x=100,
    y=550,
    vertical_scale=10,
    horizontal_scale=30,
    linewidth=3,
    linecolor="green",
    width=890,
    height=120,
)
for x in xs:
    sim.AnimateMonitor(
        monitor=x.status,
        title=f"{x.name()}.status",
        titlecolor="red",
        labels=sim.statuses(),
        x=100,
        y=100 + 150 * x.sequence_number(),
        linewidth=3,
        linecolor="red",
        label_color="red",
        horizontal_scale=30,
        width=890,
        height=100,
        vertical_scale=12,
        vertical_map=status_map,
        vertical_offset=10,
    )
    sim.AnimateMonitor(
        monitor=x.mode,
        title=f"                       {x.name()}.mode",
        labels=modes,
        label_offsetx=893,
        label_anchor="w",
        x=100,
        y=100 + 150 * x.sequence_number(),
        linewidth=3,
        borderlinewidth=0,
        titlecolor="blue",
        linecolor="blue",
        label_color="blue",
        horizontal_scale=30,
        width=890,
        height=100,
        vertical_scale=12,
        vertical_map=lambda x: modes.index(x),
        vertical_offset=10,
    )

env.animate(True)
env.speed(10)
Sampler()

env.run(5)
Interrupter()

for x in xs:
    x.activate()

env.run(till=50)
