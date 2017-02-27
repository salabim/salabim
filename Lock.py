import salabim as sim

import time
         
class  Shipgenerator(sim.Component):
        
    def __init__(self,name,side,iat_distribution,length_distribution):
        sim.Component.__init__(self,name=name)
        self.side=side
        self.iat_distribution=iat_distribution
        self.length_distribution=length_distribution
 
    def process(self):
        while True:
            t = self.iat_distribution.sample
            yield self.hold(t)
            ship=Ship(name=self.side+' ship.',side=self.side,\
              length=self.length_distribution.sample) 
            ship.showtext('created')
            ship.enter(_.system)
            ship.enter(_.arrivals[self.side])
            _.shipcounter+=1
            if _.shipcounter==100000:
                self.stop_run()
            if _.lock.is_passive:
                _.lock.reactivate()

class Ship(sim.Component):
    def __init__(self,name,side,length):
        sim.Component.__init__(self,name=name)
        self.side=side
        self.length=length
        
    def showtext(self,text):
        if sim.trace():
            printtrace('','',self.name()+' '+text)
        
class Lock(sim.Component):
    def __init__(self,name,locklength,intime,outtime,switchtime):
        sim.Component.__init__(self,name=name)
        self.side='Left'
        self.intime=intime
        self.outtime=outtime
        self.switchtime=switchtime
        self.locklength=locklength
        self.queue=sim.Queue(name='Lock queue')
        
    def showstatus(self):
        if sim.trace():
            printtrace('','',self.name()+' side is '+self.side)

    def process(self):
        self.showstatus()
        while True:
            if (_.arrivals['Left'].length+_.arrivals['Right'].length)==0:
                self.enter(_.canteen)
                yield self.passivate()
                self.leave(_.canteen)

            usedlength=0

            for ship in\
              _.arrivals[self.side].components(removals_possible=False):
                if usedlength+ship.length<=self.locklength:
                    ship.showtext('move into lock')
                    yield self.hold(self.intime)
                    usedlength=usedlength+ship.length
                    ship.enter(self.queue)
                    ship.showtext('arrived in lock')
            _.avail_length+=self.locklength
            _.used_length+=usedlength
            yield self.hold(self.switchtime)
            self.side=otherside(self.side)
            self.showstatus()
            for ship in self.queue.components(removals_possible=False):
                ship.showtext('move out of lock')
                yield self.hold(self.outtime)
                ship.showtext('moved out of lock')
                _.arrivals[ship.side].remove(ship)
                self.queue.remove(ship)
                ship.leave(_.system)


def collect(iat):
    space=";  "
    out=open('outfile.txt', 'a')
    txt=str(round(sim.now()))+space+str(iat)+space+\
      str(100*round(1.0-_.canteen.mean_length,2))+\
      space+str(round(100*_.used_length/_.avail_length,1))
    txt=txt+space+str(round(time.time()-_.startrun,2))+\
      space+str(_.shipcounter)+space
    txt=txt+str(round(_.system.mean_length_of_stay))+\
      space+str(round(_.system.number_passed))+space
    txt=txt+str(round(_.system.length))
    out.write(txt+"\n")
    out.close()


def otherside(side):
    if side=='Left':
        return 'Right'
    else:
        return 'Left'
        
def experiment(iat):
    print ('iat=',iat)
    global _
    _=sim.default_env.reset(False)

    _.arrivals={}

    _.system=sim.Queue(name='system')
    _.canteen=sim.Queue(name='canteen')
    _.shipcounter=0
    _.avail_length=0
    _.used_length=0
    
    for side in ('Left','Right'):
        _.arrivals[side]=sim.Queue(name=side+' arrivals')
        shipgenerator=Shipgenerator(
            name=side+'shipgenerator',
            side=side,
            iat_distribution=sim.Exponential(iat),
            length_distribution=sim.Uniform(15,30))

    _.lock=Lock(name='Lock',locklength=60,switchtime=10,intime=2,outtime=2)
    _.startrun=time.time()
    sim.run()
    collect(iat)

#for iat in[40.0,30.0,25.0,20.0,19.0,18.0,17.0,16.9,16.8,16.7,16.6,16.5,16.4.16.3]:

for iat in[16.3]:    
    experiment(iat)
    
print('done')
