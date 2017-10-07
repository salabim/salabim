"""
Bank renege example

Scenario:
  A counter with a random service time and customers who renege. Based on the
  program bank08.py from TheBank tutorial of SimPy 2. (KGM)

"""
import salabim as sim

NEW_CUSTOMERS = 5  # Total number of customers
INTERVAL_CUSTOMERS = 10.0  # Generate new customers roughly every x seconds
MIN_PATIENCE = 1  # Min. customer patience
MAX_PATIENCE = 3  # Max. customer patience
TIME_IN_BANK = 12


class Source(sim.Component):
    """Source generates customers randomly"""
    def process(self):
        for i in range(NEW_CUSTOMERS):
            Customer()
            yield self.hold(sim.Exponential(INTERVAL_CUSTOMERS).sample())


class Customer(sim.Component):
    """Customer arrives, is served and leaves."""
    def process(self):
        env.print_trace('', self.name(), 'arrrived')

        patience = sim.Uniform(MIN_PATIENCE, MAX_PATIENCE).sample()
        yield self.request(counter, fail_delay=patience)
        wait = env.now() - self.creation_time()

        if self.failed():
            # We reneged
            env.print_trace('', self.name(), 'RENEGED after {:6.3f}'.format(wait))
        else:
            # We got to the counter
            env.print_trace('', self.name(), 'waited for {:6.3f}'.format(wait))
            yield self.hold(sim.Exponential(TIME_IN_BANK).sample())
            env.print_trace('', self.name(), 'finished')
            # auto release counter

# Setup and start the simulation


env = sim.Environment(trace=True)

# Start processes and run

counter = sim.Resource(capacity=1)
Source()

env.run()
