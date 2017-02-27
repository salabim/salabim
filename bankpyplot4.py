import matplotlib.pyplot as plt
import salabim as sim

class  Clientgenerator(sim.Component):
    def process(self):

        for nr in range(0,250,1):
            Client(name="client.")
            yield self.hold(client_iat_distribution.sample)

class Client(sim.Component):

    def process(self):
        tin=self.now
        self.enter(systeem)
        
        yield self.request(clerk,1)
        yield self.hold(handling_distribution.sample)
        self.release(clerk,1)
        t1.append(tin)
        yield self.hold(0)
        t2.append(sim.now())
        x.append(self.sequence_number)
        dlt=self.now-tin
        y.append(dlt)
        
        self.leave(systeem)

x=[]
y=[]
t1=[]
t2=[]

clerk=sim.Resource(name='clerk',capacity=1)
systeem=sim.Queue('Systeem')
client_iat_distribution=sim.Exponential(20)
handling_distribution=sim.Uniform(20,24)
Clientgenerator(name='clientgenerator')

#experiment()
sim.trace(False)
sim.run(20000)

systeem.print_statistics()
clerk.claimers.print_statistics()
plt.scatter(x, t1,color='red',s=1)
plt.scatter(x, t2,color='blue',s=1)
plt.xlabel('time')
plt.ylabel('dlt')
plt.show()
plt.hist(y,normed=1,facecolor='g',bins=10)
plt.xlabel('time')
plt.ylabel('Probability %')
#plt.title('Histogram of dlt')
#plt.axis([10,40,0,0.1])
plt.grid(True)
plt.show()
print('done')

