#Example - bank, 3 clerks, reneging (resources).py
import salabim as sim

class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer()
            yield self.hold(sim.Uniform(5,15).sample())
        
class Customer(sim.Component):
    def process(self):
        if len(clerks.requesters())>=5:
            de.number_balked += 1
            de.print_trace('','','balked')
            yield self.cancel()
        yield self.request(clerks,fail_at=de.now()+50)
        if self.request_failed():
            de.number_reneged += 1
            de.print_trace('','','reneged')
        else:
            yield self.hold(30)
            self.release()
                    
de=sim.Environment(random_seed=1234567,trace=False)
CustomerGenerator()
de.number_balked=0
de.number_reneged=0
clerks=sim.Resource('clerk',3)

de.run(till=50000)

clerks.requesters().print_statistics()
print('number reneged',de.number_reneged)
print('number balked',de.number_balked)
