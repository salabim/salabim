import salabim as sim
import numpy as np

env = sim.Environment()


class X(sim.Component):
    def animation_objects(self):
        dimx = 25
        dimy = 25
        ao = sim.AnimateRectangle((-10, 0, 10, 20), text=str(self.sequence_number()))
        return dimx, dimy, ao

    def process(self):
        self.enter(qx)
        yield self.hold(sim.Uniform(0, 50))
        self.leave(qx)


class Y(sim.Component):
    def animation_objects(self):
        dimx = 50
        dimy = 50
        ao = sim.AnimateRectangle((-10, -10, 10, 10), angle=45, text=str(self.sequence_number()))
        return dimx, dimy, ao

    def process(self):
        self.enter(qy)
        yield self.hold(sim.Uniform(0, 50))
        self.leave(qy)


qx = sim.Queue("qx")

trajectory1 = sim.TrajectoryCircle(radius=100, x_center=200, y_center=200, angle0=180, angle1=90)
trajectory2 = sim.TrajectoryPolygon((200, 300, 250, 300, 750, 200, 800,200), spline='b')
trajectory3 = sim.TrajectoryPolygon((800, 200, 1000, 200))

trajectory = trajectory1 + trajectory2 + trajectory3

sim.AnimatePoints(trajectory.rendered_polygon(time_step=50), linewidth=3, linecolor="green")

qy = sim.Queue("qy")

sim.AnimateQueue(qx, direction="e", x=100, y=400, title='qx')
sim.AnimateQueue(qy, direction="t", trajectory=trajectory, title='qy')

sim.ComponentGenerator(X, iat=sim.Uniform(0,2))
sim.ComponentGenerator(Y, iat=sim.Uniform(0,2))

env.animate(True)
env.modelname("demo trajectory animate_queue")
env.video_repeat(0)
env.run(25)
