# Animate classes.py

"""
This program demonstrates the various animation classes available in salabim.
"""
import salabim as sim

env = sim.Environment(trace=False)
env.animate(True)
env.modelname("Demo animation classes")
env.background_color("90%gray")

sim.AnimatePolygon(spec=(100, 100, 300, 100, 200, 190), text="This is\na polygon")
sim.AnimateLine(spec=(100, 200, 300, 300), text="This is a line")
sim.AnimateRectangle(spec=(100, 10, 300, 30), text="This is a rectangle")
sim.AnimateCircle(radius=60, x=100, y=400, text="This is a cicle")
sim.AnimateCircle(radius=60, radius1=30, x=300, y=400, text="This is an ellipse")
sim.AnimatePoints(spec=(100, 500, 150, 550, 180, 570, 250, 500, 300, 500), text="These are points")
sim.AnimateText(text="This is a one-line text", x=100, y=600)
sim.AnimateText(
    text="""\
Multi line text
-----------------
Lorem ipsum dolor sit amet, consectetur
adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud
exercitation ullamco laboris nisi ut
aliquip ex ea commodo consequat. Duis aute
irure dolor in reprehenderit in voluptate
velit esse cillum dolore eu fugiat nulla
pariatur.

Excepteur sint occaecat cupidatat non
proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.
""",
    x=500,
    y=100,
)

sim.AnimateImage("Pas un pipe.jpg", x=500, y=400)
env.run(100)
