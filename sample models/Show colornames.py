# Show colornames

import salabim as sim

env = sim.Environment()
names = sorted(sim.colornames().keys())
env.modelname("show colornames")
env.background_color("20%gray")
env.animate(True)
x = 10
y = env.height() - 110
sx = 165
sy = 21

for name in names:
    sim.Animate(rectangle0=(x, y, x + sx, y + sy), fillcolor0=name)
    sim.Animate(
        text=(name, "<null string>")[name == ""],
        x0=x + sx / 2,
        y0=y + sy / 2,
        anchor="c",
        textcolor0=("black", "white")[env.is_dark(name)],
        fontsize0=15,
    )
    x += sx + 4
    if x + sx > 1024:
        y -= sy + 4
        x = 10

env.run(sim.inf)
