import salabim as sim
import types

from math import sin, cos, radians


def philosopher_fillcolor(self, t):
    if self.philosopher.mode() == 'eating':
        return 'green'
    if self.philosopher.mode() == 'thinking':
        return 'black'
    return 'red'

def fork_angle(self, t):
    claimer = self.fork.claimers().head()
    if claimer is None:
        return self.angle_mid
    if claimer == self.left_philosopher:
        return self.angle_left
    else:
        return self.angle_right


def do_animation():
    global nphilosophers, eatingtime_mean, thinkingtime_mean
    global nphilosophers_last
    env.animation_parameters(x0=-50 * env.width() / env.height(), y0=-50,
      x1=+50 * env.width() / env.height(),
      modelname='Dining philosophers', speed=8)

    alpha = 360 / nphilosophers
    r1 = 25
    r2 = r1 * sin(radians(alpha) / 4)
    for philosopher in philosophers:
        angle = philosopher.sequence_number() * alpha
        an = sim.AnimateCircle(x=r1 * cos(radians(angle)), y=r1 * sin(radians(angle)),
            radius=r2, linewidth=0, fillcolor=philosopher_fillcolor, screen_coordinates=False)
        an.philosopher = philosopher

    for fork in forks:
        angle = (fork.sequence_number() + 0.5) * alpha
        an = sim.AnimateLine(x=0, y=0,
            spec=(r1 - r2, 0, r1 + r2, 0), linewidth=r2 / 4, linecolor='green', angle=fork_angle)
        an.fork = fork
        an.left_philosopher = philosophers[fork.sequence_number()]
        an.angle_mid = angle
        an.angle_left = angle - 0.2 * alpha
        an.angle_right = angle + 0.2 * alpha
#        an.angle = forkangle

    sim.AnimateSlider(x=520, y=0, width=100, height=20,
        vmin=10, vmax=40, resolution=5, v=eatingtime_mean, label='eating time', action=set_eatingtime_mean,
        xy_anchor='nw')
    sim.AnimateSlider(x=660, y=0, width=100, height=20,
        vmin=10, vmax=40, resolution=5, v=thinkingtime_mean, label='thinking time', action=set_thinkingtime_mean,
        xy_anchor='nw')
    sim.AnimateSlider(x=520 + 50, y=-50, width=200, height=20,
        vmin=3, vmax=40, resolution=1, v=nphilosophers, label='# philosophers', action=set_nphilosophers,
        xy_anchor='nw')
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
    def setup(self):
        self.rightfork = forks[self.sequence_number()]
        self.leftfork = forks[self.sequence_number() - 1 if self.sequence_number() else nphilosophers-1]

    def process(self):
        while True:
            yield self.hold(thinkingtime_mean * sim.Uniform(0.5, 1.5)(), mode='thinking')
            yield self.request(self.leftfork, self.rightfork, mode='waiting')
            yield self.hold(eatingtime_mean * sim.Uniform(0.5, 1.5)(), mode='eating')
            self.release()

eatingtime_mean = 20
thinkingtime_mean = 20
nphilosophers = 8
sim.random_seed(1234567)

while True:
    env = sim.Environment()
    forks = [sim.Resource() for _ in range(nphilosophers)]
    philosophers = [Philosopher() for _ in range(nphilosophers)]

    do_animation()

    env.run()
