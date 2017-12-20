import salabim as sim


class AnimateCar(sim.Animate):
    def __init__(self, car, *args, **kwargs):
        self.car = car
        self.red_car_image = (sim.spec_to_image('red.png'))
        self.blue_car_image = (sim.spec_to_image('blue.png'))
        sim.Animate.__init__(self, image='', *args, **kwargs)

    def image(self, t):
        if self.car.mode() == 'drive':
            return self.red_car_image
        else:
            return self.blue_car_image


class Car(sim.Component):
    def process(self):
        while True:
            yield self.hold(1, mode='drive')
            yield self.hold(1, mode='stand_still')


env = sim.Environment(trace=True)

env.animation_parameters()
car = Car()
AnimateCar(car=car, x0=100, y0=100)
env.run(20)
