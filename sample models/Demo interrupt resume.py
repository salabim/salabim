import salabim as sim

"""
This model demonstrates the use of 'stacked' interrupts.

Each of two machine has three parts, that will be subject to failure. If one or more of these parts has failed,
the machine is stopped. Only when all parts are operational, the machine can continue its work (hold).

For a machine to work it needs the resource 'res'. If, during the requesting of this resource, one or more parts
of that machine break down, the machine stops requesting until all parts are operational.

In this model the interrupt level frequently gets to 2 or 3 (all parts broken down).

Have a close look at the trace output to see what is going on.
"""


class Machine(sim.Component):
    def setup(self):
        for _ in range(3):
            Part(name="part " + str(self.sequence_number()) + ".", machine=self)

    def process(self):
        while True:
            self.request(res)
            self.hold(5)
            self.release(res)


class Part(sim.Component):
    def setup(self, machine):
        self.machine = machine

    def process(self):
        while True:
            self.hold(ttf())
            self.machine.interrupt()
            self.hold(ttr())
            self.machine.resume()


env = sim.Environment(trace=True)
ttf = sim.Uniform(10, 20)  # time to failure distribution
ttr = sim.Uniform(3, 6)  # time to repair distribution

res = sim.Resource()

for _ in range(2):
    Machine()

env.run(400)