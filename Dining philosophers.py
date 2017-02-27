import salabim as sim

class  Philosopher(sim.Component):

    def process(self):
        while True:
            yield self.hold(25)
            yield self.request(self.leftfork,self.rightfork)
            yield self.hold(20)
            self.release()
 
def experiment():
    
    sim.trace(True)
    for i in range(8):
        philosopher=Philosopher(name='philosopher.')
        if i==0:
            philosopher0=philosopher
        else:
            philosopher.leftfork=fork
        fork=sim.Resource('fork.')
        philosopher.rightfork=fork
        
    philosopher0.leftfork=fork
    
    sim.run(100)

experiment()

print('done')
