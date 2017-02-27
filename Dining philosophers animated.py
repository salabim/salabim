import salabim as sim
from math import sin,cos,pi

class Check(sim.Component):
    def process(self):
        while True:
            yield self.hold(animation.animation_speed)
            if ui_number.v!=nphilosophers:
                yield self.stop_run()     
                

class Philosopher(sim.Component):

    def process(self):
        r=30
        while True:

            thinkingtime=sim.random.uniform(0.5,1.5)*ui_thinkingtime.v
            eatingtime=sim.random.uniform(0.5,1.5)*ui_eatingtime.v
            
            yield self.hold(thinkingtime)
            self.circle.update(fillcolor0='red')            
            yield self.request(self.leftfork,self.rightfork)
            self.leftfork.line.update(angle0=self.leftforkangle)
            self.rightfork.line.update(angle0=self.rightforkangle)
            self.circle.update(fillcolor0='green')
            yield self.hold(eatingtime)
            self.leftfork.line.update(angle0=self.leftfork.angle)
            self.rightfork.line.update(angle0=self.rightfork.angle)
            self.circle.update(fillcolor0='black')
            self.release()
 
def experiment():
    sim.default_env.reset(True)
    
    check=Check()
    check.suppress_trace=True    
    alpha=2*pi/nphilosophers
    r2=r1*sin(alpha/4)
    
    r2=r1*sin(alpha/4)
    for i in range(nphilosophers):
        philosopher=Philosopher(name='philosopher.')
        philosopher.i=i
        angle=i*alpha
        philosopher.circle=sim.main.Animate(x0=r1*cos(angle),y0=r1*sin(angle),circle0=(r2,),fillcolor0='black',linewidth0=0)
        
        philosopher.leftforkangle=(angle-alpha*0.3)*180/pi
        philosopher.rightforkangle=(angle+alpha*0.3)*180/pi
        if i==0:
            philosopher0=philosopher
        else:
            philosopher.leftfork=fork
        fork=sim.Resource('fork.')
        fork.angle=(angle+(alpha/2))*(180/pi)
        fork.line=sim.main.Animate(x0=0,y0=0,angle0=fork.angle,
            line0=(r1-r2,0,r1+r2,0),linewidth0=r2/4,linecolor0='green')

        philosopher.rightfork=fork
        
    philosopher0.leftfork=fork
    
    sim.run(sim.inf,animate=True)


r1=25
animation=sim.Animation(x0=-50*1024/768,y0=-50,x1=+50*1024/768,modelname='Dining philosophers')

ui_eatingtime=sim.main.AnimateSlider\
  (x=520,y=animation.height,width=100,height=20,\
  vmin=10,vmax=40,resolution=5,v=20,label='eating time') 
ui_thinkingtime=sim.main.AnimateSlider\
  (x=660,y=animation.height,width=100,height=20,\
  vmin=10,vmax=40,resolution=5,v=20,label='thinking time')    
ui_number=sim.main.AnimateSlider\
  (x=840,y=animation.height,width=200,height=20,\
  vmin=3,vmax=40,resolution=1,v=8,label='# philosophers') 

while True:
    nphilosophers=ui_number.v
    experiment()

animation.exit()

