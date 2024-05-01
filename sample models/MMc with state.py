import salabim as sim


class Server(sim.Component):
    def process(self):
        while True:
            if not waiting_clients:
                self.wait(work_to_do)
            this_client = waiting_clients.pop()
            self.hold(sim.Exponential(server_time).sample())
            this_client.activate()


class Client(sim.Component):
    def process(self):
        self.enter(waiting_clients)
        work_to_do.trigger(max=1)
        self.passivate()


class ClientGenerator(sim.Component):
    def process(self):
        while True:
            self.hold(sim.Exponential(iat).sample())
            Client()


env = sim.Environment(trace=True)

waiting_clients = sim.Queue("waiting_clients")
work_to_do = sim.State("work_to_do")

nservers = 5
iat = 1
server_time = 4

for i in range(nservers):
    Server()

ClientGenerator(name="clientgenerator")

env.run(100)