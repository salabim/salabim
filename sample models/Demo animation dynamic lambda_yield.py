import salabim as sim
sim.yieldless(False)


"""
In this model cars arrive randomly and want to be washed by two washers
The animation shows the queue of waiting card (the requesters of washers) on the left.
for each car, the waiting time is shown as a bar.
On the right are the cars being washed (the claimers of washers), with their total washing time
as an outline and the time spent there.
The animation rectangle object wait_anim of each car, has a dynamic y coordinate and a dynamic size,
which are both implemented as lambda functions that get the car and the time t as parameters.
Note that the fillcolor of wait_animmis changed from red into yellow just by an attribute assignment.
The outline is also a dynamic rectangle with a lambda function for the y position.
"""


class CarGenerator(sim.Component):
    def process(self):
        while True:
            yield self.hold(sim.Uniform(0, 2)())
            Car()


class Car(sim.Component):
    def setup(self):
        self.wait_anim = sim.AnimateRectangle(
            spec=lambda arg, t: (0, 0, (t - arg.enter_time(list(arg.queues())[0])) * 10, 20),
            x=200,
            y=lambda arg, t: arg.index(list(arg.queues())[0]) * 30 + 50,
            fillcolor="red",
            text=str(self.sequence_number()),
            text_anchor="w",
            text_offsetx=-20,
            textcolor="white",
            arg=self,
            parent=self,
        )
        # the lambda function get the car (via arg=self) and t as parameters from the animation engine
        # in this case, the car is exactly in one queue, either washers.requesters() or washers.claimers()
        # therefore list(queues)[0] gives the queue the car is in

    def process(self):
        yield self.request(washers)
        duration = sim.Uniform(0, 5)()
        self.duration_anim = sim.AnimateRectangle(
            spec=(0, 0, duration * 10, 20),
            x=100,
            y=lambda arg, t: arg.index(list(self.queues())[0]) * 30 + 50,
            fillcolor="",
            linecolor="yellow",
            arg=self,
            parent=self,
        )
        self.wait_anim.fillcolor = "yellow"
        self.wait_anim.x = 100

        yield self.hold(duration)


env = sim.Environment(trace=False)
env.animate(True)
env.modelname("Demo animation dynamic lambda")
env.background_color("20%gray")
sim.AnimateText("Wash", x=100, y=25, text_anchor="sw")
sim.AnimateText("Wait", x=200, y=25, text_anchor="sw")

washers = sim.Resource(name="washers", capacity=2)
CarGenerator()

env.run(100)