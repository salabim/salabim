import salabim as sim

class Car(sim.Component):
    def process(self):
        yield self.request(pumps)
        yield self.hold(sim.Uniform(1,9)())

class CarGenerator(sim.Component):
    def process(self):
        while True:
            yield self.hold(sim.Exponential(1)())
            Car()

sim.reset()
env = sim.Environment(trace=False)

CarGenerator()
pumps = sim.Resource(name='pumps', capacity=4)

env.animation_parameters()
sim.AnimateQueue(queue=pumps.requesters(), x=800, y=200, direction='w')
sim.AnimateQueue(queue=pumps.claimers(), x=900, y=200, direction='n')

sim.AnimateText('Pumps', x=900, y=200 - 50, text_anchor='n')
sim.AnimateText('<-- Waiting line', x=900 - 145, y=200 - 50, text_anchor='n')
env.animation_parameters(modelname='Fuel station')

env.run(100)

pumps.requesters().length_of_stay.print_histogram(30,0,1)
