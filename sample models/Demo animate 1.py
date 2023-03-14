import salabim as sim


class AnimateMovingText(sim.Animate):
    def __init__(self):
        env.Animate.__init__(self, text="", x0=100, x1=1000, t1=env.now() + 10,env=env)

    def y(self, t):
        return int(t) * 50 + 20

    def text(self, t):
        return f"{t:0.1f}"


env = sim.Environment()

env.animate(True)

AnimateMovingText()

env.run(12)