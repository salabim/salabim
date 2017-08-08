#Example - bank, 3 clerks, reneging.py
import salabim as sim

class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            yield self.hold(sim.Uniform(5,15).sample())
        
class Customer(sim.Component):
    def process(self):
        if len(waitingline)>=5:
            de.number_balked += 1
            de.print_trace('','','balked')
            yield self.cancel()
        self.enter(waitingline)
        for clerk in clerks:
            if clerk.ispassive():
                clerk.activate()
                break # activate only one clerk
        yield self.hold(50) #if not serviced within this time, renege
        if self in waitingline:
            self.leave(waitingline)
            de.number_reneged += 1
            de.print_trace('','','reneged')
        else:
            yield self.passivate() # wait for service to be completed
    
class Clerk(sim.Component):
    def process(self):
        while True:
            while len(waitingline)==0:
                yield self.passivate()
            self.customer=waitingline.pop()
            self.customer.activate()
            yield self.hold(30)
            self.customer.activate()            
        
de=sim.Environment(random_seed=1234567,trace=False)
CustomerGenerator()
de.number_balked=0
de.number_reneged=0
clerks=sim.Queue('clerks')
for i in range(3):
    Clerk().enter(clerks)
    
waitingline=sim.Queue('waitingline')
de.run(till=50000)

waitingline.print_statistics()
print('number reneged',de.number_reneged)
print('number balked',de.number_balked)
