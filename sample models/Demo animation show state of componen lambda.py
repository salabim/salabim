import salabim as sim


def fillcolor(component, t):
    if component.status == 0:
        return "red"
    if component.status == 1:
        return "green"
    if component.status == 2:
        return "blue"


class Machine(sim.Component):
    def fillcolor(self, t):
        if self.status == 0:
            return "red"
        if self.status == 1:
            return "green"
        if self.status == 2:
            return "blue"

    def setup(self, x):
        sim.AnimateRectangle(spec=(0, 0, 75, 75), fillcolor=fillcolor, arg=self, x=x, y=100)
        sim.AnimateRectangle(
            spec=(0, 0, 75, 75), fillcolor=lambda arg, t: ("red", "green", "blue")[arg.status], arg=self, x=x, y=200
        )
        sim.AnimateRectangle(spec=(0, 0, 75, 75), fillcolor=self.fillcolor, arg=self, x=x, y=300)
        self.rectangle = sim.AnimateRectangle(spec=(0, 0, 75, 75), x=x, y=400)

    def process(self):
        while True:
            self.status = sim.IntUniform(0, 2)()
            if self.status == 0:
                self.rectangle.fillcolor = "red"
            if self.status == 1:
                self.rectangle.fillcolor = "green"
            if self.status == 2:
                self.rectangle.fillcolor = "blue"
            self.hold(sim.Uniform(1, 2)())


sim.reset()
env = sim.Environment()
Machine(x=100)
Machine(x=200)
Machine(x=300)
env.animate(True)

env.run()