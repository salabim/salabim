import salabim as sim


def do_animation():
    servers.requesters().animate(x=800, y=200)
    servers.claimers().animate(x=900, y=200, direction='n')

    sim.Animate(text='Server', x0=900, y0=200 - 50, anchor='n')
    sim.Animate(text='<-- Waiting line', x0=900 - 145, y0=200 - 50, anchor='n')
    env.animation_parameters(modelname='M/M/c')


class Client(sim.Component):

    def process(self):
        yield self.request(servers)
        yield self.hold(sim.Exponential(server_time).sample())


class ClientGenerator(sim.Component):
    def process(self):
        while True:
            yield self.hold(sim.Exponential(iat).sample())
            Client()


env = sim.Environment()

nservers = 5
iat = 1
server_time = 4

servers = sim.Resource('servers', capacity=nservers)

ClientGenerator()

do_animation()
env.run()
