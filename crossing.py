import salabim as sim


class Car(sim.Component):
    def setup(self, dir):
        self.name('Car ' + dir + '.')
        self.direction = dir

    def process(self):
        yield self.wait((light[self.direction], '"$" in ("green","yellow")'))


class CarGenerator(sim.Component):
    def process(self):
        while True:
            yield self.hold(sim.Uniform(2, 4).sample())
            dir = sim.Pdf(directions, 1).sample()
            Car(dir=dir)


class TrafficLight(sim.Component):
    def setup(self):
        light['west'].set('red')
        light['east'].set('red')
        light['north'].set('green')
        light['south'].set('green')

    def process(self):
        while True:
            yield self.hold(55)
            for direction in directions:
                if light[direction].get() == 'green':
                    light[direction].set('yellow')
            yield self.hold(5)
            for direction in directions:
                if light[direction].get() == 'yellow':
                    light[direction].set('red')
                else:
                    light[direction].set('green')


env = sim.Environment(trace=True)
directions = ('west', 'east', 'north', 'south')

light = {}
for direction in directions:
    light[direction] = sim.State('light_' + direction)

TrafficLight()
CarGenerator()
env.run(500)
