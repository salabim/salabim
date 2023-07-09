import salabim as sim
sim.yieldless(False)


"""
This us a demonstration of several ways to show queues dynamically and the corresponding statistics
The model simply generates components that enter a queue and leave after a certain time.

Note that the actual model code (in the process description of X does not contain any reference
to the animation!
"""


class X(sim.Component):
    def setup(self, i):
        self.i = i

    def animation_objects(self, id):
        """
        the way the component is determined by the id, specified in AnimateQueue
        'text' means just the name
        any other value represents the colour
        """
        if id == "text":
            ao0 = sim.AnimateText(
                text=self.name(), textcolor="fg", text_anchor="nw", offsetx=-20
            )
            return 0, 20, ao0
        else:
            ao0 = sim.AnimateRectangle(
                (-20, 0, 20, 20),
                text=self.name(),
                fillcolor=id,
                textcolor="white",
                arg=self,
            )
            return 45, 0, ao0

    def process(self):
        while True:
            yield self.hold(sim.Uniform(0, 4)())
            self.enter(q)
            yield self.hold(sim.Uniform(0, 4)())
            self.leave()


env = sim.Environment(trace=False)
env.background_color("20%gray")

q = sim.Queue("queue")

qa0 = sim.AnimateQueue(q, x=100, y=25, title="queue, normal", direction="e", id="blue")
qa1 = sim.AnimateQueue(
    q, x=100, y=75, title="queue, reversed", direction="e", reverse=True, id="green"
)
qa2 = sim.AnimateQueue(
    q,
    x=100,
    y=125,
    title="queue, maximum 6 components",
    direction="e",
    max_length=6,
    id="red",
)
qa3 = sim.AnimateQueue(
    q, x=100, y=350, title="queue, text only", direction="s", id="text", max_length=8
)

sim.AnimateMonitor(
    q.length, x=10, y=450, width=480, height=100, horizontal_scale=50, vertical_scale=5
)

sim.AnimateMonitor(
    q.length_of_stay,
    x=10,
    y=570,
    width=480,
    height=100,
    horizontal_scale=50,
    vertical_scale=5,
)

sim.AnimateText(
    text=lambda: q.length.print_histogram(as_str=True),
    x=500,
    y=700,
    text_anchor="nw",
    font="narrow",
    fontsize=10,
)

sim.AnimateText(
    text=lambda: q.print_info(as_str=True),
    x=500,
    y=340,
    text_anchor="nw",
    font="narrow",
    fontsize=10,
)
for i in range(15):
    X(i=i)

env.animate(True)

env.modelname("Demo queue animation")

env.run(till=sim.inf)
