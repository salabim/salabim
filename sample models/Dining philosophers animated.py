import salabim as sim

from math import sin, cos, radians


class AnimatePhilosopher(sim.Animate):
    def __init__(self, i):
        alpha = 360 / nphilosophers
        r1 = 25
        r2 = r1 * sin(radians(alpha) / 4)
        angle = i * alpha
        sim.Animate.__init__(
            self, x0=r1 * cos(radians(angle)), y0=r1 * sin(radians(angle)), circle0=r2, linewidth0=0, xy_anchor="c"
        )
        self.i = i

    def fillcolor(self, t):
        if philosopher[self.i].mode() == "eating":
            return "green"
        if philosopher[self.i].mode() == "thinking":
            return "fg"
        return "red"


class AnimateFork(sim.Animate):
    def __init__(self, i):
        alpha = 360 / nphilosophers
        r1 = 25
        r2 = r1 * sin(radians(alpha) / 4)
        angle = (i + 0.5) * alpha
        sim.Animate.__init__(self, x0=0, y0=0, line0=(r1 - r2, 0, r1 + r2, 0), linewidth0=r2 / 4, linecolor0="green")
        self.i = i
        self.angle_mid = angle
        self.angle_left = angle - 0.2 * alpha
        self.angle_right = angle + 0.2 * alpha

    def angle(self, t):
        claimer = fork[self.i].claimers().head()
        if claimer is None:
            return self.angle_mid
        if claimer == philosopher[self.i]:
            return self.angle_left
        return self.angle_right


def do_animation():
    global nphilosophers, eatingtime_mean, thinkingtime_mean
    global nphilosophers_last
    env.x0(-50 * env.width() / env.height())
    env.y0(-50)
    env.x1(50 * env.width() / env.height())
    env.modelname("Dining philosophers")
    env.speed(8)
    env.background_color("20%gray")
    env.animate(True)

    for i, _ in enumerate(philosopher):
        AnimatePhilosopher(i=i)
        AnimateFork(i=i)
    sim.AnimateSlider(
        x=520,
        y=env.height(),
        width=100,
        height=20,
        vmin=10,
        vmax=40,
        resolution=5,
        v=eatingtime_mean,
        label="eating time",
        action=set_eatingtime_mean,
    )
    sim.AnimateSlider(
        x=660,
        y=env.height(),
        width=100,
        height=20,
        vmin=10,
        vmax=40,
        resolution=5,
        v=thinkingtime_mean,
        label="thinking time",
        action=set_thinkingtime_mean,
    )
    sim.AnimateSlider(
        x=520 + 50,
        y=env.height() - 50,
        width=200,
        height=20,
        vmin=3,
        vmax=40,
        resolution=1,
        v=nphilosophers,
        label="# philosophers",
        action=set_nphilosophers,
    )
    nphilosophers_last = nphilosophers


def set_eatingtime_mean(val):
    global eatingtime_mean
    eatingtime_mean = float(val)


def set_thinkingtime_mean(val):
    global thinkingtime_mean
    thinkingtime_mean = float(val)


def set_nphilosophers(val):
    global nphilosophers
    global nphilosophers_last
    nphilosophers = int(val)
    if nphilosophers != nphilosophers_last:
        nphilosophers_last = nphilosophers
        env.main().activate()


class Philosopher(sim.Component):
    def process(self):
        while True:

            thinkingtime = sim.Uniform(0.5, 1.5).sample() * thinkingtime_mean
            eatingtime = sim.Uniform(0.5, 1.5).sample() * eatingtime_mean

            self.hold(thinkingtime, mode="thinking")
            self.request(self.leftfork, self.rightfork, mode="waiting")
            self.hold(eatingtime, mode="eating")
            self.release()


eatingtime_mean = 20
thinkingtime_mean = 20
nphilosophers = 8
sim.random_seed(1234567)
env = sim.Environment()


while True:
    env.__init__()
    philosopher = []
    fork = []
    for i in range(nphilosophers):
        philosopher.append(Philosopher())
        fork.append(sim.Resource("fork."))
        if i != 0:
            philosopher[i].leftfork = fork[i - 1]
        philosopher[i].rightfork = fork[i]

    philosopher[0].leftfork = fork[nphilosophers - 1]

    do_animation()
    env.run(500)