import salabim as sim
import math
from ycecream import yc
from pathlib import Path
import functools

import fiftydots

yc.show_line_number = True
gl = sim.gl
glu = sim.glu
glut = sim.glut


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
#sim.Animate3dGrid(xrange=range(0, 101, 10), yrange=range(0, 101, 10))

env.view.x_eye = lambda t: sim.interpolate(t,0,15,49.136,-60)
env.view.y_eye = 50
env.view.z_eye = lambda t: sim.interpolate(t,0,15,0.78,100)
env.view.x_center = 50
env.view.y_center = 50
env.view.z_center = 0
env.view.field_of_view_y = 50

for i, prop in enumerate("x_eye y_eye z_eye x_center y_center z_center field_of_view_y".split()):
    ao = sim.AnimateRectangle(spec=(0, 0, 75, 35), fillcolor="30%gray", x=5 + i * 80, y=env.height() - 90, screen_coordinates=True)
    ao = sim.AnimateText(
        text=lambda arg, t: f"{arg.label}", x=5 + i * 80 + 70, y=env.height() - 90 + 15, text_anchor="se", textcolor="white", screen_coordinates=True
    )
    ao.label = "fovy" if prop == "field_of_view_y" else prop

    ao = sim.AnimateText(
        text=lambda arg, t: f"{getattr(env.view,arg.prop)(t):11.3f}",
        x=5 + i * 80 + 70,
        y=env.height() - 90,
        text_anchor="se",
        textcolor="white",
        screen_coordinates=True,
    )
    ao.prop = prop

for x,y in fiftydots.coordinates("salabim", value=True, default=" ", intra=1, proportional=True, width=None, align="c", x_first=False, narrow=False, x_offset=0, y_offset=0):
    y0 = 100-x * 2
    x0 = 60-y*2
    sim.Animate3dBox(x_len=1, y_len=1, x=x0, y=y0, color=lambda t: env.colorinterpolate(t,0,15,"red","lightblue"), edge_color="", shaded=True)

for x,y in fiftydots.coordinates("goes 3D", value=True, default=" ", intra=1, proportional=True, width=None, align="c", x_first=False, narrow=False, x_offset=0, y_offset=0):
    y0 = 100-x * 2
    x0 = 40-y*2
    sim.Animate3dBox(x_len=1, y_len=1, x=x0, y=y0, color=lambda t: env.colorinterpolate(t,0,15,"green","lightblue"), edge_color="", shaded=True)


env.speed(1)

env.run(100000)

