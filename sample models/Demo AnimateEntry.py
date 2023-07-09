import salabim as sim


def action():
    X(myname=y.entry.get())
    y.entry.remove()


class Y(sim.Component):
    def process(self):
        while True:

            self.entry = sim.AnimateEntry(x=100, y=100, value="abc", action=action)
            self.passivate()


class X(sim.Component):
    def process(self, myname):
        start = env.t
        an = sim.AnimateText("Hello " + myname, x=lambda t: (t - start) * 100, y=100)
        self.hold(10)
        an.remove()
        y.activate()


env = sim.Environment(trace=True)
env.animate(True)
y = Y()
env.run(100000)