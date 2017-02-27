import salabim as sim
    
class Check(sim.Component):
    def process(self):
        self.last_load_0_n=ui_load_0_n.v
        self.last_load_n_0=ui_load_n_0.v
        self.last_load_n_n=ui_load_n_n.v
        while True:
            yield self.hold(animation.animation_speed)
            if ui_capacity.v!=capacity:
                yield self.stop_run()     
            if ui_topfloor.v!=topfloor:
                yield self.stop_run()     
            if ui_ncars.v!=ncars:
                yield self.stop_run()     
            if ui_load_0_n.v!=self.last_load_0_n:
                vg_0_n.activate()     
                self.last_load_0_n=ui_load_0_n.v
            if ui_load_n_0.v!=self.last_load_n_0:
                vg_n_0.activate()
                self.last_load_n_0=ui_load_n_0.v
            if ui_load_n_n.v!=self.last_load_n_n:
                vg_n_n.activate()     
                self.last_load_n_n=ui_load_n_n.v

class  VisitorGenerator(sim.Component):
    def __init__(self,from_,to,ui_load,*args,**kwargs):
        sim.Component.__init__(self,*args,**kwargs)
        self.from_=from_
        self.to=to
        self.ui_load=ui_load
    
    def process(self):
        while True:
            from_=sim.random.randint(self.from_[0],self.from_[1])
            while True:
                to=sim.random.randint(self.to[0],self.to[1])
                if from_!=to:
                    break

            visitor=Visitor(from_,to)
            if self.ui_load.v==0:
                yield self.passivate()
            else:
                iat=3600/self.ui_load.v
                r=sim.random.uniform(0.5,1.5)
                yield self.hold(r*iat)


class Visitor(sim.Component):
    def __init__(self,from_,to,*args,**kwargs):
        sim.Component.__init__(self,*args,**kwargs)
        self.fromfloor=floors[from_]
        self.tofloor=floors[to]
        self.direction=getdirection(self.fromfloor,self.tofloor)
                

    def process(self):
        self.enter(self.fromfloor.visitors)
        pos=self.fromfloor.visitors.length
        
        b=0.15*xvisitor_dim
        self.an1=self.Animate\
          (x0=xwait-pos*xvisitor_dim,y0=self.fromfloor.y,\
          rectangle0=(b,0,xvisitor_dim-b,yvisitor_dim-b),\
          fillcolor0=direction_color(self.direction))
        self.an2=self.Animate\
          (x0=self.an1.x0,y0=self.fromfloor.y,\
          text=str(self.tofloor.n),fontsize0=xvisitor_dim*0.7,\
          anchor='center',offsetx0=3.5*b,offsety0=3*b,fillcolor0='white')
        if not (self.fromfloor,self.direction)  in requests:
            requests[self.fromfloor,self.direction]=sim.now()
            self.fromfloor.anled[self.direction].update\
              (fillcolor0=direction_color(self.direction))
            
        for car in cars:
            if car.is_passive:
                car.reactivate()
        
        yield self.passivate()
        self.an1.remove()
        self.an2.remove()

class Car(sim.Component):
    def __init__(self,capacity,x,*args,**kwargs):
        sim.Component.__init__(self,*args,**kwargs)
        self.capacity=capacity
        self.x=x
        self.direction=still
        self.floor=floors[0]
        self.visitors=sim.Queue(name='visitors in car')
        self.an=self.Animate(x0=x,y0=floors[0].y,
          rectangle0=(0,0,capacity*xvisitor_dim,yvisitor_dim),\
            fillcolor0='lightblue')
        
    def process(self):
        dooropen=False
        self.floor=floors[0]
        self.direction=still
        dooropen=False
        while True:
            if self.direction==still:
                if len(requests)==0:
                    yield self.passivate()
            if self.count_to_floor(self.floor)>0:
                yield self.hold(dooropen_time)
                dooropen=True
                for visitor in self.visitors.components():
                    if visitor.tofloor==self.floor:
                        visitor.leave(self.visitors)
                        visitor.reactivate()
                yield self.hold(exit_time)
                self.show_visitors()
                
            if self.direction==still:
                self.direction=up # just random
            for self.direction in (self.direction,-self.direction):
                if (self.floor,self.direction) in requests:
                    del requests[self.floor,self.direction]
                    self.floor.anled[self.direction].update(fillcolor0='')

                    if not dooropen:
                        yield self.hold(dooropen_time)
                        dooropen=True
                    for visitor in self.floor.visitors.components():
                        if visitor.direction==self.direction:
                            if self.visitors.length<self.capacity:
                                visitor.leave(self.floor.visitors)
                                visitor.enter(self.visitors)
                        yield self.hold(enter_time)
                    if (self.floor.count_in_direction(self.direction)>0):
                        if not (self.floor,self.direction) in requests:
                            requests[self.floor,self.direction]=sim.now()
                            self.floor.anled[self.direction].update\
                              (fillcolor0=direction_color(self.direction))

                    self.floor.show_visitors()
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
                yield self.hold(doorclose_time)
                dooropen=False
                
            self.show_visitors()
            if self.direction!=still:
                nextfloor=floors[self.floor.n+self.direction]
                self.an.update\
                  (y0=self.floor.y,y1=nextfloor.y,t1=sim.now()+move_time)
                for visitor in self.visitors.components():
                    visitor.an1.update\
                      (y0=self.floor.y,y1=nextfloor.y,t1=sim.now()+move_time)
                    visitor.an2.update\
                      (y0=self.floor.y,y1=nextfloor.y,t1=sim.now()+move_time)
                yield self.hold(move_time)
                self.floor=nextfloor
  
            
    def show_visitors(self):
        x=self.x
        for visitor in self.visitors.components():
            visitor.an1.update(x0=x)
            visitor.an2.update(x0=x)
            x+=xvisitor_dim
        
    def count_to_floor(self,tofloor):
        n=0
        for visitor in self.visitors.components():
            if visitor.tofloor==tofloor:
                n+=1
        return n

    def count_from_floor(self,fromfloor):
        n=0
        for visitor in self.visitors.components():
            if visitor.fromfloor==tofloor:
                n+=1
        return n

class Floor():
    def __init__(self,n):
        self.n=n
        self.anled={}
        self.y=yfloor0+n*yvisitor_dim

        self.visitors=sim.Queue(name='visitors '+str(n))
        l=sim.main.Animate\
          (x0=0,y0=self.y,line0=(0,0,xwait,0),linecolor0='black')
        l=sim.main.Animate\
          (x0=xsign,y0=self.y+yvisitor_dim/2,\
          text=str(n),fontsize0=xvisitor_dim/2,anchor='center')
        b=xvisitor_dim/2
        if n<topfloor:
            self.anled[up]=sim.main.Animate\
              (x0=xled[up],y0=self.y,\
              polygon0=(-0.5*b,0,0.5*b,0,0,1*b),fillcolor0='')
        if n>0:
            self.anled[down]=sim.main.Animate\
              (x0=xled[down],y0=self.y,\
              polygon0=(-0.5*b,b,0.5*b,b,0,0),fillcolor0='')
                
    def count_in_direction(self,dir):
        n=0
        for visitor in self.visitors.components():
            if visitor.direction==dir:
                n+=1
        return n
            
    def show_visitors(self):
        x=xwait-xvisitor_dim
        for visitor in self.visitors.components():
            visitor.an1.update(x0=x)
            visitor.an2.update(x0=x)
            x-=xvisitor_dim
            
def getdirection(fromfloor,tofloor):
    if fromfloor.n<tofloor.n:
        return +1
    if fromfloor.n>tofloor.n:
        return -1
    return 0
        
def direction_name(direction):
    if direction==1:
        return 'up'
    if direction==-1:
        return 'down'
    return 'none'

def direction_color(direction):
    if direction==1:
        return 'red'
    if direction==-1:
        return 'green'
    return 'yellow'

def experiment():
    global xwait
    global xled
    global xsign
    global floors
    global cars
    global requests
    global vg_0_n
    global vg_n_0
    global vg_n_n
        
    animation_speed=animation.animation_speed
    save_trace=sim.trace()
    sim.default_env.reset()
    sim.trace(save_trace)

    check=Check()

    xcar={}
    xled={}
    
    x=animation.width
    for icar in range(ncars):
        x-=(capacity+1)*xvisitor_dim
        xcar[icar]=x
    x-=xvisitor_dim
    xsign=x
    x-=xvisitor_dim/2
    for direction in (up,down):
        x-=xvisitor_dim/2
        xled[direction]=x
    x-=xvisitor_dim
    xwait=x

    requests={}
       
    vg_0_n=VisitorGenerator\
      (from_=(0,0),to=(1,topfloor),ui_load=ui_load_0_n,name='vg_0_n')
    vg_n_0=VisitorGenerator\
      (from_=(1,topfloor),to=(0,0),ui_load=ui_load_n_0,name='vg_n_0')
    vg_n_n=VisitorGenerator\
      (from_=(1,topfloor),to=(1,topfloor),ui_load=ui_load_n_n,name='vg_n_n')

    floors={}
    for ifloor in range(topfloor+1):
        floors[ifloor]=Floor(ifloor)


    cars=[]
        
    for icar in range(ncars):
        thiscar=Car(name='car '+str(icar),capacity=capacity,x=xcar[icar])
        cars.append(thiscar)

    sim.run(till=sim.inf,animate=True,animation_speed=animation_speed)

up=1
still=0
down=-1
xvisitor_dim=30
yvisitor_dim=xvisitor_dim
yfloor0=20

move_time=10
dooropen_time=3
doorclose_time=3
enter_time=3
exit_time=3

sim.trace(False)
animation=sim.Animation(modelname='Elevator')
animation.animation_speed=32
ui_ncars=sim.main.AnimateSlider\
  (x=540,y=animation.height,width=90,height=20,\
  vmin=1,vmax=5,resolution=1,v=3,label='#elevators') 
ui_topfloor=sim.main.AnimateSlider\
  (x=640,y=animation.height,width=90,height=20,\
  vmin=5,vmax=20,resolution=1,v=15,label='top floor')    
ui_capacity=sim.main.AnimateSlider\
  (x=740,y=animation.height,width=90,height=20,\
  vmin=2,vmax=6,resolution=1,v=4,label='capacity') 
ui_load_0_n=sim.main.AnimateSlider\
  (x=540,y=animation.height-50,width=90,height=25,\
  vmin=0,vmax=400,resolution=25,v= 50,label='Load 0->n') 
ui_load_n_n=sim.main.AnimateSlider\
  (x=640,y=animation.height-50,width=90,height=25,\
  vmin=0,vmax=400,resolution=25,v=100,label='Load n->n') 
ui_load_n_0=sim.main.AnimateSlider\
  (x=740,y=animation.height-50,width=90,height=25,\
  vmin=0,vmax=400,resolution=25,v=100,label='Load n->0') 

while True:
    topfloor=ui_topfloor.v
    ncars=ui_ncars.v
    capacity=ui_capacity.v
    experiment()    

animation.exit()

