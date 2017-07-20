import salabim as sim
import random

class AnimateLED(sim.Animate):
    def __init__(self,x,y,floor,direction):
        self.floor=floor
        self.direction=direction
        
        b=xvisitor_dim/2
        if direction==up:
            polygon=(-0.5*b,0,0.5*b,0,0,1*b)
        else:
            polygon=(-0.5*b,b,0.5*b,b,0,0)     
                          
        super().__init__(x0=x,y0=y,polygon0=polygon)
        
    def fillcolor(self,t):
        if (self.floor,self.direction) in requests:
            return direction_color(self.direction)
        else:
            return ''
            
class AnimateFloorVisitor(sim.Animate):
    def __init__(self,x,y,floor,part,index):
        self.floor=floor
        self.index=index
        b=0.1*xvisitor_dim
        if part==0:
            super().__init__(rectangle0=(b,2,xvisitor_dim-b,yvisitor_dim-b),
              x0=x,y0=y,linewidth0=0)
        else:
            super().__init__(text='',fontsize0=xvisitor_dim*0.7,
              anchor='center',offsetx0=5*b,offsety0=2+4*b,textcolor0='white',
              x0=x,y0=y)

    def fillcolor(self,t):
        visitor=self.floor.visitors[self.index]
        if visitor!=None:
            return direction_color(visitor.direction)
                        
    def text(self,t):
        visitor=self.floor.visitors[self.index]
        if visitor!=None:
            return str(visitor.tofloor.n)
        
    def visible(self,t):
        return self.floor.visitors[self.index]!=None
        
class AnimateCar(sim.Animate):
    def __init__(self,x,car):
        self.car=car
        super().__init__(x0=x,
          rectangle0=(0,0,capacity*xvisitor_dim,yvisitor_dim),
          fillcolor0='lightblue')
      
    def y(self,t):
        if self.car.mode=='Move':
            return sim.interpolate(
              t,self.car.mode_time,self.car.scheduled_time,
              self.car.floor.y,self.car.nextfloor.y)
                 
        else:
            return self.car.floor.y
            
class AnimateCarVisitor(sim.Animate):
    def __init__(self,x,car,part,index):
        self.car=car
        self.index=index
        b=0.1*xvisitor_dim
        if part==0:
            super().__init__(rectangle0=(b,2,xvisitor_dim-b,yvisitor_dim-b),
              x0=x,linewidth0=0)
        else:
            super().__init__(text='',fontsize0=xvisitor_dim*0.7,
              anchor='center',offsetx0=5*b,offsety0=2+4*b,textcolor0='white',
              x0=x,linewidth0=0)              
        
    def fillcolor(self,t):
        visitor=self.car.visitors[self.index]
        if visitor!=None:
            return direction_color(visitor.direction)
            
    def y(self,t):
        if self.car.mode=='Move':
            return sim.interpolate(
              t,self.car.mode_time,self.car.scheduled_time,
              self.car.floor.y,self.car.nextfloor.y)
        else:
            return self.car.floor.y
                             
    def text(self,t):
        visitor=self.car.visitors[self.index]
        if visitor!=None:
            return str(visitor.tofloor.n)        
        
    def visible(self,t):
        return self.car.visitors[self.index]!=None
                
def do_animation():
    
    global xvisitor_dim
    global yvisitor_dim
    global capacity_last,ncars_last,topfloor_last

    xvisitor_dim=30
    yvisitor_dim=xvisitor_dim
    yfloor0=20       
     
    xcar={}
    xled={}

    x=de.width
    for car in cars:
        x-=(capacity+1)*xvisitor_dim
        xcar[car]=x
    x-=xvisitor_dim
    xsign=x
    x-=xvisitor_dim/2
    for direction in (up,down):
        x-=xvisitor_dim/2
        xled[direction]=x
    x-=xvisitor_dim
    xwait=x
    
    for floor in floors.values():
        y=yfloor0+floor.n*yvisitor_dim
        floor.y=y       
        for direction in (up,down):
            if (direction==up and floor.n<topfloor) or (direction==down and floor.n>0):
                AnimateLED(x=xled[direction],y=y+6,floor=floor,direction=direction)
        sim.Animate\
          (x0=0,y0=y,line0=(0,0,xwait,0),linecolor0='black')
        sim.Animate\
          (x0=xsign,y0=y+yvisitor_dim/2,\
          text=str(floor.n),fontsize0=xvisitor_dim/2,anchor='center')
        
        x=xwait-xvisitor_dim
        index=0
        while x>0:
            AnimateFloorVisitor(x=x,y=y,floor=floor,index=index,part=0)
            AnimateFloorVisitor(x=x,y=y,floor=floor,index=index,part=1)
            x -= xvisitor_dim     
            index += 1
            
    for car in cars:
        AnimateCar(x=xcar[car],car=car)
        x=xcar[car]
        for index in range(capacity):
            AnimateCarVisitor(x=x,car=car,index=index,part=0)
            AnimateCarVisitor(x=x,car=car,index=index,part=1)                
            x += xvisitor_dim    
                           
    ncars_last=ncars
    ui_ncars=sim.AnimateSlider\
      (x=540,y=de.height,width=90,height=20,\
      vmin=1,vmax=5,resolution=1,v=ncars,label='#elevators',action=set_ncars)
          
    topfloor_last=topfloor
    ui_topfloor=sim.AnimateSlider\
      (x=640,y=de.height,width=90,height=20,\
      vmin=5,vmax=20,resolution=1,v=topfloor,label='top floor',action=set_topfloor)
          
    capacity_last=capacity
    ui_capacity=sim.AnimateSlider\
        (x=740,y=de.height,width=90,height=20,\
        vmin=2,vmax=6,resolution=1,v=capacity,label='capacity',action=set_capacity)
          
    ui_load_0_n=sim.AnimateSlider\
      (x=540,y=de.height-50,width=90,height=25,\
      vmin=0,vmax=400,resolution=25,v= load_0_n,label='Load 0->n',action=set_load_0_n) 
          
    ui_load_n_n=sim.AnimateSlider\
      (x=640,y=de.height-50,width=90,height=25,\
      vmin=0,vmax=400,resolution=25,v=load_n_n,label='Load n->n',action=set_load_n_n) 
          
    ui_load_n_0=sim.AnimateSlider\
      (x=740,y=de.height-50,width=90,height=25,\
      vmin=0,vmax=400,resolution=25,v=load_n_0,label='Load n->0',action=set_load_n_0) 

    sim.animation_parameters(modelname='Elevator',speed=32)
                
def set_load_0_n(val):
    global load_0_n
    load_0_n=float(val)
    if vg_0_n.ispassive:
        vg_0_n.reactivate()

def set_load_n_n(val):
    global load_n_n
    load_n_n=float(val)
    if vg_n_n.ispassive:
        vg_n_n.reactivate()
                
def set_load_n_0(val):
    global load_n_0
    load_n_0=float(val)   
    if vg_n_0.ispassive:
        vg_n_0.reactivate()
            
def set_capacity(val):
    global capacity
    global capacity_last
    capacity=int(val)
    if capacity!=capacity_last:
        capacity_last=capacity
        de.stop_run()    
        
def set_ncars(val):
    global ncars
    global ncars_last
    ncars=int(val)
    if ncars!=ncars_last:
        ncars_last=ncars
        de.stop_run()    
        
def set_topfloor(val):
    global topfloor
    global topfloor_last
    topfloor=int(val)
    if topfloor!=topfloor_last:
        topfloor_last=topfloor
        de.stop_run()    
        
def direction_color(direction):
    if direction==1:
        return 'red'
    if direction==-1:
        return 'green'
    return 'yellow'
   
class  VisitorGenerator(sim.Component):
    def __init__(self,from_,to,id,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.from_=from_
        self.to=to
        self.id=id
    
    def process(self):
        while True:
            from_=random.randint(self.from_[0],self.from_[1])
            while True:
                to=random.randint(self.to[0],self.to[1])
                if from_!=to:
                    break

            visitor=Visitor(from_,to)
            if self.id=='0_n':
                load=load_0_n
            elif self.id=='n_0':
                load=load_n_0
            else:
                load=load_n_n                    
                
            if load==0:
                yield self.passivate()
            else:
                iat=3600/load
                r=random.uniform(0.5,1.5)
                yield self.hold(r*iat)


class Visitor(sim.Component):
    def __init__(self,from_,to,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fromfloor=floors[from_]
        self.tofloor=floors[to]
        self.direction=getdirection(self.fromfloor,self.tofloor)
                
    def process(self):
        self.enter(self.fromfloor.visitors)
        if not (self.fromfloor,self.direction)  in requests:
            requests[self.fromfloor,self.direction]=sim.now()            
        for car in cars:
            if car.ispassive:
                car.reactivate()
        
        yield self.passivate()

class Car(sim.Component):
    def __init__(self,capacity,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.capacity=capacity
        self.direction=still
        self.floor=floors[0]
        self.visitors=sim.Queue(name='visitors in car')
        
    def process(self):
        dooropen=False
        self.floor=floors[0]
        self.direction=still
        dooropen=False
        while True:
            if self.direction==still:
                if len(requests)==0:
                    yield self.passivate(mode='Idle')
            if self.count_to_floor(self.floor)>0:
                yield self.hold(dooropen_time,mode='Door open')
                dooropen=True
                for visitor in self.visitors:
                    if visitor.tofloor==self.floor:
                        visitor.leave(self.visitors)
                        visitor.reactivate()
                yield self.hold(exit_time,mode='Let exit')
                
            if self.direction==still:
                self.direction=up # just random

            for self.direction in (self.direction,-self.direction):
                if (self.floor,self.direction) in requests:
                    del requests[self.floor,self.direction]

                    if not dooropen:
                        yield self.hold(dooropen_time,mode='Door open')
                        dooropen=True
                    for visitor in self.floor.visitors:
                        if visitor.direction==self.direction:
                            if self.visitors.length<self.capacity:
                                visitor.leave(self.floor.visitors)
                                visitor.enter(self.visitors)
                        yield self.hold(enter_time,mode='Let in')
                    if (self.floor.count_in_direction(self.direction)>0):
                        if not (self.floor,self.direction) in requests:
                            requests[self.floor,self.direction]=sim.now()

                if self.visitors.length>0:
                    break
            else:
                if len(requests)>0:
                    earliest=sim.inf
                    for (floor,direction) in requests:
                        if requests[floor,direction]<earliest:
                            self.direction=getdirection(self.floor,floor)
                            earliest=requests[floor,direction]
                else:
                    self.direction=still
            if dooropen:
                yield self.hold(doorclose_time,mode='Door close')
                dooropen=False
                
            if self.direction!=still:
                self.nextfloor=floors[self.floor.n+self.direction]
                yield self.hold(move_time,mode='Move')
                self.floor=self.nextfloor
  
    def count_to_floor(self,tofloor):
        n=0
        for visitor in self.visitors:
            if visitor.tofloor==tofloor:
                n+=1
        return n

    def count_from_floor(self,fromfloor):
        n=0
        for visitor in self.visitors:
            if visitor.fromfloor==tofloor:
                n+=1
        return n

class Floor():
    def __init__(self,n):
        self.n=n
        self.visitors=sim.Queue(name='visitors '+str(n))
                
    def count_in_direction(self,dir):
        n=0
        for visitor in self.visitors:
            if visitor.direction==dir:
                n+=1
        return n
                        
def getdirection(fromfloor,tofloor):
    if fromfloor.n<tofloor.n:
        return +1
    if fromfloor.n>tofloor.n:
        return -1
    return 0

up=1
still=0
down=-1

move_time=10
dooropen_time=3
doorclose_time=3
enter_time=3
exit_time=3

load_0_n=50
load_n_n=100
load_n_0=100
capacity=4
ncars=3
topfloor=15
sim.random_seed(1234567)

while True:
    de=sim.Environment()
        
    vg_0_n=VisitorGenerator(
      from_=(0,0),to=(1,topfloor),id='0_n',name='vg_0_n')
    vg_n_0=VisitorGenerator(
      from_=(1,topfloor),to=(0,0),id='n_0',name='vg_n_0')
    vg_n_n=VisitorGenerator(
      from_=(1,topfloor),to=(1,topfloor),id= 'n_n',name='vg_n_n')
      
    requests={}
    floors={}
    for ifloor in range(topfloor+1):
        floors[ifloor]=Floor(ifloor)

    cars=[]
        
    for icar in range(ncars):
        thiscar=Car(name='car '+str(icar),capacity=capacity)
        cars.append(thiscar)
        
    do_animation()

    de.run()



    
