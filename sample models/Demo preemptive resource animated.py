import salabim as sim


class Generator(sim.Component):
    def process(self):
        i = 0
        while True:
            self.hold(sim.Uniform(2, 4)())
            prio = sim.Pdf((1, 2, 3, 4), 1)()
            quantity = sim.Pdf((1, 2, 3), 1)()
            duration = sim.Uniform(4, 8)()
            Client(name=str(i), prio=prio, quantity=quantity, resource=r, duration=duration)
            Client(name=str(i), prio=prio, quantity=quantity, resource=rp, duration=duration)
            i += 1


class Client(sim.Component):
    def animation_objects(self, id):
        color = {1: "red", 2: "orange", 3: "green", 4: "blue"}[self.prio]
        len = self.quantity * 20
        if id.direction == "e":
            an0 = sim.AnimateRectangle(spec=(0, 0, len - 2, 20), fillcolor=color, text=self.name())
        else:
            an0 = sim.AnimateRectangle(spec=(-len + 2, 0, 0, 20), fillcolor=color, text=self.name())
        return (len, 20, an0)

    def setup(self, prio, quantity, resource, duration):
        self.prio = prio
        self.quantity = quantity
        self.resource = resource
        self.duration = duration

    def process(self):

        remain = self.duration
        while True:
            self.request((self.resource, self.quantity, self.prio))
            self.hold(remain, mode="")
            if not self.isbumped():
                break
            remain -= env.now() - self.mode_time()

        self.release(self.resource)


env = sim.Environment(trace=False)
Generator()
r = sim.Resource("r non premeptive", 3, preemptive=False)
rp = sim.Resource("r preemptive", 3, preemptive=True)
r.requesters().animate(x=700, y=100)
r.claimers().animate(x=850, y=100, direction="e")
rp.requesters().animate(x=700, y=200)
rp.claimers().animate(x=850, y=200, direction="e")
env.modelname("Demo preemptive resource")
env.animate(True)
env.run()