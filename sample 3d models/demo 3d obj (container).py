import salabim as sim
import math

env = sim.Environment(trace=False)

do_animate = True
do_animate3d = True

env.x0(0)
env.x1(380)
env.y0(0)

env.width3d(950)
env.height3d(768)
env.position3d((0, 100))
env.background_color("black")
env.width(950)
env.height(768)
env.position((960, 100))

env.animate(do_animate)
env.animate3d(do_animate3d)
env.show_fps(True)
sim.Animate3dGrid(x_range=range(0, 101, 10), y_range=range(0, 101, 10))


env.view.x_eye = lambda t: 50 + 100 * math.sin(t / 50)
env.view.y_eye = lambda t: 50 + 100 * math.cos(t / 50)
env.view.z_eye = 53
env.view.x_center = 50
env.view.y_center = 50
env.view.z_center = 0
env.view.field_of_view_y = 50


sim.Animate3dObj("12281_Container_v2_L2", x=lambda t: t, y=-40, y_translate=90, x_scale=0.1, y_scale=0.1, z_scale=0.1)

env.speed(1)

env.run(100000)

