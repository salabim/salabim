import salabim as sim
import math

background_color = "#eeffcc"

env = sim.Environment(trace=False)

do_animate = True
do_animate3d = True

env.x0(0)
env.x1(380)
env.y0(0)

env.width3d(900)
env.height3d(700)
env.position3d((0, 100))
env.background_color("black")
env.background3d_color(background_color)
env.width(950)
env.height(768)
env.position((960, 100))

env.animate(do_animate)
env.animate3d(do_animate3d)
env.show_fps(True)
sim.Animate3dGrid(x_range=range(-200, 201, 10), y_range=range(-200, 201, 10),color="black")

env.view(x_eye=127.3433,y_eye=47.3797,z_eye=42.9300,x_center=30.0000,y_center=100.0000,z_center=0.0000,field_of_view_y=50.0000)  # t=117.2089
env.view(x_eye=127.3433,y_eye=47.3797,z_eye=53.0000,x_center=40.0000,y_center=100.0000,z_center=0.0000,field_of_view_y=50.0000)  # t=21.8455
# env.view.x_eye = lambda t: 50 + 100 * math.sin(t / 50)
# env.view.y_eye = lambda t: 50 + 100 * math.cos(t / 50)



sim.Animate3dObj("12281_Container_v2_L2", x=40, y=0, z=0,y_translate=90, x_scale=0.1, y_scale=0.1, z_scale=0.1)

env.speed(1)

env.run(100000)

