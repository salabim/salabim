import salabim as sim

from math import sin,cos,pi,radians

class Philosopher(sim.Component):

    def process(self):
        while True:

            thinkingtime=sim.random.uniform(0.5,1.5)*thinkingtime_mean
            eatingtime=sim.random.uniform(0.5,1.5)*eatingtime_mean
            
            yield self.hold(thinkingtime,mode='thinking')          
            yield self.request(self.leftfork,self.rightfork,mode='waiting')
            yield self.hold(eatingtime,mode='eating')
            self.release()   
            
de=sim.Environment(random_seed=1234567)
eatingtime_mean=20
thinkingtime_mean=20
nphilosophers=8
    
philosopher={}
fork={}
for i in range(nphilosophers):
    philosopher[i]=Philosopher()
    fork[i]=sim.Resource('fork.')
    if i!=0:
        philosopher[i].leftfork=fork[i-1]
    philosopher[i].rightfork=fork[i]
        
philosopher[0].leftfork=fork[nphilosophers-1]
    
de.trace=True
de.run(500)    
    
