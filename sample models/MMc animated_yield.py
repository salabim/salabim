import salabim as sim
sim.yieldless(False)



def do_animation():
    sim.AnimateQueue(servers.requesters(), x=800, y=100, direction="w", title="")
    sim.AnimateQueue(servers.claimers(), x=900, y=100, direction="n", title="")

    sim.AnimateMonitor(
        servers.requesters().length,
        x=50,
        y=350,
        width=env.width() - 100,
        horizontal_scale=4,
        title=lambda: "Number of waiting customers. Mean ={:10.2f}".format(servers.requesters().length.mean()),
    )
    sim.AnimateMonitor(
        servers.claimers().length,
        x=50,
        y=450,
        width=env.width() - 100,
        horizontal_scale=4,
        title=lambda: "Number of active clerks. Mean ={:10.2f}".format(servers.claimers().length.mean()),
    )
    sim.AnimateMonitor(
        system.length_of_stay,
        x=50,
        y=550,
        height=75,
        width=env.width() - 100,
        horizontal_scale=4,
        vertical_scale=2,
        title=lambda: "Time in post office. Mean ={:10.2f}".format(system.length_of_stay.mean()),
    )

    sim.AnimateText(text="Clerks", x=900, y=100 - 50, text_anchor="n")
    sim.AnimateText(text="<-- Waiting clients", x=900 - 145, y=100 - 50, text_anchor="n")
    env.modelname("M/M/c")
    env.animate(True)


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

system = sim.Queue("system")

servers = sim.Resource(name="servers", capacity=nservers)

ClientGenerator()

do_animation()
env.run()
