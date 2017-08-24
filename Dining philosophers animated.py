import salabim as sim
import random

from math import sin, cos, pi, radians


class AnimatePhilosopher(sim.Animate):
    def __init__(self, i):
        alpha = 360 / nphilosophers
        r1 = 25
        r2 = r1 * sin(radians(alpha) / 4)
        angle = i * alpha
        super().__init__(x0=r1 * cos(radians(angle)), y0=r1 * sin(radians(angle)),
            circle0=(r2,), linewidth0=0)
        self.i = i

    def fillcolor(self, t):
        if philosopher[self.i].mode() == 'eating':
            return 'green'
        if philosopher[self.i].mode() == 'thinking':
            return 'black'
        return 'red'


class AnimateFork(sim.Animate):
    def __init__(self, i):
        alpha = 360 / nphilosophers
        r1 = 25
        r2 = r1 * sin(radians(alpha) / 4)
        angle = (i + 0.5) * alpha
        super().__init__(x0=0, y0=0,
            line0=(r1 - r2, 0, r1 + r2, 0), linewidth0=r2 / 4, linecolor0='green')
        self.i = i
        self.angle_mid = angle
        self.angle_left = angle - 0.2 * alpha
        self.angle_right = angle + 0.2 * alpha

    def angle(self, t):
        claimer = fork[self.i].claimers().head()
        if claimer == None:
            return self.angle_mid
        if claimer == philosopher[self.i]:
            return self.angle_left
        return self.angle_right


def do_animation():
    global nphilosophers, eatingtime_mean, thinkingtime_mean
    global nphilosophers_last
    sim.animation_parameters(x0=-50 * de.width / de.height, y0=-50, x1=+50 * de.width / de.height,
                             modelname='Dining philosophers',
                             speed=8)
    for i in philosopher:
        AnimatePhilosopher(i=i)
        AnimateFork(i=i)
    sim.AnimateSlider(x=520, y=de.height, width=100, height=20,
                      vmin=10, vmax=40, resolution=5, v=eatingtime_mean, label='eating time', action=set_eatingtime_mean)
    sim.AnimateSlider(x=660, y=de.height, width=100, height=20,
                      vmin=10, vmax=40, resolution=5, v=thinkingtime_mean, label='thinking time', action=set_thinkingtime_mean)
    sim.AnimateSlider(x=520 + 50, y=de.height - 50, width=200, height=20,
                      vmin=3, vmax=40, resolution=1, v=nphilosophers, label='# philosophers', action=set_nphilosophers)
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
        sim.main().activate()


class Philosopher(sim.Component):

    def process(self):
        while True:

            thinkingtime = sim.Uniform(0.5, 1.5).sample() * thinkingtime_mean
            eatingtime = sim.Uniform(0.5, 1.5).sample() * eatingtime_mean

            yield self.hold(thinkingtime, mode='thinking')
            yield self.request(self.leftfork, self.rightfork, mode='waiting')
            yield self.hold(eatingtime, mode='eating')
            self.release()


eatingtime_mean = 20
thinkingtime_mean = 20
nphilosophers = 8
sim.random_seed(1234567)

while True:
    de = sim.Environment()

    philosopher = {}
    fork = {}
    for i in range(nphilosophers):
        philosopher[i] = Philosopher()
        fork[i] = sim.Resource('fork.')
        if i != 0:
            philosopher[i].leftfork = fork[i - 1]
        philosopher[i].rightfork = fork[i]

    philosopher[0].leftfork = fork[nphilosophers - 1]

    do_animation()

    de.run()
