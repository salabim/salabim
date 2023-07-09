import salabim as sim


class AnimateRectangle(sim.Animate):
    def __init__(self, component, *args, **kwargs):
        self.component = component
        super().__init__(*args, **kwargs)

    def fillcolor(self, t):
        if self.component.state == 0:
            return "red"
        if self.component.state == 1:
            return "green"
        if self.component.state == 2:
            return "blue"


class Machine(sim.Component):
    def setup(self, x):
        AnimateRectangle(rectangle0=(0, 0, 75, 75), component=self, x0=x, y0=100)

    def process(self):
        while True:
            self.state = sim.IntUniform(0, 2)()
            self.hold(sim.Uniform(1, 2)())


env = sim.Environment()
Machine(x=100)
Machine(x=200)
Machine(x=300)
env.animate(True)

env.run()