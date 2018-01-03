import salabim as sim


class AnimateDriveCar(sim.Animate):
    def __init__(self, car, *args, **kwargs):
        self.car = car
        sim.Animate.__init__(self, image='red.png', *args, **kwargs)

    def visible(self, t):
        return self.car.mode() == 'drive'


class AnimateStandStillCar(sim.Animate):
    def __init__(self, car, *args, **kwargs):
        self.car = car
        sim.Animate.__init__(self, image='blue.png', *args, **kwargs)

    def visible(self, t):
        return self.car.mode() != 'drive'


class Car(sim.Component):
    def process(self):
        while True:
            yield self.hold(1, mode='drive')
            yield self.hold(1, mode='stand_still')

env = sim.Environment(trace=True)

env.animation_parameters()
car = Car()
AnimateDriveCar(car=car, x0=100, y0=100)
AnimateStandStillCar(car=car, x0=100, y0=100)
env.run(10)
