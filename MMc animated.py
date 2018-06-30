import salabim as sim


def do_animation():
    sim.AnimateQueue(servers.requesters(), x=800, y=200, direction='w')
    sim.AnimateQueue(servers.claimers(), x=900, y=200, direction='n')

    sim.AnimateMonitor(servers.requesters().length, x=50, y=450, width=env.width()-100, horizontal_scale=4,
        title=lambda:'Length of requesters. Mean ={:10.2f}'.format(servers.requesters().length.mean()))
    sim.AnimateMonitor(servers.claimers().length, x=50, y=550, width=env.width()-100, horizontal_scale=4,
        title=lambda:'Length of claimers. Mean ={:10.2f}'.format(servers.claimers().length.mean()))
    sim.AnimateMonitor(system.length_of_stay, x=50, y=650,
        height=75, width=env.width()-100, horizontal_scale=5, vertical_scale=2, as_points=True,
        title=lambda:'Length of stay in system. Mean ={:10.2f}'.format(system.length_of_stay.mean()))

    sim.AnimateText(text='Server', x=900, y=200 - 50, text_anchor='n')
    sim.AnimateText(text='<-- Waiting line', x=900 - 145, y=200 - 50, text_anchor='n')
    env.animation_parameters(modelname='M/M/c')


class Client(sim.Component):

    def process(self):
        self.enter(system)
        yield self.request(servers)
        yield self.hold(sim.Exponential(server_time).sample())
        self.leave()


class ClientGenerator(sim.Component):
    def process(self):
        while True:
            yield self.hold(sim.Exponential(iat).sample())
            Client()


env = sim.Environment()

nservers = 5
iat = 1
server_time = 4

system = sim.Queue('system')

servers = sim.Resource(name='servers', capacity=nservers)

ClientGenerator()

do_animation()
env.run()
