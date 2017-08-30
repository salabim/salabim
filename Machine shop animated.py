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


class MachineBarAnimate(sim.Animate):
    def __init__(self, machine):
        self.machine = machine
        super().__init__(rectangle0=(0, 0, 0, 0), linewidth0=0)

    def rectanglex(self, t):
        if self.machine.mode() == 'work':
            if self.machine.scheduled_time()==sim.inf:
                d = self.machine.remaining_time    
            else:
                d = self.machine.scheduled_time() - t
        else:
            d = self.machine.remaining_time
        return(
            100, 100 + self.machine.n * 30,
            100 + d * SCALE, 100 + self.machine.n * 30 + 20)
            
    def rectangle(self, t):
        if self.machine.scheduled_time()==sim.inf:
            d = self.machine.remaining_time    
        else:
            d = self.machine.scheduled_time() - t
        return(
            100, 100 + self.machine.n * 30,
            100 + d * SCALE, 100 + self.machine.n * 30 + 20)

    def fillcolor(self, t):
        if self.machine.mode() == 'work':
            return 'green'
        if self.machine.mode() == 'wait':
            return 'red'
        if self.machine.mode() == 'repair':
            return 'orange'


class MachineTextAnimate(sim.Animate):
    def __init__(self, machine):
        self.machine = machine
        super().__init__(x0=10, y0=100 + self.machine.n * 30, text='', anchor='sw')

    def text(self, t):
        return '{} {:4d}'.format(self.machine.ident, self.machine.parts_made)


class MachineBarJobAnimate(sim.Animate):
    def __init__(self, machine):
        self.machine = machine
        super().__init__(rectangle0=(0, 0, 0, 0), linewidth0=0)

    def rectangle(self, t):
        d = self.machine.job_time
        return(
            100, 100 + self.machine.n * 30,
            100 + d * SCALE, 100 + self.machine.n * 30 + 20)

    def fillcolor(self, t):
        if self.machine.mode() == 'work':
            return ('green', 25)
        if self.machine.mode() == 'wait':
            return ('red', 25)
        if self.machine.mode() == 'repair':
            return ('orange', 25)


class RepairBlockAnimate(sim.Animate):
    def __init__(self, i):
        self.i = i
        super().__init__(y0=10, rectangle0=(0, 0, 20, 20), linecolor0='white')

    def x(self, t):
        return xrepairman(self.i, t)

    def rectangle(self, t):
        if self.i == -1:
            if repairman.claimers()[0] is None:
                d = 0
            else:
                d = repairman.claimers()[0].scheduled_time() - t
        else:
            if repairman.requesters()[self.i] is None:
                d = 0
            else:
                if repairman.requesters()[self.i] == other:
                    d = repairman.requesters()[self.i].remaining_time
                else:
                    d = repairman.requesters()[self.i].repair_time
        return (0, 0, d * SCALE, 20)

    def fillcolor(self, t):
        if self.i == -1:
            if repairman.claimers()[0] is None:
                return ''
            else:
                return 'orange'
        else:
            if repairman.requesters()[self.i] is None:
                return ''
            else:
                return 'red'


class RepairTextAnimate(sim.Animate):
    def __init__(self, i):
        self.i = i
        super().__init__(y0=10 + 3, text='',
            textcolor0='white', fontsize0=20, anchor='sw')

    def x(self, t):
        return xrepairman(self.i, t) + 2

    def text(self, t):
        if self.i == -1:
            if repairman.claimers()[0] is None:
                return ''
            else:
                return repairman.claimers()[0].ident
        else:
            if repairman.requesters()[self.i] is None:
                return ''
            else:
                return repairman.requesters()[self.i].ident


def xrepairman(i, t):
    start = 0
    if i != -1:
        start += (repairman.claimers()[0].scheduled_time() - t)
        for j in range(i):
            if repairman.requesters()[j] is not None:
                if repairman.requesters()[j] != other:
                    start += repairman.requesters()[j].repair_time
    return 10 + start * SCALE


def do_animation():

    env.animation_parameters(modelname='Machine shop', speed=4)
    for machine in machines:
        MachineBarAnimate(machine)
        MachineTextAnimate(machine)
        MachineBarJobAnimate(machine)
    MachineBarAnimate(other)
    MachineTextAnimate(other)
    MachineBarJobAnimate(other)
    for i in range(-1, NUM_MACHINES):
        RepairBlockAnimate(i)
        RepairTextAnimate(i)


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

    def setup(self, n):
        self.n = n
        self.ident = str(n)
        self.parts_made = 0
        self.broken = False
        self.disturber = Disturber(machine=self)

    def process(self):
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

    def process(self):
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
print('Machine shop')
env = sim.Environment()
random.seed(RANDOM_SEED)  # This helps reproducing the results

repairman = sim.Resource('repairman')

machines = [Machine(n=i) for i in range(NUM_MACHINES)]
other = Other()

# Execute!
do_animation()
env.run(till=SIM_TIME)

# Analyis/results
print('Machine shop results after %s weeks' % WEEKS)
for machine in machines:
    print('%s made %d parts.' % (machine.name(), machine.parts_made))
repairman.print_statistics()
