import salabim as sim


class X(sim.Component):
    def hold2(self, t):
        '''
        Holds double the time t given. Needs to be called with yield from.
        '''
        yield self.hold(t*2)
        
    def process(self):
        yield from self.hold2(sim.Uniform(0,3)())
        
class X_Generate(sim.Component):
    def process(self, n):
        for _ in range(n):
            X()
            yield self.hold(sim.Uniform(0, 6)())
                   
env = sim.Environment(trace=True)
X_Generate(name='x_generate', n=5)
env.run()

