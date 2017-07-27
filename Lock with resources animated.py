import salabim as sim

left=-1
right=+1

def sidename(side):
    return 'l' if side==left else 'r'

def shortname(ship):
    s=''
    for c in ship.name():
        if c!='.':
            s=s+c
    return s        
    
def shipcolor(side):
    if side==left:
        return 'blue'
    else:
        return 'red'
    
def ship_polygon(ship):
    return (ship.side*(ship.length-2),0,ship.side*3,0,ship.side*2,3,ship.side*(ship.length-2),3)    
            
class AnimateWaitShip(sim.Animate):
    def __init__(self,part,x,y,index,side):
        if side==left:
            anchor='se'
        else:
            anchor='sw'
        if part==0:
            super().__init__(polygon0=(),x0=x,y0=y,fillcolor0=shipcolor(side),anchor=anchor,linewidth0=0)
        elif part==1:
            super().__init__(text='',x0=x,y0=y,textcolor0='white',anchor=anchor,fontsize0=2.5,offsetx0=side*5)            
        self.index=index
        self.side=side
    
    def polygon(self,t):
        ship=lockmeters[self.side].requesters()[self.index]
        if ship!=None:
            return ship_polygon(ship) 
        else:
             return((0,0,0,0))     
             
    def text(self,t):
        ship=lockmeters[self.side].requesters()[self.index]
        if ship!=None:
            return shortname(ship)   
        else:
            return ''  
                           
class AnimateLockShip(sim.Animate):
    def __init__(self,part,y,index):
        self.part=part
        if part==0:
            super().__init__(polygon0=(),x0=0,y0=y,fillcolor0='',linewidth0=0)
        elif part==1:
            super().__init__(text='',x0=0,y0=y,textcolor0='white',fontsize0=2.5)            
        self.index=index
        self.side=side
    
    def polygon(self,t):
        ship=lockqueue[self.index]
        if ship!=None:
            return ship_polygon(ship) 
        else:
             return((0,0,0,0))     
             
    def text(self,t):
        ship=lockqueue[self.index]
        if ship!=None:
            return shortname(ship)   
        else:
            return ''  
            
    def anchor(self,t):
        ship=lockqueue[self.index]
        if ship==None:
            return 'sw'
        else:
            if ship.side==left:
                return 'se'
            else:
                return 'sw'
                
    def fillcolor(self,t):
        if self.part==0:
            ship=lockqueue[self.index]
            if ship!=None:
                return shipcolor(ship.side)   
            else:
                return (0,0,0,0)
        else:
            return super().fillcolor(t)
                    
    def x(self,t):
        ship=lockqueue[self.index]
        if ship==None:
            return 0
        else:
            if self.part==0:
                offset=0
            else:
                offset=ship.side*5
            xprev=0
            for scanship in lockqueue:
                if scanship==ship:
                    return xdoor[-ship.side]+ship.side*xprev+offset
                else:
                    xprev+=scanship.length     
                       
    def y(self,t):
        if lock.mode()=='Switch':
            return sim.interpolate(t,lock.mode_time(),lock.scheduled_time(),ylevel[lock.side],ylevel[-lock.side])
        else:
            return ylevel[lock.side]
                   
def lock_water_rectangle(t):
    if lock.mode()=='Switch':
        y=sim.interpolate(t,lock.mode_time(),lock.scheduled_time(),ylevel[lock.side],ylevel[-lock.side])
    else:
        y=ylevel[lock.side]
    return (xdoor[left],-waterdepth,xdoor[right],y)

def lock_door_left_rectangle(t):
    if lock.mode()=='Switch' or lock.side==right:
        y=ylevel[right]+2
    else:
        y=ylevel[left]-waterdepth
    return (xdoor[left]-1,-waterdepth,xdoor[left]+1,y)                     

def lock_door_right_rectangle(t):
    if lock.mode()=='Switch' or lock.side==left:
        y=ylevel[right]+2
    else:
        y=ylevel[right]-waterdepth
    return (xdoor[right]-1,-waterdepth,xdoor[right]+1,y)                     
                     
def do_animation():
    global ylevel,xdoor,waterdepth

    lockheight=5
    waterdepth=2        
    ylevel={left:0,right:lockheight}
    xdoor={left:-0.5*locklength,right:0.5*locklength}
    xbound={left:-1*locklength, right:1*locklength}
    yspace=5
    
    sim.animation_parameters(x0=xbound[left],y0=-waterdepth,x1=xbound[right],modelname='Lock',speed=8)
    
    for side in [left,right]:
        x=xdoor[side]
        for i in range(10):
            y=10+ylevel[side]+i*yspace
            AnimateWaitShip(part=0,index=i,x=x,y=y,side=side)
            AnimateWaitShip(part=1,index=i,x=x,y=y,side=side) 
    for i in range(4):
        y=ylevel[left]
        AnimateLockShip(part=0,index=i,y=y)
        AnimateLockShip(part=1,index=i,y=y)       
        
    sim.Animate(rectangle0=(xbound[left],ylevel[left]-waterdepth,xdoor[left],ylevel[left]),fillcolor0='aqua',linewidth0=0)
    sim.Animate(rectangle0=(xdoor[right],ylevel[right]-waterdepth,xbound[right],ylevel[right]),fillcolor0='aqua',linewidth0=0)
    a=sim.Animate(rectangle0=(0,0,0,0),fillcolor0='aqua',linewidth0=0)
    a.rectangle=lock_water_rectangle
    a=sim.Animate(rectangle0=(0,0,0,0),fillcolor0='black',linewidth0=0)
    a.rectangle=lock_door_left_rectangle
    a=sim.Animate(rectangle0=(0,0,0,0),fillcolor0='black',linewidth0=0)
    a.rectangle=lock_door_right_rectangle
    
    a=sim.Animate(text='',x0=300,y0=650,screen_coordinates=True,fontsize0=15,font='DejaVuSansMono',anchor='w')
    a.text=lambda t:'mean waiting left : {:5.1f} (n={})'.\
      format(key_in[left].requesters().mean_length_of_stay(),key_in[left].requesters().number_passed())
    a=sim.Animate(text='',x0=300,y0=630,screen_coordinates=True,fontsize0=15,font='DejaVuSansMono',anchor='w')
    a.text=lambda t:'mean waiting right: {:5.1f} (n={})'.\
      format(key_in[right].requesters().mean_length_of_stay(),key_in[right].requesters().number_passed())
    a=sim.Animate(text='xx=12.34',x0=300,y0=610,screen_coordinates=True,fontsize0=15,font='DejaVuSansMono',anchor='w')
    a.text=lambda t:'  nr waiting left : {:3d}'.format(key_in[left].requesters().length())
    a=sim.Animate(text='xx=12.34',x0=300,y0=590,screen_coordinates=True,fontsize0=15,font='DejaVuSansMono',anchor='w')
    a.text=lambda t:'  nr waiting right: {:3d}'.format(key_in[right].requesters().length())   
    
    sim.AnimateSlider\
      (x=520,y=de.height,width=100,height=20,\
      vmin=16,vmax=60,resolution=4,v=iat,label='iat',action=set_iat)
    sim.AnimateSlider\
      (x=660,y=de.height,width=100,height=20,\
      vmin=10,vmax=60,resolution=5,v=meanlength,label='mean length',action=set_meanlength)   
          
def set_iat(val):
    global iat
    iat=float(val)       
    
def set_meanlength(val):
    global meanlength
    meanlength=float(val)
                     
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
        if lock.ispassive():
            lock.reactivate()
        yield self.request((lockmeters[self.side],self.length),key_in[self.side])
        self.enter(lockqueue)
        yield self.hold(intime)
        self.release(key_in[self.side])
        yield self.request(key_out)
        yield self.hold(outtime)
        self.leave(lockqueue)
        self.release(key_out)        
                
class Lock(sim.Component):

    def process(self):
        yield self.request(key_in[left])
        yield self.request(key_in[right])
        yield self.request(key_out)
        
        while True:
            if len(key_in[self.side].requesters())==0:
                if len(key_in[-self.side].requesters())==0:
                    yield self.passivate()
            self.release(key_in[self.side])
            yield self.request((key_in[self.side],1,1000))
            lockmeters[self.side].release()
            yield self.hold(switchtime,mode='Switch')
            self.side=-self.side
            self.release(key_out)
            yield self.request((key_out,1,1000),mode=None)
            
de=sim.Environment(random_seed=1234567)

locklength=60
switchtime=10
intime=2
outtime=2
meanlength=30
iat=30

lockmeters={}
key_in={}
lockqueue=sim.Queue('lockqueue')    
key_out=sim.Resource(name=' key_out')

for side in (left,right):
    lockmeters[side]=sim.Resource(capacity=locklength,name=sidename(side)+' lock meters',anonymous=True)
    key_in[side]=sim.Resource(name=sidename(side)+' key in')    
    shipgenerator=Shipgenerator(name=sidename(side)+'Shipgenerator')
    shipgenerator.side=side

lock=Lock('Lock')
lock.side=left

do_animation()
de.run()

