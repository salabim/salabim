# Car.py
import salabim as sim
sim.yieldless(True)


class Car(sim.Component):
    def process(self):
        while True:
            self.hold(1)


env = sim.Environment(trace=True)
Car()
env.run(till=5)