import salabim as sim


class Car(sim.Component):
    def process(self):
        car_animate = sim.Animate(x0=100, y0=100, image='')
        while True:
            car_animate.update(image='red.png')
            yield self.hold(1, mode='drive')
            car_animate.update(image='blue.png')
            yield self.hold(1, mode='stand_still')


env = sim.Environment(trace=True)

env.animation_parameters()
car = Car()
env.run(20)
