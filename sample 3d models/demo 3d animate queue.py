import salabim as sim

class X(sim.Component):
    def animation3d_objects(self, id):
        size_x = 10
        size_y = 10
        size_z = 10
        if id == 1:
            ao0 = sim.Animate3dBox(x_len=8, y_len=8, z_len=8, z=0, x_ref=0, y_ref=0, z_ref=1, color="red", shaded=True)
            ao1 = sim.Animate3dCylinder(x1=0, y1=0, z0=8, z1=9, color="white")
            return (size_x, size_y, size_z, ao0, ao1)
        else:
            ao0 = sim.Animate3dBox(x_len=8, y_len=8, z_len=8, z=0, x_ref=0, y_ref=0, z_ref=1, color="green", shaded=True)
            return (size_x, size_y, size_z, ao0)

    def process(self):
        self.enter(q)
        self.hold(sim.Uniform(1, 10))
        self.leave(q)


env = sim.Environment(trace=True)

q = sim.Queue("q")
sim.ComponentGenerator(X, iat=1)


env.animate(True)
env.animate3d(True)

sim.AnimateQueue(q, direction="e", x=100, y=100)
sim.Animate3dQueue(q, x=20, y=0, z=0, direction="x+", id=1)
sim.Animate3dQueue(q, x=0, y=20, z=0, direction="y+")
q.animate3d(x=0, y=0, z=20, direction="z+")  # alternative for Animate3dQueue

env.width3d(950)
env.height3d(768)
env.position3d((0, 100))
env.background_color("black")
env.width(950)
env.height(768)
env.position((960, 100))

env.show_fps(True)
sim.Animate3dGrid(x_range=range(0, 101, 10), y_range=range(0, 101, 10))


env.view.x_eye = -100
env.view.y_eye = -100
env.view.z_eye = 100
env.view.x_center = 50
env.view.y_center = 50
env.view.z_center = 0
env.view.field_of_view_y = 50

env.show_camera_position()
env.speed(1)

env.run(100000)
