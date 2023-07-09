import salabim as sim

"""
This is a demonstration of several ways to show queues dynamically and the corresponding statistics
The model simply generates components that enter a queue and leave after a certain time.

Note that the actual model code (in the process description of X does not contain any reference
to the animation!
"""


class X(sim.Component):
    def setup(self, i, q):
        self.i = i
        self.q = q

    def animation_objects(self, id):
        """
        the way the component is determined by the id, specified in AnimateQueue
        'text' means just the name
        any other value represents the colour
        """
        if id == "text":
            ao0 = sim.AnimateText(text=self.name(), textcolor="fg", text_anchor="nw", offsetx=-20)
            return 0, 16, ao0
        else:
            ao0 = sim.AnimateRectangle((-20, 0, 20, 20), text=self.name(), fillcolor=id, textcolor="white", arg=self)
            return 45, 0, ao0

    def process(self):
        while True:
            self.hold(sim.Uniform(0, 20)())
            self.enter(self.q)
            self.hold(sim.Uniform(0, 20)())
            self.leave()


env = sim.Environment(trace=False)
env.background_color("20% gray")


q0 = sim.Queue("Drilling station")
q1 = sim.Queue("Packaging station")

sim.AnimateMonitor(q0.length, x=10, y=10, width=500, height=300, horizontal_scale=10, vertical_scale=20)
sim.AnimateMonitor(q0.length_of_stay, x=10, y=360, width=500, height=300, horizontal_scale=10, vertical_scale=20)

sim.AnimateMonitor(q1.length, x=520, y=10, width=500, height=300, horizontal_scale=10, vertical_scale=20)
sim.AnimateMonitor(q1.length_of_stay, x=520, y=360, width=500, height=300, horizontal_scale=10, vertical_scale=20)


[X(i=i, q=q0) for i in range(15)]
[X(i=i, q=q1) for i in range(20)]

env.run(100)
q0.reset_monitors()
q1.reset_monitors()


env.animate(True)

env.modelname("Jobshop 2000")
env.run()