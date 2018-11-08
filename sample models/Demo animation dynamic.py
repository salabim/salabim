import salabim as sim

"""
In this model cars arrive randomly and want to be washed by two washers

The animation shows the queue of waiting card (the requesters of washers) on the left.
for each car, the waiting time is shown as a bar.
On the right are the cars being washed (the claimers of washers), with their total washing time
as an outline and the time spent there.

The animation rectangle object wait_anim of each car, has a dynamic y coordinate and a dynamic size,
which are both implemented as methods of the car.
Note that the fillcolor of wait_animmis changed from red into yellow just by an attribute assignment.
The outline is also a dynamic rectangle.
"""


class CarGenerator(sim.Component):
    def process(self):
        while True:
            yield self.hold(sim.Uniform(0, 2)())
            Car()


class Car(sim.Component):
    def my_y(self, t):
        if self in washers.requesters():
            return self.index(washers.requesters()) * 30 + 50
        if self in washers.claimers():
            return self.index(washers.claimers()) * 30 + 50

    def my_rectangle(self, t):
        if self in washers.requesters():
            return 0, 0, (t - self.enter_time(washers.requesters())) * 10, 20
        if self in washers.claimers():
            return 0, 0, (t - self.enter_time(washers.claimers())) * 10, 20

    def setup(self):
        self.wait_anim = sim.AnimateRectangle(
            self.my_rectangle,
            x=200,
            y=self.my_y,
            fillcolor="red",
            text=str(self.sequence_number()),
            text_anchor="w",
            text_offsetx=-20,
            textcolor="white",
            arg=self,
            parent=self,
        )
        #  the arg parameter is used to access the right car in my_y and my_rectangle (self)
        #  the parent parameter is used to automatically remove the animation when the car terminates

    def process(self):
        yield self.request(washers)
        duration = sim.Uniform(0, 5)()
        self.duration_anim = sim.AnimateRectangle(
            (0, 0, duration * 10, 20), fillcolor="", linecolor="yellow", x=100, y=self.my_y, arg=self, parent=self
        )
        self.wait_anim.fillcolor = "yellow"
        self.wait_anim.x = 100

        yield self.hold(duration)


env = sim.Environment(trace=False)
env.animate(True)
env.modelname("Demo animation dynamic")
env.background_color("20%gray")
sim.AnimateText("Wash", x=100, y=25, text_anchor="sw")
sim.AnimateText("Wait", x=200, y=25, text_anchor="sw")

washers = sim.Resource(name="washers", capacity=2)
CarGenerator()

env.run(100)
