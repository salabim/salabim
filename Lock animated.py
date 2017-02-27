import salabim as sim
         
class  Shipgenerator(sim.Component):
        
    def process(self):
        while True:
            iat=ui_iat.v
            meanlength=ui_meanlength.v
            t = sim.random.expovariate(1/iat)
                
            yield self.hold(t)
            ship=Ship(name=self.side+' ship.') 
            ship.side=self.side
            ship.length=sim.random.uniform(meanlength*2/3,meanlength*4/3)

class Ship(sim.Component):
        
    def process(self):
        self.enter(system)
        mysign=sign[self.side]
        polygon=(mysign*(self.length-2),0,mysign*3,0,mysign*2,2,mysign*(self.length-2),2)
        if lock.is_passive:
            lock.reactivate()
        x=xdoor[self.side]
        y=10+ylevel[self.side]+\
          yspace*lockmeters[self.side].requesters.length-1
        self.s=self.Animate\
          (x0=x,y0=y,polygon0=polygon,fillcolor0='red',linewidth0=0)
        self.t=self.Animate\
          (x0=x+mysign*5,y0=y,text=self.name,fillcolor0='white',fontsize0=2,\
          anchor=('se' if self.side=='left' else 'sw'))
                
        yield self.request\
          (lockmeters[self.side],self.length,key_in[self.side])
        y=10+ylevel[self.side]

        for ship in lockmeters[self.side].requesters.components():
            ship.s.update(y0=y)
            ship.t.update(y0=y)
            y+=yspace            

        lengthin=0
        for ship in key_out.requesters.components():
            lengthin+=ship.length
        
        self.s.update(y0=ylevel[self.side],
            x1=xdoor[otherside(self.side)]+mysign*lengthin,
            t1=sim.now()+intime)
        self.t.update(y0=ylevel[self.side],
            x1=xdoor[otherside(self.side)]+mysign*lengthin+mysign*5,
            t1=sim.now()+intime)

        yield self.hold(intime)

        self.release(key_in[self.side])
        yield self.request(key_out)
            
        self.s.update(x1=self.s.x1-mysign*self.length,t1=sim.now()+outtime)
        self.t.update(x1=self.t.x1-mysign*self.length,t1=sim.now()+outtime)
        for ship in key_out.requesters.components():
            if ship!=lock:
                ship.s.update\
                  (x1=ship.s.x1-mysign*self.length,t1=sim.now()+outtime)
                ship.t.update\
                  (x1=ship.t.x1-mysign*self.length,t1=sim.now()+outtime)
                
        yield self.hold(outtime)
        self.release(key_out)
        self.s.remove()
        self.t.remove()
        self.leave(system)
        
class Lock(sim.Component):

    def process(self):
        self.side='left'
        yield self.request(key_in['left'])
        yield self.request(key_in['right'])
        yield self.request(key_out)
        self.s=self.Animate\
          (rectangle0=(xdoor['left'],ylevel['left']-waterdepth,xdoor['right'],ylevel['left']),\
          fillcolor0='blue',linewidth0=0)
        self.sdoor={}
        self.sdoor['left' ]=self.Animate\
          (rectangle0=(xdoor['left' ]-1,ylevel['left']-waterdepth,\
          xdoor['left' ]+1,ylevel['left' ]-waterdepth),\
          fillcolor0='black',linewidth0=0)
        self.sdoor['right']=self.Animate\
          (rectangle0=(xdoor['right']-1,ylevel['left']-waterdepth,\
          xdoor['right']+1,ylevel['right']+waterdepth),\
          fillcolor0='black',linewidth0=0)
        
        while True:
        
            if key_in[self.side].requesters.length==0:
                if key_in[otherside(self.side)].requesters.length==0:
                    yield self.passivate()
            self.release(key_in[self.side])
            yield self.request(key_in[self.side],1,1000)
            lockmeters[self.side].release()
            for ship in key_out.requesters.components():
                if ship!=lock:
                    ship.s.update\
                      (y1=ylevel[otherside(self.side)],\
                      t1=sim.now()+switchtime)
                    ship.t.update\
                      (y1=ylevel[otherside(self.side)],\
                      t1=sim.now()+switchtime)                    
            self.s.update\
              (rectangle1=(xdoor['left'],ylevel['left']-waterdepth,\
              xdoor['right'],ylevel[otherside(self.side)]),\
              t1=sim.now()+switchtime)        
            self.sdoor[self.side].update\
              (rectangle0=(xdoor[self.side]-1,ylevel['left']-waterdepth,\
              xdoor[self.side]+1,ylevel['right']+waterdepth))
            yield self.hold(switchtime)
            for ship in key_out.requesters.components():
                if ship!=lock:
                    ship.s.update()
                    ship.s.update()
            self.side=otherside(self.side)
            self.sdoor[self.side].update\
              (rectangle0=(xdoor[self.side]-1,ylevel['left']-waterdepth,\
              xdoor[self.side]+1,ylevel[self.side]-waterdepth))

            self.release(key_out)
            yield self.request(key_out,1,1000)
            
def otherside(side):
    if side=='left':
        return 'right'
    else:
        return 'left'

sim.trace(True)

switchtime=10
intime=2
outtime=2
locklength=60
lockheight=5
waterdepth=2

key_in={}
lockmeters={}
system=sim.Queue(name='system')

key_out=sim.Resource(name=' key_out')

for side in ('left','right'):
    lockmeters[side]=sim.Resource\
      (capacity=locklength,name=side+' lock meters',anonymous=True)
    key_in[side]=sim.Resource(name=side+' key in')

    shipgenerator=Shipgenerator(name=side+'shipgenerator')
    shipgenerator.side=side
    sim.random.seed(1010201)


lock=Lock(name='lock') 

ylevel={'left':0,'right':lockheight}
xdoor={'left':-0.5*locklength,'right':0.5*locklength}
xbound={'left':-1.5*locklength, 'right':1.5*locklength}
sign={'left':-1,'right':+1}
yspace=5

animation=sim.Animation\
  (x0=xbound['left'],y0=-waterdepth,x1=xbound['right'],modelname='Lock')
ui_iat=sim.main.AnimateSlider\
  (x=520,y=animation.height,width=100,height=20,\
  vmin=16,vmax=60,resolution=4,v=24,label='iat')
ui_meanlength=sim.main.AnimateSlider\
  (x=660,y=animation.height,width=100,height=20,\
  vmin=10,vmax=60,resolution=5,v=30,label='mean length')  
                
for side in ('left','right'):
    sim.main.Animate\
    (rectangle0=(xbound[side],ylevel[side]-waterdepth,\
    xdoor[side]-sign[side],ylevel[side]),fillcolor0='blue',linewidth0=0)

sim.run(till=sim.inf,animate=True,animation_speed=8)


