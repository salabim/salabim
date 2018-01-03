import salabim as sim

class P(sim.Component):
    def process(self):
        while True:
            x.set('red')
            yield self.hold(2)
            x.set('blue')
            yield self.hold(2)
            x.set()
            yield self.hold(2)
            x.reset()
            yield self.hold(2)
            

env=sim.Environment()
env.animation_parameters(background_color='black')
x=sim.State()
x.animate()

P()

env.run()

