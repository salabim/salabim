"""
Machine shop example

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

    def setup(self, machine=0):
        self.parts_made = 0
        self.broken = False
        self.disturber = Disturber(machine=self)

    def process(self):
        while True:
            self.remaining_time = time_per_part()
            while self.remaining_time > 1e-8:
                yield self.hold(self.remaining_time, mode='work')
                self.remaining_time -= (self.env.now() - self.mode_time())
                if self.broken:
                    if repairman.claimers()[0] == other:
                        other.release()
                        other.activate()
                    yield self.request((repairman, 1, 0))
                    yield self.hold(REPAIR_TIME)
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
    def process(self):
        while True:
            self.remaining_time = JOB_DURATION
            while self.remaining_time > 1e-8:
                yield self.request((repairman, 1, 1))
                yield self.hold(self.remaining_time, mode='work')
                self.remaining_time -= (self.env.now() - self.mode_time())
            other.release()


# Setup and start the simulation
print('Machine shop')
env = sim.Environment()
random.seed(RANDOM_SEED)  # This helps reproducing the results

repairman = sim.Resource('repairman', monitor=True)

machines = [Machine() for i in range(NUM_MACHINES)]
other = Other()

# Execute!
env.run(till=SIM_TIME)
# Analyis/results
print('Machine shop results after %s weeks' % WEEKS)
for machine in machines:
    print('%s made %d parts.' % (machine.name(), machine.parts_made))
repairman.print_statistics()
