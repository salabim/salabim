# Car.py
import salabim as sim
sim.yieldless(False)



class Car(sim.Component):
    def process(self):
        while True:
            yield self.hold(1)


env = sim.Environment(trace=True)
Car()
env.run(till=5)
