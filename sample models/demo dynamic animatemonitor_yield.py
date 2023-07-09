import salabim as sim
sim.yieldless(False)


class X(sim.Component):
    def process(self):
        v0 = v1 = 10
        while True:
            v0 = max(0, min(500, v0 + sim.Uniform(-1, 1)() * 10))
            level_monitor.tally(v0)
            v1 = max(0, min(500, v1 + sim.Uniform(-1, 1)() * 10))
            non_level_monitor.tally(v1)
            yield self.hold(1)

env = sim.Environment()
env.speed(10)

sim.AnimateText("Demonstration dynamic AnimateMonitor", fontsize=20, y=700,x=100)

level_monitor = sim.Monitor("level_monitor", level=True)
non_level_monitor = sim.Monitor("non_level_monitor")
X()
sim.AnimateMonitor(
    level_monitor,
    linewidth=3,
    x=100,
    y=100,
    width=900,
    height=250,
    vertical_scale=lambda arg, t: min(50, 250 / arg.monitor().maximum()),
    labels=lambda arg, t: [i for i in range(0, int(arg.monitor().maximum()), 10)],
    horizontal_scale=lambda t: min(10, 900 / t),
)
sim.AnimateMonitor(
    non_level_monitor,
    linewidth=5,
    x=100,
    y=400,
    width=900,
    height=250,
    vertical_scale=lambda arg, t: min(50, 250 / arg.monitor().maximum()),
    labels=lambda arg, t: [i for i in range(0, int(arg.monitor().maximum()), 10)],
    horizontal_scale=lambda t: min((10, 900 / t)),
)

env.video_repeat(0)
env.video("demo dynamic animatemonitor.gif")
env.run(1)
env.animate(True)
env.run(120)
env.video_close()
