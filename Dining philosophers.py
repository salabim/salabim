import salabim as sim


class Philosopher(sim.Component):
    def process(self):
        while True:
            thinkingtime = sim.Uniform(0.5, 1.5).sample() * thinkingtime_mean
            eatingtime = sim.Uniform(0.5, 1.5).sample() * eatingtime_mean

            yield self.hold(thinkingtime, mode='thinking')
            yield self.request(self.leftfork, self.rightfork, mode='waiting')
            yield self.hold(eatingtime, mode='eating')
            self.release()


env = sim.Environment(trace=True)
eatingtime_mean = 20
thinkingtime_mean = 20
nphilosophers = 8

philosopher = {}
fork = {}
for i in range(nphilosophers):
    philosopher[i] = Philosopher()
    fork[i] = sim.Resource('fork.')
    if i != 0:
        philosopher[i].leftfork = fork[i - 1]
    philosopher[i].rightfork = fork[i]

philosopher[0].leftfork = fork[nphilosophers - 1]

env.run(500)
