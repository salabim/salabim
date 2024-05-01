import salabim as sim


class Philosopher(sim.Component):
    def setup(self):
        self.rightfork = forks[self.sequence_number()]
        self.leftfork = forks[(self.sequence_number() - 1) % nphilosophers]

    def process(self):
        while True:
            self.hold(thinkingtime_mean * sim.Uniform(0.5, 1.5)(), mode="thinking")
            self.request(self.leftfork, self.rightfork, mode="waiting")
            self.hold(eatingtime_mean * sim.Uniform(0.5, 1.5)(), mode="eating")
            self.release()


eatingtime_mean = 20
thinkingtime_mean = 20
nphilosophers = 8

env = sim.Environment(trace=True)
forks = [sim.Resource() for _ in range(nphilosophers)]
[Philosopher() for _ in range(nphilosophers)]

env.run(100)