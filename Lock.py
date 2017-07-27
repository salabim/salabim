import salabim as sim

left=-1
right=+1

def sidename(side):
    return 'l' if side==left else 'r'
                     
class Shipgenerator(sim.Component):

    def process(self):
        while True:
            yield self.hold(sim.Exponential(iat).sample())
            ship=Ship(name=sidename(self.side)+'ship.')
            ship.side=self.side
            ship.length=meanlength*sim.Uniform(2/3,4/3).sample()
            if lock.mode()=='Idle':
                lock.reactivate()
            
class Ship(sim.Component):
    def process(self):
        self.enter(wait[self.side])
        yield self.passivate(mode='Wait')
        yield self.hold(intime,mode='Sail in')
        self.leave(wait[self.side])
        self.enter(lockqueue)
        lock.reactivate()
        yield self.passivate(mode='In lock')
        yield self.hold(outtime,mode='Sail out')
        self.leave(lockqueue)
        lock.reactivate()
        
class Lock(sim.Component):

    def process(self):
        while True:
            if len(wait[left])+len(wait[right])==0:
                yield self.passivate(mode='Idle')

            usedlength=0

            for ship in wait[self.side]:
                if usedlength+ship.length<=locklength:
                    usedlength += ship.length
                    ship.reactivate()
                    yield self.passivate('Wait for sail in')
            yield self.hold(switchtime,mode='Switch')
            self.side=-self.side
            for ship in lockqueue:
                ship.reactivate()
                yield self.passivate('Wait for sail out')

de=sim.Environment(random_seed=1234567,trace=True)
locklength=60
switchtime=10
intime=2
outtime=2
meanlength=30
iat=30

lockqueue=sim.Queue('lockqueue')

shipcounter=0
wait={}
    
for side in (left,right):
    wait[side]=sim.Queue(name=sidename(side)+'Wait')
    shipgenerator=Shipgenerator(name=sidename(side)+'Shipgenerator')
    shipgenerator.side=side

lock=Lock('Lock')
lock.side=left

de.run(500)

