# demo wait.py
"""
Here, princes, are generated.
In the meantime, kings die.
The youngest prince, will become king.

If a new prince arrives, he checks, whether there's a king.
If so, he will wait for a kingdied trigger.
If not, he will become king.

Note that in this demo, the priority (-now) in wait is used to make
the youngest prince to become king.

This is demo of the trigger/waitfor mechanism,
just to allow one waiter to be honored.
"""

import salabim as sim


class PrinceGenerator(sim.Component):
    def process(self):
        while True:
            self.hold(int(sim.Exponential(40).sample()))  # every 10-20 years othere's a new heir of the throne
            Prince()


class Prince(sim.Component):
    def process(self):
        self.live_till = env.now() + int(sim.Uniform(60, 90).sample())
        env.print_trace("", "", "going to live till", "{:13.3f}".format(self.live_till))
        if env.king is None:  # there is no king, so this prince will become king, immediately
            kings.append(("no king", env.lastkingdied, env.now(), env.now() - env.lastkingdied))
            env.king = self
        else:
            self.wait((king_died, True, -env.now()), fail_at=self.live_till)
            if self.failed():  # the prince dies before getting to the throne
                env.print_trace("", "", "dies before getting to the throne")
                return
            env.king = self
        env.print_trace("", "", "vive le roi!", env.king.name())
        kings.append((self.name(), env.now(), self.live_till, self.live_till - env.now()))
        self.hold(till=self.live_till)
        env.print_trace("", "", "Le roi est mort.")
        env.king = None
        king_died.trigger(max=1)
        if env.king is None:
            env.lastkingdied = env.now()


env = sim.Environment(trace=True)
env.king = None
env.lastkingdied = env.now()
kings = []
king_died = sim.State(name="king died")
PrinceGenerator()

env.run(5000)
print("king                     from       to duration")
for king in kings:
    print("{:20}{:9d}{:9d}{:9d}".format(*king))