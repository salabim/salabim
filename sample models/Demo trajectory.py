import salabim as sim
import numpy as np

if __name__ == "__main__":
    env = sim.Environment()
    env.x0(-11)
    env.x1(20)
    env.y0(-10)
    env.animate(True)

    acc = 1
    dec = 1
    trajectory0 = sim.TrajectoryPolygon(
        [-10, -10, -10, 0, -10, 8, -8, 10, 0, 10, 10, 10], t0=0, v0=0, v1=0, vmax=5, acc=acc, dec=dec, spline="Catmull-Rom", res=50
    )
    trajectory1 = sim.TrajectoryStandstill([10, 10], duration=5)
    trajectory2 = sim.TrajectoryCircle(radius=5, x_center=10, y_center=5, angle0=90, angle1=0, vmax=1, v0=0, acc=acc, dec=dec, orientation=0)
    trajectory3 = sim.TrajectoryPolygon((15, 5, 15, 0), t0=50, v0=1, v1=1, vmax=10, acc=acc, dec=dec)
    trajectory4 = sim.TrajectoryCircle(radius=5, x_center=10, y_center=0, angle0=0, angle1=-90, vmax=1, acc=acc, dec=dec)
    trajectory5 = sim.TrajectoryPolygon(
        polygon=(10, -5, 8, -5, -8, -10, -10, -10), v0=1, vmax=5, v1=0, acc=acc, dec=dec, spline="bézier", orientation=lambda x: x + 90
    )
    trajectory = sum((trajectory0, trajectory1, trajectory2, trajectory3, trajectory4, trajectory5))
    ticks = [0]
    for itrajectory in (trajectory1, trajectory2, trajectory3, trajectory4, trajectory5):
        ticks.append(ticks[-1] + itrajectory.duration())
    colors = ["red", "blue", "green", "red", "yellow", "red"]

    sim.AnimatePoints(trajectory.rendered_polygon(time_step=0.5), linewidth=0.1, linecolor="green")

    sim.AnimatePolygon(
        (-0.5, -0.1, 0.5, -0.1, 0.75, 0, 0.5, 0.1, -0.5, 0.1),
        x=lambda t: trajectory.x(t),
        y=lambda t: trajectory.y(t),
        angle=lambda t: trajectory.angle(t),
        fillcolor=lambda t: env.color_interp(t, ticks, colors),
        linecolor="black",
        linewidth=0.01,
        visible=lambda t: trajectory.in_trajectory(t),
    )
    env.speed(2)
    env.modelname("demo trajectory")
    env.run(50)
