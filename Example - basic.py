#Example - basic.py
import salabim as sim


class Car(sim.Component):
    def process(self):
        while True:
            yield self.hold(1)


de = sim.Environment(trace=True)
Car()
sim.run(till=5)
