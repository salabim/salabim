import salabim as sim
sim.yieldless(False)



class ClientGenerator(sim.Component):
    def process(self):
        while True:
            yield self.hold(inter_arrival_time_dis.sample())
            Client()


class Client(sim.Component):
    def process(self):
        yield self.request(clerks)
        yield self.hold(service_duration_dis.sample())


env = sim.Environment(trace=True)
number_of_clerks = 5
inter_arrival_time_dis = sim.Exponential(1)
service_duration_dis = sim.Exponential(4)

clerks = sim.Resource(name="clerks", capacity=number_of_clerks)

ClientGenerator()
env.run()
