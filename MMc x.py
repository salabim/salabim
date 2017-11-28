import salabim as sim
from collections import deque


class AnimateWaitingClientSquare(sim.Animate):
    def __init__(self, pos):
        # define animation object for the green square of pos'th client in the queue
        self.pos = pos

        sim.Animate.__init__(
            self, rectangle0=(-20,-20,20,20), offsetx0=800-pos*50, offsety0=200,
            fillcolor0='green', linewidth0=0)

    def visible(self, t):
        client = servers.requesters()[self.pos]  # this gets the pos'th client in the requesters queue
        return client is not None  # hide if there's no client there


class AnimateWaitingClientText(sim.Animate):
    def __init__(self, pos):
        # define animation object for the sequence_number of pos'th client in the queue
        self.pos = pos

        sim.Animate.__init__(
            self, text='', offsetx0=800-pos*50, offsety0=200, textcolor0='white', anchor='center')

    def text(self, t):
        client = servers.requesters()[self.pos]  # this gets the pos'th client in the requesters queue
        if client:  # if there is a client
            return str(client.sequence_number())  # give the sequence_number
        else:
            return ''


class AnimateServicedClientSquare(sim.Animate):
    def __init__(self, index):
        # define animation object for the green/gray square for the index'th server
        self.index = index

        sim.Animate.__init__(
            self, rectangle0=(-20,-20,20,20), offsetx0=900, offsety0=200+index*50,
            linewidth0=0)

    def fillcolor(self, t):
        for client in servers.claimers():
            if client.server_index == self.index:
                return 'green'  # if there's a client as server index, make green
        return 'gray'  # if not, gray


class AnimateServicedClientText(sim.Animate):
    def __init__(self, index):
        # define animation object for the sequence_number for the index'th server
        self.index = index

        sim.Animate.__init__(
            self, text='', offsetx0=900, offsety0=200+index*50, textcolor0='white', anchor='center')

    def text(self, t):
        for client in servers.claimers():
            if client.server_index == self.index:
                return str(client.sequence_number())  # if there's a client at server index, show sequence_number
        return ''  # else, null string


def do_animation():
    for pos in range(20):  # show at most 20 waiting clients
        AnimateWaitingClientSquare(pos)  # to show a green square for the pos'th client in the waiting queue
        AnimateWaitingClientText(pos)  # to show the sequence number of the pos'th client in the waiting queue

    for index in range(nservers):
        AnimateServicedClientSquare(index)  # to show a green/gray square for the client served by server index
        AnimateServicedClientText(index)  # to show the sequence number of the client served by server index

    sim.Animate(text='Server', x0=900, y0=200-50, anchor='n')
    sim.Animate(text='<-- Waiting line', x0=900-145, y0=200-50, anchor='n')
    env.animation_parameters(modelname='M/M/c')


class Client(sim.Component):
    def process(self):
        yield self.request(servers)
        self.server_index=idle_server_indexes.popleft()  # makes that servers are assigned round robin
        yield self.hold(sim.Exponential(server_time).sample())
        idle_server_indexes.append(self.server_index)  # return the server to the idle pool


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
idle_server_indexes= deque(range(nservers))  # this is to keep track of which servers are idle (only for animation)

ClientGenerator()

do_animation()
env.run()
