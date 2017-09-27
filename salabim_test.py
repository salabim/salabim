import salabim as sim
import math
import random

import platform
Pythonista=(platform.system()=='Darwin')

def test():
    test35()
    
def test35():
    env=sim.Environment()
    sim.getfont('cour',10)
    

def test34():
    class X(sim.Component):
        def process(self):
            
            yield self.hold(1)
            s1.set(1)
            yield self.hold(1)
            s1.set(2)
            s2.set('red')
            yield self.hold(2)
            s1.set(30)
                        
    class Y(sim.Component):
        def process(self):
            while True:
                yield self.wait((s1,'$==2'))
                yield self.hold(1.5)

    class Z(sim.Component):
        def process(self):
            while True:
                yield self.wait((s2,'"$" in ("red","yellow")'),all=True)
                yield self.hold(1.5)
                
            
    env=sim.Environment(trace=True)
    env.print_info()
    s1=sim.State(name='s.',value=0)
    s2=sim.State(name='s.',value='green')
    s3=sim.State(name='s.')
    s1.name('piet')
    q=sim.Queue('q.')
    x=X()
    y=Y()
    z=Z()
    env.run(10)
    s1.print_statistics()


def test33():
    class X(sim.Component):
        def process(self):
            
            yield self.hold(1)
            s1.set(1)
            yield self.hold(1)
            s1.set(2)
            s2.set('red')
            yield self.hold(2)
            s1.set(30)
                        
    class Y(sim.Component):
        def process(self):
            while True:
                yield self.wait((s1,lambda x, component, state: x/2>self.env.now()))
                yield self.hold(1.5)

    class Z(sim.Component):
        def process(self):
            while True:
                yield self.wait((s2,lambda x, component, state: x in ("red","yellow")))
                yield self.hold(1.5)
                
            
    env=sim.Environment(trace=True)
    env.print_info()
    s1=sim.State(name='s.',value=0)
    s2=sim.State(name='s.',value='green')
    s3=sim.State(name='s.')
    q=sim.Queue('q.')
    x=X()
    y=Y()
    z=Z()
    env.run(10)
    sim.show_fonts()
    print(sim.fonts())


def test32():
    class X(sim.Component):
        def process(self):
            yield self.wait(go)
            print('X after wait')
            yield self.hold(10)
            
        def p1(self):
            print('X in p1')
            yield self.passivate()
            
    class Y(sim.Component):
        def process(self):
            yield self.hold(2)
            x.activate(keep_wait=True,at=20)
            
            
            
            
    env=sim.Environment(trace=True)
    go=sim.State()
    x=X()
    y=Y()
    env.run()
    
    
def test31():
    class X(sim.Component):
        def process(self):
            
            yield self.hold(1)
            s1.set()
            yield self.hold(2)
            s1.reset()
            yield self.hold(2)
            y.print_info()
            s1.trigger()
            
    class Y(sim.Component):
        def process(self):
            while True:
                yield self.wait(s1,(s2,'red'),(s2,'green'),s3)
                yield self.hold(1.5)
                
            
    env=sim.Environment(trace=True)
    env.print_info()
    s1=sim.State(name='s.')
    s2=sim.State(name='s.')
    s3=sim.State(name='s.')
    q=sim.Queue('q.')
    x=X()
    y=Y()
    env.run(10)
    print('value at ',env.now(),s1.get())
    print (s1.value.xduration())
    print(s1.value.tx())
    print(env)
    print(y)
    print(q)
    print(s1)
    s1.print_info()
    s2.print_info()
    
def test30():
    env=sim.Environment()
    m=sim.Monitor('m')
    print (m.x(ex0=True))
    m.tally(1)
    m.tally(2)
    m.tally(3)
    m.tally(0)
    m.tally('0')
    m.tally('12')
    m.tally('abc')
    print (m.x(ex0=True))
    
    
def test29():
    global light
    class Light(sim.Component):
        def setup(self):
            self.green=sim.State(name='green')
            
        def process(self):
            while True:
                yield self.hold(1)
                self.green.trigger(max=2)
                yield self.hold(1)
                self.green.reset()
                
    class Car(sim.Component):
        def process(self):
            while True:
                yield self.wait((light.green,True,1),(light.green,True,1),fail_delay=8,all=True)
                yield self.hold(sim.Uniform(1,3).sample())
    
    de=sim.Environment(trace=True)
    for i in range(10):
        car=Car()
    light=Light()
    de.run(10)
    light.green.print_statistics()
    print(light.green.value.xt())
    print(light.green.waiters())
    
    
def test28():
    de=sim.Environment(trace=True)
    wait={}
    for i in range(3):
        wait[i]=sim.Queue('wait.')

    
def test27():
    m1=sim.Monitor('m1')
    print (m1.mean(),m1.std(),m1.percentile(50),m1.histogram())
    m1.tally(10)
    print (m1.mean(),m1.std(),m1.percentile(50),m1.histogram())
    
    
def test26():
    global de
    class X(sim.Component):
        def _get_a(self):
            return self.a
           
        def _now(self):
            return self.env._now
           
        def process(self):
            m2.tally()
            yield self.hold(1)
            self.a=4
            m2.tally()
            m2.monitor(True)
            print('3',m2.xt())
            yield self.hold(1)
            self.a=20
            m2.tally()
            yield self.hold(1)
            self.a=0
            m2.tally()
            yield self.hold(1)
            m3.tally()
            m2.monitor(True)


        
    
    de=sim.Environment()
    m1=sim.Monitor('m1',type='uint8')
    print (m1.mean())    
    m1.tally(10)
    m1.tally(15)
    m1.tally(20)
    m1.tally(92)
    m1.tally(0)
    m1.tally(12)
    m1.tally(0)
    print ('m1.x()',m1.x(force_numeric=False))
        
    print ('m1',m1.mean(),m1.std(),m1.percentile(50))
    print ('m1 ex0',m1.mean(ex0=True),m1.std(ex0=True),m1.percentile(50,ex0=True))
    x=X()
    x.a=10
    m2=sim.MonitorTimestamp('m2',getter=x._get_a,type='int8')
    print('1',m2.xt())
    m2.monitor(True)
    m2.tally()
    print('a',m2.xt())
#    m2.monitor(True)
    m2.tally()
    print('2',m2.xt())

        
    m3=sim.MonitorTimestamp('m3',getter=x._now) 
    print(m3())

    de.run(10)
    print('4',m2.xt()) 
    print('5',m2.xduration())     
    print(m2.mean(),m2.std(),m2.percentile(50))
    m1.print_histogram(10,0,10)    
    m2.print_histogram(10,0,10)
    print(m3.xduration())

    m3.print_histogram(10,0,10)
    print('done')

#    for i in range(101):
#        print(i,m1.percentile(i),m2.percentile(i))
    m3=sim.Monitor('m3')
    m3.tally(1)
    m3.tally(3)
    print('xx')    
    
def test25():
    de=sim.Environment()
    q=sim.Queue('q')
    c={}
    for i in range(8):
        c[i]=sim.Component(name='c.')
        c[i].enter(q)
    print(q)
    for c in q:
        c.priority(q,-c.sequence_number())
    print(q)
    
def test24():
    class X1(sim.Component):
        def process(self):
            print('**x1 active')
            yield self.request((r,2))
        def p1(self):
            yield self.hold(0.5)
            yield self.activate(process=self.process())
            
    class X2(sim.Component):
        def process(self):
            yield self.hold(1)
            x1.activate(at=3,keep_request=True)
            yield self.hold(5)
            x1.request(r)
            yield self.hold(1)
            x1.passivate()
            de.main().passivate()
            yield self.hold(5)
            x1.reactivate(at=20)
            
    class X3(sim.Component):
        def process(self):
            a=1
            yield self.hold(1)
        pass
            
    de=sim.Environment(trace=True)
    x1=X1(process='p1')
    x1.activate(at=0.5,process='process',urgent=True,mode='blabla')
    x2=X2()
    x3=X3()
    print('***name=',x3.running_process())
    x4=sim.Component()
    x3.activate(process='process')
    r=sim.Resource('resource')
    de.run(till=sim.inf)
    
def test1():
    print('test1')

    class X(sim.Component):
        def __init__(self,extra=1,*args,**kwargs):
            sim.Component.__init__(self,*args,**kwargs)
            self.extra=extra
            
        
        def process(self):
            while True:
                yield self.hold(1)
                pass
                
        def action2(self):
            for i in range(5):
                yield self.hold(25)

            yield self.hold(1)
                
        def actionx(self):
            pass
                    
    class Y(sim.Component):
        
        def process(self):
            x[3].reactivate(process=x[3].action2(),at=30)
            x[4].cancel()
            yield self.hold(0.5)
            yield self.standby()
            yield self.activate(process=self.action2(0.3))

            
        def action2(self,param):
            yield self.hold(param)
            
    class Monitor(sim.Component):
        def process(self):
            while env.now()<30:
                yield self.standby()
                        
    de=sim.Environment(trace=True)
    q=sim.Queue()

    x=[0]
    for i in range(10):
        x.append(X(name='x.',at=i*5))
#        x[i+1].activate(at=i*5,proc=x[i+1].action())
        x[i+1].enter(q)
        
    x[6].suppress_trace(True)
    i=0
    for c in q:
        print (c._name)
        i=i+1
        if i==4:
            x[1].leave(q)
            x[5].leave(q)
            x[6].leave(q)
        
    y=Y(name='y')
#    y.activate(at=20)
    env.run(till=35)

#    env.run(4)
    
def test2():
    de=sim.Environment()
    print('test2')
    x=[None]
    q=[None]
    for i in range(5):
        x.append(sim.Component(name='x.'))
        q.append(sim.Queue(name='q.'))
    y=sim.Component(name='y')
    x[1].enter(q[1])
    y.enter(q[1])
    x[1].enter(q[2])
    x[2].enter(q[2])
    x[2].enter(q[1])
    x[3].enter(q[2])
    q[1].print_statistics()

    q[2].print_statistics()
    q[1].union(q[2],'my union').print_statistics()

    q[1].difference(q[2],'my difference').print_statistics()
    q[1].intersect(q[2],'my intersect').print_statistics()
    q[1].copy('my copy').print_statistics()    
#    q[1].move('my move').print_statistics()
    q[1].print_statistics()

    print (q[1])
    
    yy=q[1].component_with_name('y')
    ii=q[1].index(y)
    print(yy,ii)
    
    
def sample_and_print(dist,n):
    s=[]
    
    for i in range(n):
        s.append(dist.sample())
    print ('mean=',dist.mean(),'samples', s)
    
def test3():
    print('test3')
    
    sim.Environment(random_seed=1234567)
    print('string')
    d=sim.Distribution('Exponential (1000)')
    sample_and_print(d,5)
    sim.random_seed(1234567)
    sample_and_print(d,5)
    sim.random_seed(None)
    sample_and_print(d,5)
    
    print('triangular')
    tr=sim.Triangular(1,5,3)
    sample_and_print(tr,5)

    print('uniform')
    u=sim.Uniform(1,1.1)
    sample_and_print(u,5)
    print('constant')
    c=sim.Constant(10)
    sample_and_print(c,5)

    print('normal')
    n=sim.Normal(1,2)
    sample_and_print(n,5)
    sample_and_print(n,5)

    print('cdf')
    cdf=sim.Cdf((1,0,2,25,2,75,3,100))
    sample_and_print(cdf,5)
    sample_and_print(cdf,5)

    print('pdf')
    pdf=sim.Pdf((1,2),1)
    sample_and_print(pdf,5)

    print('pdf 1')
    pdf=sim.Pdf((sim.Uniform(10,20),10,sim.Uniform(20,30),80,sim.Uniform(30,40),10))
    sample_and_print(pdf,5)  
    
    print('pdf 2')
    pdf=sim.Pdf((sim.Uniform(10,20),sim.Uniform(20,30),sim.Uniform(30,40)),(10,80,10)) 
    sample_and_print(pdf,5)  

    print('pdf 3')
    pdf=sim.Pdf(('red','green',1000),(10,1,10))
    sample_and_print(pdf,5)  

def test4():
    print('test4')
    class X(sim.Component):
        def process(self):
            yield self.hold(10)
            yield self.request(res,4)
            yield self.hold(20)
            res.requesters().print_statistics()
            res.claimers().print_statistics()
            for i in range(1):
                self.release(res,4)
    
    class Y(sim.Component):
        def process(self):
            yield self.hold(11)
            yield self.request(res,1,priority=1-self.i)
            if self.request_failed():
                pass
            else:
                yield self.hold(1)
                self.release(res)

    class Z(sim.Component):
        def process(self):
            yield self.hold(20)
            y[4].reschedule()
            res.capacity(2)
            
    de=sim.Environment()
    res=sim.Resource(name='res.',capacity=4)
    res.x=0
    x=X(name='x')
    y=[0]
    for i in range(6):
        c=Y(name='y.')
        c.i=i
        y.append(c)

    z=Z(name='z')
    env.run(till=1000)
    
def test5():
    print('test5')
    
    class X1(sim.Component):
        
        def process(self):
            while True:
                while True:
                    yield self.request(r1,2,5,r2,greedy=True,fail_at=de.now()+6)
                    if not self.request_failed()():
                        break
                yield self.hold(1)
                self.release(r1,r2)
                yield self.passivate()
    class X2(sim.Component):
        
        def process(self):
            while True:
                yield self.request((r1,3),(r2,1,1))
                yield self.hold(1)
                self.release(r1)
                yield self.passivate()
    class X3(sim.Component):
        
        def process(self):
            while True:
                yield self.request(r1,r2)
                yield self.hold(1)
                self.release(r1,r2)
                yield self.passivate()
            
    class Y(sim.Component):
        
#        def __init__(self,*args,**kwargs):
#            sim.Component.__init__(self,*args,**kwargs)
            
        def process(self):
            yield self.hold(3)
            x1.cancel()
            yield self.hold(10)
            r2.capacity(1)
            pass

            
                        
    de=sim.Environment(trace=True)
    q=sim.Queue(name='q')
    r1=sim.Resource(name='r1',capacity=3)
    r2=sim.Resource(name='r2',capacity=0)    
    r3=sim.Resource(name='r3',capacity=1)  
      
    x1=X1()
    x2=X2()
    x3=X3()

        
    y=Y(name='y')
    env.run(till=21)    
    
def test6():
    print('test6')
    class X(sim.Component):
        def process(self):
            yield self.passivate()
            yield self.hold(1)
            
    de=sim.Environment(trace=True)
    x=X()
    print (x.status()())
    q=sim.Queue(name='Queue.')
    q.name('Rij.')
    print (q.name())
    q.clear()
    env.run(till=10)
    x.reactivate()
    env.run()
    
def test7():
    print('test7')

    class X1(sim.Component):
        def process(self):
            yield self.request(r1,5,r2,2,greedy=True,fail_at=5)
            yield self.passivate()
    

    class X2(sim.Component):
        def process(self):
            yield self.request(r1,8,r2)
            yield self.passivate()
    
    class X3(sim.Component):
        def process(self):
            yield self.request(r1,7)
            yield self.passivate()
    

    de=sim.Environment(trace=True)
    
    x1=X1()
    x2=X2()
    x3=X3()
    
    X4=sim.Component()
    
    r1=sim.Resource(capacity=10,anonymous=True)    
    r2=sim.Resource()    
    r3=sim.Resource()    
    
    q={}
    for i in range(1,5):
        q[i]=sim.Queue()
        
    x1.enter(q[1])    
    x1.enter(q[2])    
    x1.enter(q[3])   
    
    x2.enter(q[1])    
    x3.enter(q[1])    
    
    
        
    env.run(10)
    r2.capacity(2)
    env.run(20)

    print(sim.default_env)

    print(x1)
    print(x2)
    print(x3)

    print (q[1])
    print (q[2])
    print (q[3])
    print (q[4])
    
    print(r1)
    print(r2)
    print(r3)
    
    d=sim.Exponential(10)
    print(d)
    print(sim.Uniform(1,2))
    print(sim.Triangular(40,150,55))
    print(sim.Distribution('Constant(5)'))


        
def test8():
    print('test8')

    class AnimatePolar(sim.Animate):
        def __init__(self,r,*args,**kwargs):
            self.r=r
            super().__init__(*args,**kwargs)
            
        def x(self,t):
            tangle=sim.interpolate(t,self.t0,self.t1,0,2*math.pi)
            sint=math.sin(tangle)
            cost=math.cos(tangle)
            x,y=(100+self.r*cost-0*sint,100+self.r*sint+0*cost)
            return x
                        
        def y(self,t):
            tangle=sim.interpolate(t,self.t0,self.t1,0,2*math.pi)
            sint=math.sin(tangle)
            cost=math.cos(tangle)
            x,y=(100+self.r*cost-0*sint,100+self.r*sint+0*cost)
            return y
            
        def angle(self,t):
            return sim.interpolate(t,self.t0,self.t1,0,360)
            
        def fillcolor(self,t):
            f=sim.interpolate(t,self.t0,self.t1,0,1)
            if f<0.5:
                return sim.colorinterpolate(f,0,0.5,sim.colorspec_to_tuple('red'),sim.colorspec_to_tuple('blue'))
            else:
                return sim.colorinterpolate(f,0.5,1,sim.colorspec_to_tuple('blue'),sim.colorspec_to_tuple('green'))
        
        def text(self,t):
            angle=sim.interpolate(t,self.t0,self.t1,0,360)
            return '{:3.0f}'.format(angle)

            
    class X(sim.Component):
        def slideraction(self):
            print ('value='+str(self.myslider.v))
            
        def process(self):
            
            AnimatePolar(r=100,text='A',t1=10)            
            
            x=0
            for fontsize in range(8,30):
                sim.Animate(x0=x,y0=height-100,text='aA1',font=('Calibri,calibri'),fontsize0=fontsize)
                x+=fontsize*2
            x=0
            for fontsize in range(8,30):
                sim.Animate(x0=x,y0=height-200,text='aA1',font='CabinSketch-Bold',fontsize0=fontsize)
                x+=fontsize*2
            
                                    
            self.rx=sim.Animate(x0=600,y0=300,linewidth0=1,
                            rectangle0=(-200,-200,200,200),t1=10,fillcolor0='green#7f',angle1=0)
            self.rx=sim.Animate(x0=500,y0=500,linewidth0=1,line0=(-500,0,500,0),t1=10,fillcolor0='black')
            self.rx=sim.Animate(x0=500,y0=500,linewidth0=1,line0=(0,-500,0,500),t1=10,fillcolor0='black')

            self.rx=sim.Animate(x0=500,y0=500,linewidth0=10,polygon0=(0,0,100,0,100,100,50,50,0,100),offsetx1=100,offsety1=100,t1=10,fillcolor0='red#7f',angle1=360)
            self.rx=sim.Animate(x0=600,y0=300,linewidth0=1,rectangle0=(-200,-200,200,200),t1=10,fillcolor0='blue#7f',angle1=360)

#            self.t1=sim.Animate(x0=500,y0=500,fillcolor0='black',
#                text='Test text',x1=500,y1=500,t1=25,font='CabinSketch-#Bold',fontsize0=20,anchor='ne',angle1=0,fontsize1=50)


            self.i1=sim.Animate(x0=250,y0=250,offsetx0=100,offsety0=100,angle0=0,angle1=360,circle0=(20,),fillcolor0=('red',0),linewidth0=2,linecolor0='blue',circle1=(20,),t1=15)

#            self.ry=sim.Animate(x0=500,y0=300,linewidth0=1,polygon0=(-100,-100,100,-100,0,100),t1=10,fillcolor0='blue',angle1=90)

            self.i1=sim.Animate(x0=500,y0=500,angle0=0,layer=1,image='salabim.png',width0=300,x1=500,y1=500,angle1=360,t1=20,anchor='center')
    
            yield self.hold(3)
            self.i1.update(image='Upward Systems.jpg',angle1=self.i1.angle1,t1=self.i1.t1,width0=self.i1.width0)
            return
            self.myslider=sim.AnimateSlider(x=600,y=height,width=100,height=20,vmin=5,vmax=10,v=23,resolution=1,label='Test slider',action=self.slideraction) 
            
            return
            
            
            self.p1=sim.AnimatePolygon(
            x0=200,y0=200,polygon0=(-100,-100,100,-100,100,100,-100,100),
            t1=25,x1=100,y1=100,fillcolor1='red',linecolor0='blue',linewidth0=3)
            self.p2=sim.Animate(linewidth0=2,linecolor0='black',linecolor1='white',
                x0=100,y0=600,fillcolor0='green',polygon0=(-50,-50,50,-50,0,0),angle1=720,t1=8)
            self.r1=sim.Animate(layer=1,x0=500,y0=500,rectangle0=(0,0,100,100),fillcolor0='yellow',linecolor0='red',linewidth0=2,angle1=180,t1=10)
            self.t1=sim.Animate(x0=200,y0=200,fillcolor0='black',
                text='Test text',x1=100,y1=100,anchor='center',t1=25,font='courier',fontsize1=50)
            self.r2=sim.Animate(rectangle0=(-5,-5,5,5))
            
            i=0
            for s in ['ne','n','nw','e','center','w','se','s','sw']:
                sim.Animate(x0=200,y0=200,text=s,t0=i,t1=i+1,anchor=s,keep=False,fillcolor0='red')
                i=i+1

            self.p2=sim.Animate(x0=500,y0=500,line0=(0,0,100,100),angle1=360,t1=10,linecolor0='red',linewidth0=5)
            self.r2=sim.Animate(x0=300,y0=700,rectangle0=(-300,-300,300,300),fillcolor0='',linecolor0='black', linewidth0=2)
            self.c1=sim.Animate(x0=300,y0=700,circle0=(0,),fillcolor0='blue',circle1=(60,),t1=20)
            self.i1=sim.Animate(x0=500,y0=500,angle0=0,layer=1,image='BOA.png',width0=300,x1=500,y1=500,angle1=360,t1=20,anchor='center')
#            self.i1=sim.AnimateText(text='ABCDEF',x0=500,y0=200,angle0=0,layer=1,angle1=360,t1=20,anchor='center')
            yield self.hold(10)
#            self.t1.update(color0='white',x1=100,y1=100,t1=25)
            self.r1.update()
            self.c1.update(t1=20,radius1=0)
            
    import os

    de=sim.Environment(trace=True)
    x=X()
#    s='abcdefghijk' 
    
#    size=getfontsize_to_fit(s,10000)
#    print ('--fontsize_to_fit',size)
#    print('--width-1=', getwidth(s,'',size-1))
#    print('--width  =', getwidth(s,'',size))
#    print('--width+1=', getwidth(s,'',size+1))
#    assert False

    height=768
    env.animation_parameters(modelname='Salabim test')
    env.run(15) 
    env.run(till=30)
    print('THE END')


def test9():
    print('test9')
    class X(sim.Component):
        def process(self):
            yield self.passivate(mode='One')
            yield self.passivate(mode='Two')
            yield self.passivate()
            yield self.hold(1)
        
    class Y(sim.Component):
        def process(self):
            while True:
                print('de.now()=',de.now())
                yield self.hold(1)
                print(x.mode())
                if self.ispassive():
                    x.reactivate()
                
                
    de=sim.Environment(trace=True)
    x=X()
    y=Y()
    env.run(till=6)
    
    
def test10():
    print('test10')
    for s in ('blue','','black#23','#123456','#12345678',(1,2,3),(4,5,6,7),('blue',8),('blue#67',1),('#123456',23)):
        t=sim.colorspec_to_tuple(s)
        print(s,'==>',t)
        
def test11():
    class Do1(sim.Component):
        def process(self):
            while True:
                if q1.length()==0:
                    yield self.passivate()
                print('------')
                for cc in q1:
                    print(de.now(),cc.name())
                    yield self.hold(1)
            
    class Do2(sim.Component):
        def process(self):

            c[1].enter(q1)
            c[2].enter(q1)
            if d1.ispassive():
                d1.reactivate()
            yield self.hold(till=1.5)

            c[3].enter(q1)
            c[4].enter_at_head(q1)
            if d1.ispassive():
                d1.reactivate()
                
            yield self.hold(till=20.5)
            for cc in q1:
                cc.leave(q1)
            if d1.ispassive():
                d1.reactivate()
                
    class X(sim.Component):
        pass
        
    de=sim.Environment(trace=True)
    d2=Do2()
    d1=Do1()
    
    q1=sim.Queue('q1')
    q2=sim.Queue('q2')
    c={}
    for i in range(10):
        c[i]=sim.Component(name='c'+str(i))
        c[i].enter(q2)
    x=q2.pop()
    print('x=',x)
    print('head of q1',q1.head())
    print('q1[0]',q1[0])
    print('tail of q1',q1.tail())
    print('q1[-1]',q1[-1])

    print('head of q2',q2.head())
    print('q2[0]',q2[0])
    print('tail of q2',q2.tail())
    print('q2[-1]',q2[-1])



    
    print('**c[0]=',c[0])
    c[0].enter(q1)
    c[0].set_priority(q1,10)
    print(q1)

    c[3].set_priority(q2,10)

    c[1].set_priority(q2,-1)
    c[5].set_priority(q2,10)    
    for cx in q2:
        print(cx.name())
    for cx in reversed(q2):
        print(cx.name(),cx in q1)

    print ('--')
    print(q2[-1])
    print('---')


    env.run(till=100)

def test12():
        
    class X(sim.Component):
        def process(self):
            sim.Animate(text='Piet' ,x0=100,y0=100,x1=500,y1=500,t1=10)
            while True:
                print(sim.default_env())
                yield self.hold(1)
           
    de=sim.Environment(trace=True)
    env.animation_parameters(speed=1)
    a=sim.Environment(name='piet.')
    b=sim.Environment(name='piet.')
    c=sim.Environment(name='piet.')
    print(a)
    print(b)
    print(c)    
    
    X(auto_start=False)
    X(auto_start=False)
    X(auto_start=False)
    X()       
    env.animation_parameters(speed=0.1,video='x.mp4')
    env.run(4)
    env.run(2)
    env.run(4)


def test13():
    de=sim.Environment()
    q=sim.Queue()
    for i in range(10):
        c=sim.Component(name='c.')
        q.add(c)
        
    print(q)
    for c in q:
        print (c.name())
        
    for i in range(20):
        print(i,q[i].name())

        
def test14():
    class X(sim.Component):
        def process(self):
            yield self.request(*r)
            print(self.claimed_resources())
            
    de=sim.Environment()
    X()
    r=[sim.Resource() for i in range(10)]
    de.run(till=10)
    
def test15():
    d=sim.Pdf(('r',1,'c',1))
    d=sim.Pdf((1,2,3,4) ,1) 
    print(d.mean())
    s=''
    for i in range(100):
        x=d.sample()
        s=s+str(x)
    print(s)    
        
        
def test16():
    de=sim.Environment()
    env.animation_parameters()
    a=sim.Animate(text='Test',x0=100,y0=100,fontsize0=30,fillcolor0='red')
    a=sim.Animate(line0=(0,0,500,500),linecolor0='white',linewidth0=6)
    env.run()
    
    
def test17():
    def actiona():
        bb.remove()
        sl.remove()        
    def actionb():
        ba.remove()   
        
    de=sim.Environment()     

    for x in range(10):
        for y in range(10):
            a=sim.Animate(rectangle0=(0,0,95,65),x0=5+x*100,y0=5+y*70,fillcolor0='blue',linewidth0=0)
    ba=sim.AnimateButton(x=100,y=700,text='A',action=actiona)
    bb=sim.AnimateButton(x=200,y=700,text='B',action=actionb)
    sl=sim.AnimateSlider(x=300,y=700,width=300)  
    sim.Animate(text='Text',x0=700,y0=750,font='Times NEWRomian Italic',fontsize0=30)    
    de.animation_parameters(animate=True)
    env.run(5)
    env.animation_parameters(animate=False)
    env.run(100)
    env.animation_parameters(animate=True,background_color='yellow')
    env.run(10)
    
def test18():
    for j in range(2):
        print('---')
        r=random.Random(-1)
        r1=random.Random(-1)
        d=sim.Exponential(3,r1)
        sim.Environment(random_seed=-1)
        for i in range(3):
            print(sim.Exponential(3,r).sample())
            print(sim.Exponential(3).sample())
            print(d.sample())
    
def test19():
    sim.show_fonts()    
    
def test20():
    de=sim.Environment()     
    y=650
    if Pythonista:
        for t in ('TimesNewRomanPSItalic-MT','Times.NewRoman. PSItalic-MT',
          'TimesNewRomanPSITALIC-MT','TimesNoRomanPSItalic-MT'):
            sim.Animate(text=t,x0=100,y0=y,font=t,fontsize0=30,anchor='w')
            y=y-50
    else:
        for t in ('Times New Roman Italic','TimesNEWRoman   Italic','Times No Roman Italic','timesi','TIMESI'):
            sim.Animate(text=t,x0=100,y0=y,font=t,fontsize0=30,anchor='w')
            y=y-50
        
    de.animation_parameters(animate=True)
    env.run()
    
    
def test21():
#    d=sim.Pdf((sim.Uniform(10,20),10,sim.Uniform(20,30),80,sim.Uniform(30,40),10))
    d=sim.Pdf((sim.Uniform(10,20),sim.Uniform(20,30),sim.Uniform(30,40)),(10,80,10))


    for i in range(20):
        print (d.sample())

def test22():
    
    class X(sim.Component):
        def process(self):
            yield self.hold(10)

    class Y(sim.Component):
        def process(self):
            while True:
                yield self.hold(1)
                print('status of x=',env.now(),x.status()())
        
    de=sim.Environment()
    x=X()
    Y()

    env.run(12)
    
def test23():
    sim.a=100
    for d in ('uni(12,30)','n(12)','exponentia(a)','TRI(1)','(12)','12','  (  12,  30)  ','a'):
        print(d)
        print(sim.Distribution(d))
    

if __name__ == '__main__':
    test()
