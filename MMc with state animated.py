import salabim as sim


def do_animation():
    waiting_clients.animate(x=800, y=200)
    for i, server in enumerate(servers):
        server.atwork.animate(x=900, y=200 + i * 50)

    sim.Animate(text='Server', x0=900, y0=200 - 50, anchor='n')
    sim.Animate(text='<-- Waiting line', x0=900 - 145, y0=200 - 50, anchor='n')
    env.animation_parameters(modelname='M/M/c')


class Server(sim.Component):
    def setup(self, i):
        self.atwork = sim.State('at work {}'.format(i))

    def process(self):
        while True:
            if not waiting_clients:
                self.atwork.set('gray')
                yield self.wait(work_to_do)
            this_client = waiting_clients.pop()
            self.atwork.set(this_client.sequence_number())
            yield self.hold(sim.Exponential(server_time).sample())
            this_client.activate()


class Client(sim.Component):

    def process(self):
        self.enter(waiting_clients)
        work_to_do.trigger(max=1)
        yield self.passivate()


class ClientGenerator(sim.Component):
    def process(self):
        while True:
            yield self.hold(sim.Exponential(iat).sample())
            Client()


env = sim.Environment()

waiting_clients = sim.Queue('waiting_clients')
work_to_do = sim.State('work_to_do')

nservers = 5
iat = 1
server_time = 4

servers = (Server(i=i) for i in range(nservers))

ClientGenerator()

do_animation()
env.run()
