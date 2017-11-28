import salabim as sim


def do_animation():
    servers.requesters().animate(x=800, y=200)
    servers.claimers().animate(x=900, y=200, direction='n',reverse=True)

    sim.Animate(text='Server', x0=900, y0=200-50, anchor='n')
    sim.Animate(text='<-- Waiting line', x0=900-145, y0=200-50, anchor='n')
    env.animation_parameters(modelname='M/M/c')


class Client(sim.Component):
    def animation_objects(self, q):
        s = 20 + self.sequence_number()*2
        size_x = 2*s+10
        size_y = size_x
        an1=sim.Animate(rectangle0=(-s,-s,s,s), linewidth0=0,fillcolor0='green')
        an2=sim.Animate(text=str(self.sequence_number()), textcolor0='white',anchor='center')
        return (size_x, size_y, an1, an2)

    def process(self):
        yield self.request(servers)
        yield self.hold(sim.Exponential(server_time).sample())


class ClientGenerator(sim.Component):
    def process(self):
        while True:
            yield self.hold(sim.Exponential(iat).sample())
            client = Client()

env = sim.Environment()

nservers = 5
iat = 1
server_time = 4

servers = sim.Resource('servers', capacity=nservers)

ClientGenerator()

do_animation()
env.run()
