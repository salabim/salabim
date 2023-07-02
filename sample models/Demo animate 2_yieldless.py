# Demo animate 2.py
import salabim as sim
sim.yieldless(True)


class AnimateWaitSquare(sim.Animate):
    def __init__(self, i):
        self.i = i
        sim.Animate.__init__(
            self, rectangle0=(-12, -10, 12, 10), x0=300 - 30 * i, y0=100, fillcolor0="red", linewidth0=0
        )

    def visible(self, t):
        return q[self.i] is not None


class AnimateWaitText(sim.Animate):
    def __init__(self, i):
        self.i = i
        sim.Animate.__init__(self, text="", x0=300 - 30 * i, y0=100, textcolor0="white")

    def text(self, t):
        component_i = q[self.i]

        if component_i is None:
            return ""
        else:
            return component_i.name()


def do_animation():
    env.animate(True)
    for i in range(10):
        AnimateWaitSquare(i)
        AnimateWaitText(i)
    show_length = sim.Animate(text="", x0=330, y0=100, textcolor0="black", anchor="w")
    show_length.text = lambda t: "Length= " + str(len(q))


class Person(sim.Component):
    def process(self):
        self.enter(q)
        self.hold(15)
        self.leave(q)


env = sim.Environment(trace=True)

q = sim.Queue("q")
for i in range(15):
    Person(name="{:02d}".format(i), at=i)

do_animation()

env.run()