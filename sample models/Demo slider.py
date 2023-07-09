import salabim as sim
import datetime


def action(v):
    v_as_datetime = datetime.datetime(2022, 1, 1) + datetime.timedelta(days=int(v))
    an0.label(f"{v_as_datetime:%Y-%m-%d}")


env = sim.Environment()
an0 = sim.AnimateSlider(x=100, y=100, action=action, width=500, height=30, v=30, vmin=0, vmax=365, resolution=1, fontsize=12, show_value=False)

env.animate(True)
env.run(sim.inf)
