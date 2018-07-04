"""
Machine shop example

Covers:

- Interrupts
- Resources: PreemptiveResource

Scenario:
  A workshop has *n* identical machines. A stream of jobs (enough to
  keep the machines busy) arrives. Each machine breaks down
  periodically. Repairs are carried out by one repairman. The repairman
  has other, less important tasks to perform, too. Broken machines
  preempt theses tasks. The repairman continues them when he is done
  with the machine repair. The workshop works continuously.

"""
import random

import salabim as sim


RANDOM_SEED = 42
PT_MEAN = 10.0         # Avg. processing time in minutes
PT_SIGMA = 2.0         # Sigma of processing time
MTTF = 300.0           # Mean time to failure in minutes
BREAK_MEAN = 1 / MTTF  # Param. for expovariate distribution
REPAIR_TIME = 30.0     # Time it takes to repair a machine in minutes
JOB_DURATION = 30.0    # Duration of other jobs in minutes
NUM_MACHINES = 10      # Number of machines in the machine shop
WEEKS = 4              # Simulation time in weeks
SIM_TIME = WEEKS * 7 * 24 * 60  # Simulation time in minutes
SCALE = 10


def do_animation():

    env.animation_parameters(modelname='Machine shop', speed=4, background_color='20%gray')
    for machine in machines + [other]:
        sim.AnimateRectangle(spec=lambda arg, t: arg.rectangle(t, remain=False),
        fillcolor=lambda arg, t: arg.fillcolor(t, remain=False),
            linewidth=0,
            text=lambda self, t: '{} {:4d}'.format(self.ident, self.parts_made),
            text_anchor='sw', font='narrow', fontsize=15, text_offsetx=-90, textcolor='white',
            arg=machine)
        sim.AnimateRectangle(spec=lambda arg, t: arg.rectangle(t, remain=True),
            fillcolor=lambda arg, t: arg.fillcolor(t, remain=True), linewidth=0,
            text=lambda self, t: '{} {:4d}'.format(self.ident, self.parts_made),
            text_anchor='sw', font='narrow', fontsize=15, text_offsetx=-90, textcolor='white',
            arg=machine)
    sim.AnimateQueue(queue=repairman.requesters(),
        x=lambda t: 10 + repairman.claimers()[0].l(t) + 2 if repairman.claimers() else 10,
        y=10, direction='e')
    sim.AnimateQueue(queue=repairman.claimers(), x=10, y=10, direction='e')


def time_per_part():
    """Return actual processing time for a concrete part."""
    return random.normalvariate(PT_MEAN, PT_SIGMA)


def time_to_failure():
    """Return time until next failure for a machine."""
    return random.expovariate(BREAK_MEAN)


class Machine(sim.Component):
    """A machine produces parts and my get broken every now and then.

    If it breaks, it requests a *repairman* and continues the production
    after the it is repaired.

    A machine has a *name* and a numberof *parts_made* thus far.

    """
    def setup(self, n, ident, disturb):
        self.n = n
        self.ident = ident
        self.parts_made = 0
        if disturb:
            self.broken = False
            self.disturber = Disturber(machine=self)

    def l(self, t):
        if self in repairman.claimers():
            d = self.scheduled_time() - t
        else:
            if self == other:
                d = self.remaining_time
            else:
                d = self.repair_time
        return d * SCALE

    def animation_objects(self):
        ao0 = sim.AnimateRectangle(
            spec=lambda arg, t: (0, 0, arg.l(t), 20),
            fillcolor=lambda arg, t: 'orange' if self in repairman.claimers() else 'red',
            textcolor='white',
            text=self.ident, arg=self)
        return lambda arg, t: arg.l(t) + 2, 0, ao0

    def rectangle(self, t, remain):
        if remain:
            d = self.job_time
        else:
            if self.scheduled_time() == sim.inf:
                d = self.remaining_time
            else:
                d = self.scheduled_time() - t
        return(
            100, 100 + self.n * 30,
            100 + d * SCALE, 100 + self.n * 30 + 20)

    def fillcolor(self, t, remain):
        alpha = 100 if remain else 255
        if self.mode() == 'work':
            return ('green', alpha)
        if self.mode() == 'wait':
            return ('red', alpha)
        if self.mode() == 'repair':
            return ('orange', alpha)

    def process_normal(self):
            while True:
                self.job_time = time_per_part()
                self.remaining_time = self.job_time
                while self.remaining_time > 1e-8:
                    yield self.hold(self.remaining_time, mode='work')
                    self.remaining_time -= (self.env.now() - self.mode_time())
                    if self.broken:
                        if repairman.claimers()[0] == other:
                            other.release()
                            other.activate()
                        self.repair_time = REPAIR_TIME
                        yield self.request((repairman, 1, 0), mode='wait')
                        yield self.hold(self.repair_time, mode='repair')
                        self.release()
                        self.broken = False
                self.parts_made += 1

    def process_other(self):
        while True:
            self.job_time = JOB_DURATION
            self.remaining_time = self.job_time
            while self.remaining_time > 1e-8:
                yield self.request((repairman, 1, 1), mode='wait')
                yield self.hold(self.remaining_time, mode='work')
                self.remaining_time -= (self.env.now() - self.mode_time())
            other.release()
            self.parts_made += 1


class Disturber(sim.Component):
    def setup(self, machine):
        self.machine = machine

    def process(self):
        while True:
            yield self.hold(time_to_failure())
            if not self.machine.broken:
                self.machine.broken = True
                self.machine.activate()  # postpone work


class Other(sim.Component):
    def setup(self):
        self.n = -1
        self.ident = 'X'
        self.parts_made = 0

    def process_other(self):
        while True:
            self.job_time = JOB_DURATION
            self.remaining_time = self.job_time
            while self.remaining_time > 1e-8:
                yield self.request((repairman, 1, 1), mode='wait')
                yield self.hold(self.remaining_time, mode='work')
                self.remaining_time -= (self.env.now() - self.mode_time())
            other.release()
            self.parts_made += 1


# Setup and start the simulation
env = sim.Environment()
random.seed(RANDOM_SEED)  # This helps reproducing the results

repairman = sim.Resource('repairman')

machines = [Machine(n=i, ident=str(i), disturb=True, process='process_normal') for i in range(NUM_MACHINES)]
other = Machine(n=-1, ident='X', disturb=False, name='other', process='process_other')

# Execute!
do_animation()
env.run(till=SIM_TIME)

# Analyis/results
print('Machine shop results after %s weeks' % WEEKS)
for machine in machines:
    print('%s made %d parts.' % (machine.name(), machine.parts_made))
repairman.print_statistics()
