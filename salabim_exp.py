import salabim as sim
import math
import random
import string
import time
import logging
import inspect
import types
import itertools
import os
import platform
from ycecream import yc
import numpy as np
import datetime

Pythonista = platform.system() == "Darwin"

def exp():
    exp184()

def exp184():
    class X(sim.Component):
        def process(self):
            for i in range(4):
                mon.tally(i)
                yield self.hold(1)

    env = sim.Environment()
    mon=sim.Monitor("mon", level=True)
    X()
    env.run()
    print(env._now)
    print(mon.xt())

def exp183():
    import salabim as sim
    import datetime

    def action(v):
        v_as_datetime = datetime.datetime(2022,1,1) + datetime.timedelta(days=int(v))
        an0.label(f"{v_as_datetime:%Y-%m-%d}")

    env = sim.Environment()    
    an0 = sim.AnimateSlider(x=100, y=100, action=action, width=500, height=30, v=30, vmin=0, vmax=365, resolution=1, fontsize=12,show_value=False)

    an1=sim.AnimateSlider(x=100, y=200, width=500, height=30, vmin=0, vmax=365, resolution=1, fontsize=12,show_value=True,foreground_color="red", label="label")
    an2=sim.AnimateSlider(x=100, y=300, width=500, height=30, vmin=0, vmax=365, resolution=1, fontsize=12,show_value=True,background_color="red", foreground_color="white", trough_color="blue", label="label")

    env.animate(True)


    env.run(sim.inf)


    
def exp182():
    env = sim.Environment()    
    an0 = sim.AnimateLine(spec=(1,2,3,4),x=8)
    an1 = sim.AnimateCircle(radius=5)
    an2 = sim.AnimateText('ab',x=9)
    an = sim.AnimateCombined((an0, an1, an2))
    print(an.x(env.now()))


def exp181():
    env = sim.Environment()

    class X(sim.Component):
        def process(self):
            m.tally(1)
            yield self.hold(1)
            m.tally(2)



    env.animate(True)
    m = sim.Monitor("m", level=True)
    X()
    sim.AnimateText(x=10, y=100, text=lambda:f"mean={m.mean():6.3f}")

    env.run(10)
    print(m.mean())

def exp180():
    env = sim.Environment(trace=True)
    
    class X(sim.Component):
        def process(self):
            yield self.hold(5)
            print('xx')
            yield 1
            print('yy')
            yield self.hold(1)
            print('+++')
        
    class Y(sim.Component):
        def process(self):
            yield self.passivate()
            
    x = X()
    y = Y()
    env.run()
        
    
def exp179():
    class X(sim.Component):
        def process(self):
            yield self.hold(5)

    env=sim.Environment()
    x=X()
    sim.AnimateRectangle((100,100,200,50), text=lambda t: f"{t:5.1f}",parent=x)
    env.animate(True)
    env.run(1000)
    print("end")



def exp178():
    env = sim.Environment()
    m1 = sim.Monitor('m1')
    m2 = sim.Monitor('m2',level=True)
    for t in range(5):
        print(env.now(), m1.start, m2.start, m2.tx()[0][0])
        env.run(10)
#        m1.reset()
#        m2.reset()
        env.reset_now()
        
        

def exp177():
    class Machine(sim.Component):
        def setup(self, y, color):
            self.color = color
            sim.AnimateRectangle(spec=(0,0,50,50), x=100, y=y, text=self.name(), fillcolor=lambda arg, t: arg.color, arg=self)

        def process(self):
            yield self.hold(5)
            self.color='red'

    class Ticker(sim.Component):
        def process(self):
            while True:
                print(env.now())
                yield self.hold(1)

    env=sim.Environment()
    Machine(color="blue", y=100, at=0)
    Machine(color="green", y=200, at=1)
    Machine(color="yellow", y=300, at=2)
    Machine(color="orange", y=400, at=3)
    Ticker()
    env.animate(True)
    try:
        env.run(10000)
    except sim.SimulationStopped:
        print("exception")
    env.run(10000)
    print("end")


def exp176():
    class X(sim.Component):
        def animation_objects(self, id):
            if id==1:
                an0 = sim.AnimateRectangle(spec=(-30,-30,30,30), offsety=-30, text=self.name(), fillcolor="blue")
                return 70,70,an0
            else:
                an0 = sim.AnimateRectangle(spec=(-30,-30,30,30), offsety=-30, text=self.name(), fillcolor="green", visible=lambda t: int(t%2)==0)
                an1 = sim.AnimateCircle(radius=20,text=self.name(), offsety=-30, fillcolor="red", visible=lambda t: int(t%2)==1)
                return lambda t: 70 if (int(t)%2)==0 else 45,lambda t: 70 if (int(t)%2)==0 else 45 , an0,an1

        def process(self):
            self.enter(q)
            yield self.hold(sim.Uniform(5,10))
            self.leave(q)

    class Y(sim.Component):
        def process(self):
            yield self.hold(8)
            an_q_length.remove()
            an_q.remove()
            yield self.hold(8)
            an_q_length.show()
            an_q.show()

    env = sim.Environment()
    q=sim.Queue('q')
    an_q = sim.AnimateQueue(q, x=lambda t: 100+ 10*t, y=100, direction= lambda t: 'e' if int(t%2)==0 else 'n', keep=lambda t: not (4<t<5))
    an_q1 = sim.AnimateQueue(q, x=1000, y=200, direction= 'w', id=1)


    sim.ComponentGenerator(X, iat=sim.Uniform(1,2))
    Y()

    sim.AnimateText("This is a text", font="Calibri", fontsize=25,x=100, y=300)
    an_q_length=sim.AnimateMonitor(q.length, x=100,y=400, width=900, height=200, horizontal_scale=10, vertical_map=lambda x: float(x), keep=lambda t: not (4<t<5))
    env.animate(True)


    env.run(1000)

def exp175():

    env = sim.Environment()
    env.animate(True)
    env.modelname("test")

    an=sim.Animate(line0=(0,0,300,300), line1=(1000,700,0,0), t0=3, t1=2211, linecolor0="green", linewidth0=7, keep=True)

    an1 = sim.AnimateText("an1", x=100, y=700, angle=lambda t:0*t)
    an2 = sim.AnimateText("an2", x=100, y=600)
    an3 = sim.Animate(text="an3", x0=100, y0=500)
    an1.abc=12
    an2.abc=12
    anc=sim.AnimateCombined((an1,an2), textcolor="red")
    an3.update(textcolor0="red")
    an.update(linecolor0="red")
    env.run(4)
    env.modelname("")
    env.run(till=8)
    env.modelname("xxxxxxx")
    anc.remove()
    an3.remove()
    an.remove()
    env.run(till=12)
    anc.show()
    an3.show()
    an.show()
    env.run(till=14)
#    an.remove()
    an1.remove()
#    an1.show()
    env.run(till=16)
#    an.show()
    an1.show()
    print(an1._image_visible)


    env.run(10000)



def exp174():
    class MyAnimateRectangle(sim.AnimateRectangle):
        def fillcolor(self,t):
            return "red"

    env = sim.Environment()
    env.animate(True)
    env.animate_debug(True)

    sim.AnimateRectangle((100,100,200,200),x=lambda t: 100+10*t,text="This is a rectangle")
    ao1=MyAnimateRectangle((500,500,600,600),x=lambda t: 100+10*t,text=lambda arg,t:f"This is a rectangle {t:3.1f}")
    ao2=MyAnimateRectangle((0,0,100,100),x=lambda t: 100+10*t, y=600, text=lambda arg,t:f"This is also rectangle{arg.abc}{t:3.1f}", fillcolor="orange", textcolor="blue", keep=lambda t: t<4 or t>6)
    ao2.abc='abc'
    sim.AnimateCircle(radius=50, radius1=100, angle=lambda t:45+5*t, x=400,y=400, linecolor='blue', arc_angle0=90, draw_arc=True, fillcolor="")
    sim.AnimatePoints((100,600, 150,600,200,650,250,600), as_points=lambda t: int(t % 2)==0, linewidth=7, linecolor="blue")
    sim.AnimateLine((0,0,500,500), x=lambda t: 100+10*t,text="This is a line")
    ao3= sim.AnimateText(lambda t: f"this is a text {t}", x=100, y=500)

    x0=800
    y0=500
    sim.AnimateImage('transparent.png',x=x0,y=y0, textcolor="red", fontsize=40, angle=lambda t: 10*t, anchor="c")
    sim.AnimateLine((-100,0,100,0), x=x0, y=y0,linecolor="red")
    sim.AnimateLine((0,-100,0,100), x=x0, y=y0,linecolor="red")

    sim.AnimatePolygon((10,50, 50,50, 50,10,100,100, 0,400), x=lambda t:10*t, angle=lambda t:5*t)
    sim.Animate(text="Hallo", x0=0, y0=0, x1=1000, y1=700, t0=4, t1=10, keep=False)

    sim.Animate(image='transparent.png',x0=100,y0=50)
    env.modelname("ab")

    sim.Animate(polygon0=(50,50,1000,23), polygon1=(300,10,0,560),linewidth0=10,t1=10)
    sim.Animate(circle0=12, circle1=100, x0=400, y0=100,t1=10,fillcolor0="orange")

    env.run(8)

    ao2.show()
    ao1.fillcolor="green"
    ao1.spec=(400,400,500,500)
    ao1.textcolor='blue'

    env.run(4)
    ao1.remove()
    env.run(10000)


def exp173():
    class X(sim.Component):
        def process(self):
            v0 = v1 = 10
            while True:
                v0 = max(0, min(500, v0 + sim.Uniform(-1, 1)() * 10))
                level_monitor.tally(v0)
                v1 = max(0, min(500, v1 + sim.Uniform(-1, 1)() * 10))
                non_level_monitor.tally(v1)
                yield self.hold(1)
                print(env.now())

    env = sim.Environment()
    env.animate(True)
    env.speed(8)

    level_monitor = sim.Monitor("level_monitor", level=True)
    non_level_monitor = sim.Monitor("non_level_monitor")
    X()
    sim.AnimateMonitor(
        level_monitor,
        linewidth=3,
        x=100,
        y=100,
        width=900,
        height=250,
        vertical_scale=lambda arg, t: min(50, 250 / arg.monitor().maximum()),
        labels=lambda arg, t: [i for i in range(0, int(arg.monitor().maximum()), 10)],
        horizontal_scale=lambda t: min(10, 900 / t),
    )
    sim.AnimateMonitor(
        non_level_monitor,
        linewidth=5,
        x=100,
        y=400,
        width=900,
        height=250,
        vertical_scale=lambda arg, t: min(50, 250 / arg.monitor().maximum()),
        labels=lambda arg, t: [i for i in range(0, int(arg.monitor().maximum()), 10)],
        horizontal_scale=lambda t: min(10, 900 / t),
    )
    env.run()


def exp172():
    class X(sim.Component):
        def process(self):
            while True:
                v = sim.IntUniform(0, 5)() * 10
                m.tally(v)
                m1.tally(v)
                yield self.hold(1)

    env = sim.Environment()
    env.animate(True)
    m = sim.Monitor("m", level=True)
    m1 = sim.Monitor("m1")
    X()
    #    sim.AnimateMonitor(m, title="abc")
    #    sim.AnimateMonitor(m, title=lambda t: f"def({t})")
    #    a=sim.AnimateMonitor(m, title=lambda arg, t: f"ghi({arg.hallo}, {t})",arg=s, width=lambda t:1000-51*t, height=300,x=lambda t: 40 * t, fillcolor=lambda t: "red" if t<5 else "blue")
    #    a=sim.AnimateMonitor(m, title=lambda arg, t:f"TITLE {t}", width=lambda t:1000-51*t, height=300,x=lambda t: 40 * t)
    a = sim.AnimateMonitor(
        m,
        visible=lambda t: int(t) % 2,
        angle=lambda t: t,
        title=lambda arg, t: f"TITLE {t:5.2f}",
        labels=(0, 10, 20, 30, 40, 50),
        x=100,
        width=900,
        height=250,
        vertical_scale=5,
        horizontal_scale=10,
        nowcolor=lambda t: "red" if t < 5 else "blue",
    )
    #    a=sim.AnimateMonitor(m1, title=lambda arg, t:f"TITLE {t}", y=lambda t:350+10*t,width=1000,  height=300, horizontal_scale=lambda t:10+t,nowcolor=lambda t: "red" if t<5 else "blue")

    env.run(10)
    a.labels = labels = (0, 25, 50)
    env.run(10)
    a.labels = labels = (0, 16, 32, 50)
    env.run(10)
    a.remove()
    env.run(1000)


def exp171():
    env = sim.Environment(datetime0=datetime.datetime(2022, 1, 1), trace=True, time_unit="days")
    #    env=sim.Environment(datetime0=False, trace=True, time_unit="days")
    print(env._time_unit)
    env.run(2)
    print(env.time_to_str(env.now()) + "|")
    print(env.time_to_str(sim.inf) + "|")
    print(env.duration_to_timedelta(4))
    env.reset_now()

    class WorkLoadGenerator(sim.Component):
        def process(self):
            with open("workload.txt", "r") as f:
                for line in f.readlines():
                    workload_date_str = line[:19]
                    workload_datetime = datetime.datetime.strptime(workload_date_str, "%Y-%m-%d %H:%M:%S")
                    yield self.hold(till=env.datetime_to_t(workload_datetime))
                    # generate workload

    env = sim.Environment(datetime0=True, trace=True)
    WorkLoadGenerator()
    env.run()

    env = sim.Environment(time_unit="days", datetime0=datetime.datetime(2022, 4, 29))
    env.trace(True)
    env.run(1)  # this is one day


def exp170():
    class X(sim.Component):
        def process(self):
            def solve():
                if False:
                    yield from solve()

            yield from solve()
            env.main().activate()

    env = sim.Environment()
    env.animate(True)
    env.synced(False)

    X()
    env.run(sim.inf)

    env.animate(True)
    env.synced(True)
    env.run(sim.inf)


def exp169():
    class X(sim.Component):
        def process(self):
            while True:
                yield self.hold(1)

    env = sim.Environment()
    env.animate(True)
    env.trace(True)
    env.synced(False)
    X()
    env.run(sim.inf)


def exp168():
    class X(sim.Component):
        def process(self):
            while True:
                yield self.hold(1)

    class Interrupter(sim.Component):
        def process(self):
            while True:
                yield self.hold(4)
                x.interrupt()
                yield self.hold(1)
                x.resume()

    env = sim.Environment(trace=True)
    x = X()
    Interrupter()
    env.run(40)
    x.status.print_histogram(values=True)
    print(x.status.value_duration("interrupted"))


def exp167():
    class DisIter(sim._Distribution):
        def __init__(self, iterable, env=None):
            self.iterable = iter(iterable)

        def sample(self):
            sample = next(self.iterable, None)
            if sample is None:
                raise ValueError("iterable exhausted")
            return sample

    class X(sim.Component):
        def process(self):
            yield self.hold(20)

    class Y:
        pass

    env = sim.Environment(trace=True)
    sim.ComponentGenerator(X, iat=10, disturbance=sim.Uniform(1), till=50, force_at=True)
    #    sim.ComponentGenerator(X, iat=DisIter([1,1,1,1,1]), disturbance=0.3,cap_now=True)
    env.run(100)


def exp166():
    class X(sim.Component):
        def process(self):
            for i in range(100):
                for over3d in (False, True):
                    sim.AnimateText(text=str(i), x=200, y=i * 20, textcolor="green", visible="not in video", over3d=over3d)
                    sim.AnimateText(text=str(i), x=100, y=i * 20, textcolor="red", visible="only in video", over3d=over3d)
                yield self.hold(1)

    env = sim.Environment()
    X()

    env.animate(True)
    env.animate3d(True)
    env.position3d((1025, 0))

    env.view(x_eye=-529.7288, y_eye=-550.3268, z_eye=393.4118, x_center=50.0000, y_center=50.0000, z_center=0.0000, field_of_view_y=10.0000)  # t=9.9491
    sim.Animate3dBox(x_len=lambda t: 10 + t, y_len=10, z_len=10, x=0, y=0, z=0, x_ref=1, y_ref=1, z_ref=1, color="red", shaded=True, visible="only in video")
    sim.Animate3dBox(
        x_len=lambda t: 10 + t, y_len=10, z_len=10, x=0, y=0, z=0, x_ref=-1, y_ref=-1, z_ref=-1, color="green", edge_color="white", visible="not in video"
    )

    sim.AnimateCircle(
        radius=6,
        fillcolor="red",
        text="REC",
        text_offsetx=22,
        textcolor="fg",
        font="mono",
        x=-35,
        y=-22,
        xy_anchor="ne",
        visible=lambda: ((time.time() % 1 < 0.5) and env.is_videoing() and "not in video"),
    )
    with env.video(""):
        print(env.is_videoing())
        env.run(3)
        env.video_mode("3d")
        env.run(3)


def exp165():
    class X(sim.Component):
        def process(self):
            yield self.hold(10)

    sim.can_animate3d()


    env = sim.Environment(trace=False)
    env.background3d_color("orange")
    x=X()


    #    env.animation3d_init()
    do_animate = True
    do_animate3d = True

    env.x0(0)
    env.x1(380)
    env.y0(0)

    env.width3d(950)
    env.height3d(768)
    env.position3d((0, 100))
    env.background_color("black")
    env.width(950)
    env.height(768)
    env.position((960, 100))

    env.animate(do_animate)
    env.animate3d(do_animate)
    env.show_fps(True)
    sim.Animate3dGrid(x_range=range(0, 101, 10), y_range=range(0, 101, 10))

    env.view.x_eye = -100
    env.view.y_eye = -100
    env.view.z_eye = 100
    env.view.x_center = 50
    env.view.y_center = 50
    env.view.z_center = 0
    env.view.field_of_view_y = 50

    env.show_camera_position()
    #    env.camera_control()

    sim.Animate3dSphere(x=60, y=60, z=60, radius=10, number_of_slices=32, parent=x)

    sim.Animate3dRectangle(x0=10, y0=10, x1=40, y1=40, z=-20, color="yellow")
    sim.Animate3dLine(x0=0, y0=0, z0=0, x1=50, y1=50, z1=50, color="purple")

    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=40, y1=10, z1=10)
    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=40, z1=10)
    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=10, z1=40)
    sim.Animate3dBar(x0=10, y0=10, z0=40, x1=10, y1=10, z1=10)

    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=40, z1=10)
    sim.Animate3dBar(x0=40, y0=40, z0=10, x1=40, y1=10, z1=10)
    sim.Animate3dBar(x0=40, y0=40, z0=10, x1=10, y1=40, z1=10)

    sim.Animate3dBar(x0=10, y0=10, z0=40, x1=40, y1=10, z1=40)
    sim.Animate3dBar(x0=10, y0=10, z0=40, x1=10, y1=40, z1=40)
    sim.Animate3dBar(x0=40, y0=40, z0=40, x1=40, y1=10, z1=40)
    sim.Animate3dBar(x0=40, y0=40, z0=40, x1=10, y1=40, z1=40)

    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=10, z1=40)
    sim.Animate3dBar(x0=10, y0=40, z0=10, x1=10, y1=40, z1=40)
    sim.Animate3dBar(x0=40, y0=10, z0=10, x1=40, y1=10, z1=40)
    sim.Animate3dBar(x0=40, y0=40, z0=10, x1=40, y1=40, z1=40)

    sim.Animate3dCylinder(x0=0, y0=50, z0=0, x1=0, y1=50, z1=40, number_of_sides=8, radius=10, show_lids=False, color="green")

    sim.Animate3dBox(x_len=10, y_len=10, z_len=10, x=0, y=0, z=0, x_ref=1, y_ref=1, z_ref=1, color="red", shaded=True)
    sim.Animate3dBox(x_len=10, y_len=10, z_len=10, x=0, y=0, z=0, x_ref=-1, y_ref=-1, z_ref=-1, color="blue", edge_color="white")

    env.view(x_eye=-102.59501523905122, y_eye=-97.35929330786617, z_eye=100, x_center=50, y_center=50, z_center=0, field_of_view_y=10)  # t=1.665048599243164
    env.camera_auto_print(True)
    env.camera_move(
        """\
view(x_eye=-102.5950,y_eye=-97.3593,z_eye=100.0000,x_center=50.0000,y_center=50.0000,z_center=0.0000,field_of_view_y=10.0000)  # t=0.0000
view(field_of_view_y=11.1111)  # t=4.5963
view(field_of_view_y=12.3457)  # t=4.7949
view(field_of_view_y=13.7174)  # t=4.9926
view(field_of_view_y=15.2416)  # t=5.1239
view(field_of_view_y=16.9351)  # t=5.3295
view(field_of_view_y=18.8168)  # t=5.5006
view(field_of_view_y=20.9075)  # t=5.6818
view(field_of_view_y=23.2306)  # t=5.8401
view(field_of_view_y=25.8117)  # t=5.9804
view(field_of_view_y=28.6797)  # t=6.1807
view(field_of_view_y=31.8664)  # t=6.3549
view(field_of_view_y=35.4071)  # t=6.6974
view(field_of_view_y=39.3412)  # t=6.9483
view(field_of_view_y=43.7124)  # t=7.3397
view(x_eye=-105.1435,y_eye=-94.6737)  # t=8.3734
view(x_eye=-107.6448,y_eye=-91.9440)  # t=8.8074
view(x_eye=-110.0981,y_eye=-89.1711)  # t=9.2869
view(x_eye=-112.5026,y_eye=-86.3558)  # t=9.7139
view(x_eye=-114.8576,y_eye=-83.4990)  # t=10.1206
view(x_eye=-117.1623,y_eye=-80.6015)  # t=10.5025
view(x_eye=-119.4162,y_eye=-77.6642)  # t=10.9584
view(x_eye=-121.6184,y_eye=-74.6881)  # t=11.2653
view(x_eye=-123.7684,y_eye=-71.6739)  # t=11.6096
view(x_eye=-125.8654,y_eye=-68.6227)  # t=11.8866
view(x_eye=-108.2789,y_eye=-56.7605,z_eye=100.0000)  # t=12.7295
view(x_eye=-92.4510,y_eye=-46.0844,z_eye=100.0000)  # t=13.1205
view(x_eye=-94.1062,y_eye=-43.5837)  # t=13.7187
view(x_eye=-95.7175,y_eye=-41.0544)  # t=14.1318
view(x_eye=-97.2844,y_eye=-38.4974)  # t=14.3119
view(x_eye=-98.8065,y_eye=-35.9135)  # t=14.4877
view(x_eye=-100.2832,y_eye=-33.3034)  # t=14.6567
view(x_eye=-100.2832,y_eye=-33.3034,z_eye=90.0000)  # t=15.1176
view(x_eye=-100.2832,y_eye=-33.3034,z_eye=81.0000)  # t=15.3591
view(x_eye=-100.2832,y_eye=-33.3034,z_eye=72.9000)  # t=15.7827
view(x_eye=-100.2832,y_eye=-33.3034,z_eye=65.6100)  # t=16.0167
view(x_eye=-100.2832,y_eye=-33.3034,z_eye=59.0490)  # t=16.2729
view(x_eye=-100.2832,y_eye=-33.3034,z_eye=53.1441)  # t=16.5423
view(x_eye=-100.2832,y_eye=-33.3034,z_eye=47.8297)  # t=16.8177
view(x_eye=-100.2832,y_eye=-33.3034,z_eye=43.0467)  # t=17.1245
view(x_eye=-100.2832,y_eye=-33.3034,z_eye=38.7420)  # t=17.5944
view(field_of_view_y=39.3412)  # t=19.4049
""",
        lag=1,
        offset=-3,
        enabled=True,
    )


    try:
        env.run(4)
        env.animate3d(False)
        env.background3d_color("blue")

        env.run(4)
        env.animate3d(True)

        env.run(sim.inf)
    except sim.SimulationStopped:
        pass


def exp164():
    class MyEnvironment(sim.Environment):
        def print_trace(self, s1="", s2="", s3="", s4="", s0=None, **kwargs):

            if s1:
                self.last_s1 = s1
            else:
                s1 = self.last_s1 if hasattr(self, "last_s1") else ""
            super().print_trace(s1=s1, s2=s2, s3=s3, s4=s4, s0=s0, **kwargs)

    class FollowComponent(sim.Component):
        def animation_objects(self, id):
            if id == follow_queue:
                an = sim.AnimateRectangle(
                    (0, 0, 200, 20),
                    text=lambda arg, t: f"{self.name()}|{self.line_number()}|{self.status()}",
                    text_anchor="sw",
                    fillcolor="red",
                    textcolor="white",
                    font="narrow",
                )
                return 210, 25, an
            else:
                return super().animation_objects(id)

    class X1(FollowComponent):
        def process(self):
            while True:
                yield self.hold(1, mode="mode!")
                yield self.hold(2)
                if env.now() > 20:
                    break

    class X2(FollowComponent):
        def process(self):
            yield self.hold(2.5)
            while True:
                yield self.hold(2)
                if not x1.isdata():
                    x1.interrupt()
                yield self.hold(3)
                if x1.isinterrupted():
                    x1.resume()

    class X3(FollowComponent):
        def process(self):
            yield self.hold(5, mode="hold")
            yield self.passivate(mode="passivate!")

    class X4(FollowComponent):
        def process(self):
            while env.now() < 4:
                yield self.standby()

    env = MyEnvironment(trace=True)
    env.suppress_trace_standby(False)

    follow_queue = sim.Queue("follow_queue")
    my_q = sim.Queue("my_q")

    x1 = X1()
    x2 = X2()
    x3 = X3()
    x4 = X4()

    x1.enter(follow_queue)
    x1.enter(my_q)
    x2.enter(follow_queue)
    x3.enter(follow_queue)
    x4.enter(follow_queue)

    sim.AnimateQueue(follow_queue, x=50, y=50, direction="n", id=follow_queue)
    sim.AnimateQueue(my_q, x=400, y=50, direction="e")
    env.animate(True)

    env.run(1000)


def exp163():
    class X1(sim.Component):
        def process(self):
            m1.tally("x1.0")
            yield self.hold(2)
            m1.tally("x1.2")
            yield self.hold(2)
            m1.tally("x1.4")

    class X2(sim.Component):
        def process(self):
            yield self.hold(1)
            m2.tally("x2.1")
            yield self.hold(1)
            m2.tally("x2.3")
            yield self.hold(1)
            m2.tally("x2.4")

    class M2Spoiler(sim.Component):
        def process(self):
            yield self.hold(1.5)
            m2.monitor(False)
            yield self.hold(2)
            m2.monitor(True)

    env = sim.Environment()
    X1()
    X2()
    M2Spoiler()
    m = sim.Monitor("m", level=False)
    m.tally(45.6)
    m.tally(6)
    m.tally(5.8)
    m1 = sim.Monitor("m1", level=True, initial_tally="x1.0")
    m2 = sim.Monitor("m2", level=True, initial_tally="x2.0")
    env.run(10)
    m3 = m1.x_map(lambda x1, x2: f"({x1},{x2})", [m2])
    print(m1.xt())
    print(m2.xt())
    print(m3.xt(force_numeric=False))
    print(m.x())
    print(m.x_map(int).x())


def exp162():
    class X(sim.Component):
        def process(self):
            yield self.hold(5)
            yield self.hold(1)

    env = sim.Environment()
    env.animate(True)
    env.video("a.mp4`")
    X()
    env.run()
    print("ok")
    env.video_close()


def exp161():
    class X0(sim.Component):
        def process(self):
            yield self.request((res, 6))
            yield self.hold(10)
            self.release((res, 6))
            yield self.hold(10)

    class X1(sim.Component):
        def process(self):
            yield self.hold(1)
            yield self.request((res, 5, 1))
            yield self.hold(10)

    class X2(sim.Component):
        def process(self):
            yield self.hold(1)
            yield self.request((res, 1, 1))
            yield self.hold(10)

    env = sim.Environment(trace=True)
    res = sim.Resource("res", capacity=10, honor_only_first=True)
    X0()
    X1()
    X2()
    X2()
    X2()
    X2()
    X2()
    env.run()

    env = sim.Environment()


def exp160():
    class X(sim.Component):
        def process(self):
            while env.now() < 15:
                yield self.hold(1)
                pos = env.now() * 20
                sim.AnimateText(x=pos, y=pos, text=str(env.now()))
                if 5 <= env.now() <= 10:
                    env.animate(False)
                if env.now() >= 10:
                    env.animate(True)

    env = sim.Environment(trace=True)

    env.animate(True)
    x = X()
    try:
        env.run()
        print(x.status())

    except sim.SimulationStopped:
        pass


def exp159():
    class X(sim.Component):
        def process(self):
            yield self.hold(5)
            yield env.main().activate()
            yield self.hold(2)
            yield self.hold(3)

    class Y(sim.Component):
        def process(self):
            for i in range(20):
                yield self.hold(1)

    env = sim.Environment(trace=True)

    x = X()
    Y()
    env.run()
    print(x.status())
    x.activate()
    env.run()


def exp158():
    class X(sim.Component):
        def process(self):
            while True:
                yield self.hold(0.1)

    def action():
        env.main().activate()

    while True:
        env = sim.Environment(trace=False)
        sim.AnimateText(text=lambda: f"{env.now():10.4f}", x=100, y=100)
        sim.AnimateButton(text="reset", x=100, y=700, action=action)
        X()
        env.animate(True)
        env.run()


def exp157():
    class X(sim.Component):
        def process(self):
            while True:
                yield self.hold(10)
                print(env.main().scheduled_time())

    class Y(sim.Component):
        def process(self):
            yield self.hold(5)
            yield self.hold(15)
            env.main().activate(at=50)
            yield self.hold(till=35)
            env.main().passivate()
            yield self.hold(till=55)
            env.main().activate(at=70)

    env = sim.Environment(trace=True)
    X()
    Y()
    env.animate(True)
    env.run(40)


def exp156():
    class X(sim.Component):
        def process(self):
            try:
                self.enter(q)
            except OverflowError:
                pass

    env = sim.Environment(trace=True)
    sim.ComponentGenerator(X, iat=1)
    X()
    q = sim.Queue("q", capacity=5)
    env.run(1)
    q.capacity.value = 4
    env.run(10)
    q.capacity.value = 6
    env.run(10)
    q.print_info()
    print(q.capacity.xt())


def exp155():
    class X(sim.Component):
        def process(self):
            while True:
                print(env.now())
                yield self.hold(1)

    class DisplayMenuAtEnd(sim.Component):
        def process(self):
            print("1")
            env.an_menu()
            print("2")

    env = sim.Environment()
    run_time = 5
    DisplayMenuAtEnd(at=run_time, priority=1)
    X()
    env.animate(True)
    env.run(run_time)


def exp154():
    class Part(sim.Component):
        def process(self):
            while 1:
                yield self.d

            pass

    class Interrupter(sim.Component):
        def process(self):
            while True:
                yield self.hold(interrupt_iat)

    number_of_machines = 3
    interrupt_iat = 10
    env = sim.Environment(trace=True)
    machines = [sim.Resource("machine.", capacity=2) for _ in range(number_of_machines)]
    Interrupter()
    sim.ComponentGenerator(Part, iat=4)
    env.run(50)


def exp153():
    class X(sim.Component):
        def process(self):
            yield self.wait([c1.state, c2.state])

    class C(sim.Component):
        def setup(self):
            self.state = sim.State("state", False)

        def process(self):
            self.state.set()

    env = sim.Environment(trace=True)
    c1 = C(at=3)
    c2 = C(at=5)
    X()
    env.run()


def exp152():
    class Normal(sim.Component):
        def process(self):
            yield self.request(env.res)
            yield self.hold(1)

    class Emergency(sim.Component):
        def process(self):
            yield self.request((env.res, 1, -self.sequence_number()))
            yield self.hold(1)

    env = sim.Environment(trace=True)
    env.res = sim.Resource("res", capacity=0)
    Normal(at=1)
    Emergency(at=2)
    Normal(at=3)
    Emergency(at=4)

    env.run(10)
    env.res.set_capacity(1)
    env.run()


def exp151():
    class X(sim.Component):
        def greedy_request(self, resource, quantity):
            prio = env.now()
            for _ in range(quantity):
                yield self.request((res, 1, prio))

        def process(self, n):
            yield from self.greedy_request(res, n)
            self.release(res)

    env = sim.Environment(trace=True)
    res = sim.Resource("res", 10)
    print(res.occupancy.value)
    X(n=10)
    X(n=1)
    env.run()


def exp150():
    class X(sim.Component):
        def process(self):
            while True:
                delta = sim.Uniform(-1, 2)()
                env.mon_delta.tally(delta)
                env.mon_total.value += delta
                yield self.hold(1)

    env = sim.Environment()
    env.animate(True)
    env.mon_total = sim.Monitor("total", level=True)
    env.mon_delta = sim.Monitor("delta", level=True)
    an_total = env.mon_total.animate(width=950, height=200, x=30, y=10, horizontal_scale=10, vertical_offset=0, vertical_scale=10, labels=range(0, 21, 5))
    env.mon_delta.animate(
        width=950,
        height=200,
        x=30,
        y=10,
        horizontal_scale=10,
        vertical_offset=100,
        vertical_scale=10,
        labels=range(-10, 11, 5),
        label_offsetx=955,
        label_anchor="w",
        label_color="red",
        linecolor="red",
        titlecolor="red",
        title="            delta",
    )
    X()
    env.run(10)
    an_total.remove()
    an_total = env.mon_total.animate(width=950, height=200, x=30, y=10, horizontal_scale=10, vertical_offset=-50, vertical_scale=10, labels=range(5, 26, 5))
    env.run()


def exp149():

    components = {}

    class RegisterComponent(sim.Component):
        def __init__(self, name=None, *args, **kwargs):
            if name is None:
                name = type(self).__name__.lower() + "."
            super().__init__(name, *args, **kwargs)
            components[self.name()] = self

    class Car(RegisterComponent):
        pass

    env = sim.Environment()
    for i in range(5):
        Car()
    porsch0 = Car(name="Porche")
    porsche = Car(name="Porche")
    print(components)


def exp148():
    env = sim.Environment()
    env.animate(True)
    for xx in range(10):
        an = sim.AnimateRectangle(spec=lambda arg, t: (arg.xx, arg.yy, arg.xx + 10, arg.xx + t * 10)).add_attr(xx=xx * 20, yy=xx * 5)
    env.run(10000)


def exp147():
    env = sim.Environment()
    env.m = sim.Monitor()
    for value in range(101):
        env.m.tally(value)

    env.m.print_histogram()


def exp146():
    class X(sim.Component):
        def process(self):
            for value in (4, 1, 1, 3, 6, 3, 0, 7, 2, 2):
                env.ml.tally(value)
                env.m.tally(value)
                yield self.hold(1)

    env = sim.Environment()
    env.ml = Monitor()
    X()
    env.run(10)


def exp145():
    env = sim.Environment()

    mon = sim.Monitor()
    for value in (1, 2, 3, 1, 2, 3, 6, 0, 4, 7):
        mon.tally(value)
    x_np = np.array(mon.x())
    print(x_np)
    for q in range(0, 101, 1):
        s = ""
        for interpolation in "linear lower higher midpoint nearest".split():
            s += f"{mon.percentile(q, interpolation=interpolation):6.3f} {np.percentile(x_np, q, interpolation=interpolation):6.3f}    "
        #            s+=f'{mon.percentile(q, interpolation=interpolation):6.3f}    '
        print(f"{q:5.0f}%  {s}")

    mon = sim.Monitor()
    for value in (2, 3, 2, 3, 6, 0, 4, 7):
        mon.tally(value)
    mon.tally(1, weight=2)
    for q in range(0, 101, 1):
        s = ""
        for interpolation in "linear lower higher midpoint".split():
            s += f"{mon.percentile(q, interpolation=interpolation):6.3f}    "
        print(f"{q:5.0f}%  {s}")


def exp144():
    env = sim.Environment()
    env.animate(True)
    env.animate3d(True)
    sim.Animate3dBox(x_len=5, y_len=2, z_len=1, color="red", z_ref=1, z=0.5)
    sim.Animate3dBox(x_len=0.25, y_len=0.25, z_len=0.25, z=1.5, color="yellow", z_ref=1, x_ref=-19, y_ref=7)

    env.run(1000)


def exp143():
    env = sim.Environment()
    env.x0(-100)
    env.x1(100)
    env.y0(-50)
    env.animate(True)

    sim.AnimateRectangle(spec=(-1, -1, 1, 1))
    sim.AnimateRectangle(spec=(48, 48, 52, 52), fillcolor="red")

    sim.AnimateRectangle(spec=(-1, -1, 1, 1), offsetx=50, offsety=50)
    sim.AnimateCircle(radius=1, offsetx=50, offsety=50, fillcolor="yellow", angle=45)

    env.run(100)


def exp142():
    class X(sim.Component):
        def process(self):
            yield self.request(r)

    env = sim.Environment(trace=True)
    r = sim.Resource("r")
    x = X()
    a = 1
    env.run()


def exp141():

    env = sim.Environment(trace=False)

    do_animate = True
    do_animate3d = True

    env.x0(0)
    env.x1(380)
    env.y0(0)

    env.width3d(950)
    env.height3d(768)
    env.position3d((0, 100))
    env.background_color("black")
    env.width(950)
    env.height(768)
    env.position((960, 100))

    env.animate(do_animate)
    env.animate3d(do_animate)
    env.show_fps(True)
    sim.Animate3dGrid(x_range=range(0, 101, 10), y_range=range(0, 101, 10))

    env.view.x_eye = 0
    env.view.y_eye = 0
    env.view.z_eye = 100
    env.view.x_center = 50
    env.view.y_center = 50
    env.view.z_center = 0
    env.view.field_of_view_y = 50

    env.show_camera_position()

    sim.Animate3dSphere(x=25, y=25, z=25, radius=15, color="red", number_of_slices=32)

    sim.Animate3dRectangle(x0=10, y0=10, x1=40, y1=40, z=-20, color="yellow")
    sim.Animate3dLine(x0=0, y0=0, z0=0, x1=50, y1=50, z1=50, color="purple")

    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=40, y1=10, z1=10)
    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=40, z1=10)
    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=10, z1=40)
    sim.Animate3dBar(x0=10, y0=10, z0=40, x1=10, y1=10, z1=10)

    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=40, z1=10)
    sim.Animate3dBar(x0=40, y0=40, z0=10, x1=40, y1=10, z1=10)
    sim.Animate3dBar(x0=40, y0=40, z0=10, x1=10, y1=40, z1=10)

    sim.Animate3dBar(x0=10, y0=10, z0=40, x1=40, y1=10, z1=40)
    sim.Animate3dBar(x0=10, y0=10, z0=40, x1=10, y1=40, z1=40)
    sim.Animate3dBar(x0=40, y0=40, z0=40, x1=40, y1=10, z1=40)
    sim.Animate3dBar(x0=40, y0=40, z0=40, x1=10, y1=40, z1=40)

    sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=10, z1=40)
    sim.Animate3dBar(x0=10, y0=40, z0=10, x1=10, y1=40, z1=40)
    sim.Animate3dBar(x0=40, y0=10, z0=10, x1=40, y1=10, z1=40)
    sim.Animate3dBar(x0=40, y0=40, z0=10, x1=40, y1=40, z1=40)

    sim.Animate3dCylinder(x0=0, y0=50, z0=0, x1=0, y1=50, z1=40, number_of_sides=8, radius=10, show_lids=False, color="green")

    sim.Animate3dBox(x_len=10, y_len=10, z_len=10, x=0, y=0, z=0, x_ref=1, y_ref=1, z_ref=1, color="red", shaded=True)
    sim.Animate3dBox(x_len=10, y_len=10, z_len=10, x=0, y=0, z=0, x_ref=-1, y_ref=-1, z_ref=-1, color="blue", edge_color="white")

    # AnimatePyramid(x=0, y=0, z=50, z_angle=lambda t:t*5, side_length=30, color="cyan", shaded=True)
    sim.Animate3dLine(
        x0=lambda t: (env.view.x_eye(t) + env.view.x_center(t)) / 2,
        y0=lambda t: (env.view.y_eye(t) + env.view.y_center(t)) / 2,
        z0=lambda t: (env.view.z_eye(t) + env.view.z_center(t)) / 2,
        x1=lambda t: env.view.x_center(t),
        y1=lambda t: env.view.y_center(t),
        z1=lambda t: env.view.z_center(t),
    )
    env.run(sim.inf)


def exp140():
    @yc
    def funcr(event):
        yc(event.keysym)

    class X(sim.Component):
        def process(self):
            pass

    env = sim.Environment(trace=True)

    env.animate(True)
    env.root.bind("r", funcr)
    env.root.bind("s", funcr)
    env.root.bind("t", funcr)
    env.root.bind("<Down>", funcr)
    env.root.bind("<Up>", funcr)
    env.root.bind("<Right>", funcr)
    env.root.bind("<Left>", funcr)
    env.root.bind("<Next>", funcr)
    env.root.bind("<Prior>", funcr)

    env.run(1000)


def exp139():
    class X(sim.Component):
        def process(self):
            for v in range(1, 101):
                env.ml.tally(v)
                env.m.tally(v)
                yield self.hold(1)
                env.ended = True

    class Controller(sim.Component):
        def process(self):
            while not env.ended:
                yield self.hold(sim.Uniform(10, 20)())
                env.ml.monitor(False)
                env.x.interrupt()
                yield self.hold(sim.Uniform(1000, 2000)())
                env.ml.monitor(True)
                env.x.resume()

    env = sim.Environment()
    env.ml = sim.Monitor("ml", level=True, stats_only=False)
    env.m = sim.Monitor("m")
    env.ended = False

    env.x = X()
    Controller()
    env.run()
    print(env.ml.mean())
    print(env.m.mean())
    assert env.ml.mean() == pytest.approx(50.5)
    assert env.ml.percentile(95) == 95
    assert env.ml.maximum() == 100
    assert env.ml.minimum() == 1

    assert env.m.mean() == 50.5
    assert env.m.percentile(95) == 95
    assert env.m.maximum() == 100
    assert env.m.minimum() == 1


def exp138():
    env = sim.Environment()
    stats_only_methods = []
    not_stats_only_methods = []
    for pn in sim.Monitor.__dict__.keys():
        p = getattr(sim.Monitor, pn)
        if callable(p) and not pn.startswith("sys"):
            if "_block" in inspect.getsource(p):
                stats_only_methods.append(pn)
            else:
                not_stats_only_methods.append(pn)
    print(", ".join(sorted(stats_only_methods)))
    print()
    print(", ".join(sorted(not_stats_only_methods)))


def exp137():
    env = sim.Environment(trace=True, blind_animation=True)
    print(sorted(list(sim.Monitor.__dict__.keys())))
    m1 = sim.Monitor("m1")
    m2 = sim.Monitor("m2")
    m2.reset(stats_only=True)
    for m in (m2,):
        m.print_histogram()

        m.tally(0)
        m.tally("3")
        m.tally(100, 10)
        m.monitor(True)
        m.tally(-100, 11115)
        print(f"mean {m.mean()} {m.mean(ex0=True)}")
        print(f"std  {m.std()} {m.std(ex0=True)}")
        print(f"min  {m.minimum()} {m.minimum(ex0=True)}")
        print(f"max  {m.maximum()} {m.maximum(ex0=True)}")
        print(f"number_of_entries {m.number_of_entries()} {m.number_of_entries(ex0=True)}")
        print(f"weight {m.weight()} {m.weight(ex0=True)}")
        m.print_statistics()
        m.print_histogram()

    print(m1 + m2)


def exp136():
    env = sim.Environment(trace=True, blind_animation=True)

    class X(sim.Component):
        def process(self):
            while True:
                sim.AnimateText("t=" + str(env.now()), x=env.now() * 40, y=env.now() * 40, fontsize=30)
                yield self.hold(1)

    X()
    env.video("test.mp4")
    env.animate(True)
    env.run(10)
    env.video_close()
    print("done")


def exp135():

    env = sim.Environment()

    monitor_names = sim.Monitor(name="names")
    for _ in range(10000):
        name = sim.Pdf(("John", 30, "Peter", 20, "Mike", 20, "Andrew", 20, "Ruud", 5, "Jan", 5)).sample()
        monitor_names.tally(name)

    monitor_names.print_histograms(values=("John", "Andrew", "Ruud", "Fred"))

    monitor_names.print_histogram(values=True, sort_on_weight=True)


def exp134():
    class X(sim.Component):
        def process(self):
            self.set_mode("abc")
            yield self.hold(0)
            yield self.request(r, mode="def")
            yield self.hold(10.1, mode="ghi")
            self.release()
            yield self.passivate(mode="jkl")

    class Interrupter(sim.Component):
        def process(self):
            yield self.hold(6)
            x0.interrupt()
            x1.interrupt()
            x2.interrupt()
            yield self.hold(4)
            x0.resume()
            x1.resume()
            x2.resume()

    def status_map(status):
        return sim.statuses().index(status)

    modes = "abc def ghi jkl".split()

    env = sim.Environment(trace=False)

    q = sim.Queue("queue")
    q.length_of_stay.print_histogram()
    q.length.print_histogram()

    r = sim.Resource("r")
    x0 = X(process="", mode="abc")
    x1 = X(process="")
    x2 = X(process="")
    Interrupter()
    x0.status.print_histogram(values=True)
    env.run(4.3)
    x0.activate()
    x1.activate()
    x2.activate()

    env.run(till=50)
    x0.status.print_histogram(values=True)
    x0.status.print_histogram(values=True, sort_on_duration=True)
    x0.status.print_histogram(values=[], sort_on_duration=True)


def exp133():
    class X(sim.Component):
        def process(self):
            sim.AnimateRectangle(spec=(-10, -10, 10, 10), x=100, y=100, fillcolor="red", parent=self)
            yield self.hold(2)
            self.enter(q)
            yield self.hold(4)

    env = sim.Environment()
    env.title("")
    env.show_menu_buttons(True)
    env.animate(True)
    x = X()
    q = sim.Queue("q")
    q.length.animate(x=100, y=300, horizontal_scale=10, parent=x)
    q.animate(parent=x)
    env.run(10)


def exp132():
    class X(sim.Component):
        def process(self):
            for v in range(7):
                yield self.hold(1, mode="abc")
                self.status._value = 3
                env.ml.tally(v)
                print(self.mode(), self.mode_time())
                self.mode.value = "def"
                yield self.hold(1)
                print(self.mode(), self.mode_time())
                env.ml.tally(v * 0.5)
                env.m.tally(v)
            env.ml.monitor(False)

    env = sim.Environment()
    env.ml = sim.Monitor("ml", level=True, initial_tally="aaaa")
    env.m = sim.Monitor("m")
    env.m.tally("aaaa", 4)
    env.m.tally("bbbb", 10)
    env.m.tally("cccc", 7)
    env.m.tally(["dddd"], 6)

    X()
    env.run(10)
    env.m.print_histogram()
    env.ml.print_histogram()
    env.m.print_histogram(values=True)
    env.ml.print_histogram(values=True)
    print(env.m.values())
    print(env.ml.values())
    print(env.m.values(force_numeric=True))
    print(env.ml.values(force_numeric=True))
    print(env.m.values(ex0=True))
    print(env.ml.values(ex0=True))

    env.m.print_histogram(values=True)
    env.m.print_histogram(values=[0, 1, 2, "aaaa", "bbbb", "cccc", "dddd", "eeee"])
    print(env.m.value_weight("aaaa"))
    env.m.print_histogram(values=[0, 1, 2, "aaaa", "bbbb", "cccc", "dddd", "eeee"])
    print(env.m.value_weight("aaaa"))
    env.m.print_histogram(values=True, sort_on_weight=True)
    env.m.print_histogram(values=[2, 0, 1, "aaaa", "dddd", "eeee", "0000"])
    env.m.print_histogram(values=[2, 0, 1, "aaaa", "dddd", "eeee", "0000"], sort_on_weight=True)
    env.m.print_histogram(values=[2, 0, 1, "aaaa", "dddd", "eeee", "0000"], sort_on_value=True)
    env.m.print_histogram(values=[5])


def test131():
    class X(sim.Component):
        pass

    env = sim.Environment()
    q = sim.Queue("q", fill=[X() for _ in range(5)])
    print(q == q)


def test130():

    env = sim.Environment(time_unit="days")
    d = sim.Distribution("uniform(1,1, time_unit='days')", time_unit="weeksjj")
    d = sim.Distribution('uniform(0,2, "minutes")', time_unit="hours")
    print(d())


def test129():
    env = sim.Environment()
    sim.AnimateText("123456", x=lambda t: sim.interpolate(t, 0, 4, 0, 300), y=lambda t: sim.interpolate(t, 1, 3, 100, 200), fontsize=50, textcolor="blue")
    for i, c in enumerate(("blue", "red", "yellow", "green", "orange")):
        sim.AnimateRectangle((0, 0, 50, 50), x=i * 50, y=300, fillcolor=c)

    env.background_color(("red", 0))
    with env.video("./videos/gif/test*.gif"):
        env.video_pingpong(True)
        env.video_repeat(0)
        env.animate(True)
        env.run(1)


#    env.video_close()


def exp128():
    sim.show_fonts()


def test127():
    import time

    class Car(sim.Component):
        def process(self):
            yield self.hold(sim.IntUniform(5, 10)())
            yield self.hold(lambda: 2)

    start = time.time()

    env = sim.Environment(trace=True)
    env.suppress_trace_linenumbers(True)
    car_generator0 = sim.ComponentGenerator(component_class=Car, iat=sim.Uniform(2, 5), till=10)
    env.run()
    print(time.time() - start)


def test126():
    class Car(sim.Component):
        def process(self):
            yield self.hold(sim.IntUniform(5, 10)())
            yield self.hold(lambda: 2)

    class Bus(sim.Component):
        def process(self):
            yield self.hold(1)

    env = sim.Environment(trace=True)
    env.run(5)
    #    env.suppress_trace_linenumbers(True)
    car_generator0 = sim.ComponentGenerator(component_class=sim.Pdf((Car, Bus), 1), iat=3, number=6, till=100, force_at=True)
    car_generator0.print_info()
    car_generator1 = sim.ComponentGenerator(component_class=Car, number=1, at=100, till=200, force_at=True, force_till=False)
    car_generator1.print_info()
    car_generator2 = sim.ComponentGenerator(component_class=Car, iat=sim.Uniform(1, 2), at=1000, till=1010)
    car_generator2.print_info()
    car_generator3 = sim.ComponentGenerator(component_class=Car, iat=sim.Uniform(10, 20), at=10000, till=10001)
    car_generator3.print_info()
    car_generator4 = sim.ComponentGenerator(component_class=Car, iat=sim.Uniform(10, 20), at=100000, duration=100)
    car_generator4.print_info()
    print(repr(car_generator4))
    env.run()


def test125():
    class X(sim.Component):
        def setup(self):
            self.activate(process="proc1", at=100)

        def proc1(self):
            yield self.hold(5)

    env = sim.Environment(trace=True)
    X()
    env.run()


def test124():
    env = sim.Environment()
    env.animate(True)
    an0 = sim.AnimateRectangle(spec=(-50, -50, 50, 50), offsetx=100, offsety=100)
    an1 = sim.AnimateRectangle(spec=(-50, -50, 50, 50), offsetx=300, offsety=100)
    anx = sim.AnimateRectangle(spec=(-50, -50, 50, 50), offsetx=300, offsety=300)
    an01 = sim.AnimateCombined((an0, an1))
    an2 = sim.AnimateRectangle(spec=(-50, -50, 50, 50), offsetx=500, offsety=100)
    an3 = sim.AnimateRectangle(spec=(-50, -50, 50, 50), offsetx=700, offsety=100)
    an23 = sim.AnimateCombined((an2, an3))
    an01.extend([anx])
    an = an01
    an += an23
    an.y = lambda t: 10 * t
    print(an.x)
    an.text = lambda t: str(t) if t < 5 else "..."

    env.run(sim.inf)


def exp123():
    env = sim.Environment()
    d = sim.Map(sim.Normal(0, 3), lambda x: x if x > 0 else 0)
    for _ in range(10):
        print(d.sample())
    d = sim.Map(sim.Normal(0, 3), round)
    for _ in range(10):
        print(d.sample())
    d = sim.Map(sim.Uniform(1, 7), int)
    for _ in range(10):
        print(d.sample())
    d = sim.Map(sim.Pdf("abcdef", 1), lambda x: ord(x))
    for _ in range(10):
        print(d.sample())
    d = sim.Distribution("Map(Uniform(1, 10),int)")
    for _ in range(10):
        print(d.sample())


def test122():
    import PIL

    print(PIL.VERSION)


def test121():
    class X(sim.Component):
        def process(self):
            yield self.hold(2)

    out = open("output.txt", "w")

    env = sim.Environment(trace=out)
    for _ in range(3):
        X("testcomma,")
    env.trace(True)
    X()
    env.trace(False)
    X()
    env.trace(out)
    X()
    env.trace(False)
    out.close()
    env.run()


def test120():
    class Client(sim.Component):
        def process(self, quantity=1, prio=sim.inf):

            remain = 10
            while True:
                yield self.request((clerks, quantity, prio))
                yield self.hold(remain, mode="hold")
                if not self.isbumped():
                    break
                remain -= env.now() - self.mode_time()

            self.release(clerks)

        def process(self, quantity=1, prio=sim.inf):

            remain = 10
            while self.isbumped():
                yield self.request((clerks, quantity, prio))
                yield self.hold(remain, mode="hold")
                remain -= env.now() - self.mode_time()

            self.release(clerks)

    class Changer(sim.Component):
        def process(self):
            yield self.hold(3.5)
            clerks.set_capacity(1)

    env = sim.Environment(trace=True)
    Client(prio=0, quantity=1, at=0)
    Client(quantity=2, at=1)
    Client(prio=-2, at=3)
    Client(prio=-2, quantity=2, at=4)
    Client(prio=-2, at=5)
    #    Changer()
    clerks = sim.Resource("clerks", 2, preemptive=True)

    env.run()


def test119():
    class X(sim.Component):
        def process(self):
            yield self.hold(duration=sim.Constant(1))
            yield self.hold(till=sim.Constant(10))
            yield self.activate(at=sim.Constant(20))
            yield self.activate(delay=sim.Constant(6))
            yield self.request(res, 2, fail_at=sim.Constant(30))
            yield self.request(res, 2, fail_delay=sim.Constant(7))
            yield self.wait(st, True, fail_at=sim.Constant(40))
            yield self.wait(st, True, fail_delay=sim.Constant(8))

    env = sim.Environment(time_unit="seconds", trace=True)
    res = sim.Resource("res")
    st = sim.State("st")
    print(env.minutes(sim.IntUniform(1, 2)))
    X(at=sim.Constant(1))
    X(delay=sim.Constant(2))
    env.run(sim.Constant(100))
    env.reset_now(sim.Constant(1000))
    print(env.hours(sim.Constant(1.01)))
    print(env.to_time_unit("hours", sim.Constant(3600.1)))


def exp118():
    import numpy
    import random
    import scipy.stats as st

    env = sim.Environment(time_unit="seconds")
    for d in (
        sim.External(st.norm, loc=5, scale=1, random_state=1),
        sim.External(st.norm, loc=5, scale=1, random_state=1, size=4),
        sim.Bounded(sim.External(numpy.random.laplace, loc=5, scale=1, size=None)),
        sim.External(random.lognormvariate, mu=5, sigma=1, time_unit="minutes"),
        sim.Distribution("External(random.uniform,2,6,time_unit='minutes')"),
        sim.IntUniform(1, 5, time_unit="minutes"),
        sim.Exponential(10, time_unit="minutes"),
        sim.Exponential(rate=1 / 10, time_unit="minutes"),
        sim.Constant(1),
        sim.Constant(1, time_unit="minutes"),
        sim.Uniform(1, 2),
        sim.Uniform(1, 2, time_unit="minutes"),
        sim.Triangular(1, 3, 2),
        sim.Triangular(1, 3, 2, time_unit="minutes"),
        sim.Erlang(4, 2),
        sim.Erlang(4, 2, time_unit="minutes"),
        sim.Weibull(scale=2, shape=3),
        sim.Weibull(scale=2, shape=3, time_unit="minutes"),
        sim.Gamma(scale=2, shape=3),
        sim.Gamma(scale=2, shape=3, time_unit="minutes"),
        sim.Pdf((1, 2, 10), (1, 1, 2)),
        sim.Pdf((1, 2, 10), (1, 1, 2), time_unit="minutes"),
        sim.CumPdf((1, 2, 10), (1, 2, 4)),
        sim.CumPdf((1, 2, 10), (1, 2, 4), time_unit="minutes"),
        sim.Cdf((1, 0, 2, 1, 10, 10)),
        sim.Cdf((1, 0, 2, 1, 10, 10), time_unit="minutes"),
    ):
        print("***")
        d.print_info()
        print("mean=", d.mean())

        for i in range(10):
            print(d())


def test117():
    import numpy as np

    env = sim.Environment(set_np_random_seed=False)
    for _ in range(4):
        print(np.random.rand())


def test116():
    import scipy.stats as st

    env = sim.Environment()
    d = sim.SciPyDis(st.norm, loc=5, scale=1, randomstate=11)
    print(d.mean())

    for i in range(10):
        print(d())


def test115():
    class X(sim.Component):
        def animation_objects(self):
            ao = sim.AnimateRectangle(spec=(-40, -10, 40, 10), fillcolor="red", text=lambda arg, t: f"{len(q)}.{arg.sequence_number()}", arg=self)
            return 90, 30, ao

    class Generator(sim.Component):
        def process(self):
            while True:
                x = X()
                x.enter(q)
                yield self.hold(2)

    env = sim.Environment()
    q = sim.Queue("Queue")
    q.animate(x=1000, y=100)
    Generator()
    env.animate(True)
    env.run(1000)


def test114():
    class gengamma:
        i = 0

        def rvs(*args, **kwargs):
            gengamma.i += 1
            print("***rvs", args, kwargs)
            return [gengamma.i * kwargs["loc"]]

        def mean(*args, **kwargs):
            return kwargs["loc"]

    print("start")
    env = sim.Environment(time_unit="seconds")
    d = sim.SciPyDis(gengamma, 1, loc=2, scale=20, time_unit="seconds")
    for _ in range(5):
        print(d.sample())
    print(d.mean())


def test113():
    class Putter(sim.Component):
        def process(self):
            while True:
                yield self.request((r0, -5))
                yield self.hold(1)

    class Getter(sim.Component):
        def process(self):
            while True:
                yield self.request((r0, 1))
                yield self.hold(10)

    env = sim.Environment(trace=True)
    Getter()
    Putter()
    r0 = sim.Resource("r0", 10, anonymous=True)
    env.run(100)


def test112():
    env = sim.Environment()

    for i in range(3):
        for s in ("ab", "ab.", "ab,", ""):
            c = sim.Component(s)
            print(c.name(), c.base_name())


def test111():
    class X(sim.Component):
        def process(self):
            while True:
                yield self.hold(sim.Uniform(5, 10))
                yield self.request(res)
                yield self.hold(sim.Uniform(5, 10))
                self.release()

    env = sim.Environment()
    res = sim.Resource("res", capacity=3)
    for _ in range(5):
        X()

    env.run(till=1000)
    res.reset_monitors()
    env.run(till=5000)
    res.occupancy.slice(start=1000, stop=5000).rename("ruud").print_statistics()
    res.occupancy[1000:5000].print_statistics()
    res.claimers().length[1000:5000].print_statistics()
    res.occupancy.print_statistics()
    res.occupancy.print_statistics()


def test110():
    class Controller(sim.Component):
        def process(self):
            while True:
                #                clerks.set_capacity(clerks.capacity() + 1)
                clerks.capacity.value += 1
                msg.text = "Silence"
                yield self.hold(3)
                msg.text = "test1.mp3"
                env.audio("test1.mp3>1")
                yield self.hold(1.5)
                #                if sim.Windows and not env.video():
                #                    env.video("test.mp4")

                yield self.hold(1.5)
                msg.text = "test0.mp3"

                env.audio("test0.mp3")
                yield self.hold(3)
                env.audio("")

    sim.reset()
    env = sim.Environment()
    env.debug_ffmpeg = True

    Controller()
    clerks = sim.Resource()
    env.background_color("black")
    env.animate(True)

    print("env._animate", env._animate)

    msg = sim.AnimateText(text="", x=100, y=100)
    env.run(30)
    env.video("")


def test109():
    env = sim.Environment(trace=True)

    q0 = sim.Queue("q0")
    comps = [sim.Component("comp.").enter(q0) for _ in range(4)]
    q1 = sim.Queue("q1")
    comps.extend([sim.Component("comp.").enter(q1) for _ in range(4)])
    even_comps = [c for i, c in enumerate(comps) if i % 2]
    print(even_comps)
    #    for c in q0:
    #        q0.pop().enter(q1)
    q1.extend(q0.move())
    q1.extend(even_comps)
    #    q1.extend(q0, clear_source=True)

    for comp in comps:
        print(comp.name(), *(q.name() for q in comp.queues()))


def test108():
    env = sim.Environment()
    print(sim.__version__)
    q0 = sim.Queue("q0")
    for _ in range(10):
        sim.Component("comp.").enter(q0)
    q0.print_info()
    q1 = q0.move("q1")
    q0.print_info()
    q1.print_info()


def test107():
    env = sim.Environment()
    mylist = [1, 2, 3, 400]
    m = sim.Monitor("Test", type="int8", fill=mylist)
    m.print_histogram()
    print(m._t)
    print(m._x)


def test106():
    env = sim.Environment()
    for i in range(10):
        print(sim.Bounded(sim.Uniform(-10, 10), 0).sample())
    print()
    sim.random_seed()
    for i in range(10):
        print(sim.Uniform(-10, 10).bounded_sample(0))
    print()
    sim.random_seed()
    for i in range(10):
        print(max(0, sim.Uniform(-10, 10).sample()))


def test105():
    env = sim.Environment()
    m0 = sim.Monitor("m0")
    m1 = sim.Monitor("m1")
    m0.tally("m0.0")
    m0.tally("m0.1")
    m1.tally("m1.0")
    sum((m0, m1)).rename("m0-m1").print_histogram(values=True)

    q0 = sim.Queue("q0")
    q1 = sim.Queue("q1")
    q2 = sim.Queue("q2")
    for _ in range(5):
        q0.add(sim.Component("Comp0."))
        q1.add(sim.Component("Comp1."))
        c = sim.Component("Compx.")
        q0.add(c)
        q2.add(c)
    (q0 - q2).rename("diff").print_info()
    sum((q0, q1, q2)).rename("qs").print_info()


def test104():
    import salabim as sim

    class X(sim.Component):
        def process(self):
            aos = []
            for iy in range(100):
                for ix in range(100):
                    aos.append(sim.AnimateRectangle(spec=(-1, -1, 1, 1), x=10 + ix * 6, y=10 + iy * 6))
                    yield self.hold(0.001)
            print("releasing")
            i = 0
            for ao in aos:
                #                print(i, end=" ")
                i += 1
                ao.remove()
                yield self.hold(0.001)

    env = sim.Environment(retina=True)
    env.animation_parameters(maximum_number_of_bitmaps=10000)
    print(env._maximum_number_of_bitmaps)
    env.animate(True)
    X()
    sim.AnimateText(
        """
             _         _      _
 ___   __ _ | |  __ _ | |__  (_) _ __ ___
/ __| / _` || | / _` || '_ \ | || '_ ` _ \\
\__ \| (_| || || (_| || |_) || || | | | | |
|___/ \__,_||_| \__,_||_.__/ |_||_| |_| |_|
Discrete event simulation in Python
""",
        x=100,
        y=600,
        font="mono",
        fontsize=30,
        text_anchor="nw",
    )
    env.run()
    env.run(3)


def test103():
    def print_samples():
        print()
        for i in range(5):
            print(sim.Uniform(0, 1)())

    env = sim.Environment()
    print_samples()
    sim.random_seed()
    print_samples()
    sim.random_seed("")
    print_samples()
    sim.random_seed("*")
    print_samples()
    sim.random_seed(None)
    print_samples()


def test102():
    env = sim.Environment(time_unit="hours")
    m = sim.Monitor(name="test", type="float")
    for i in range(100):
        m.tally(sim.Uniform(0, 100000)())
    m.print_histogram()
    m.multiply(100).print_histogram()
    (m * 5).print_histogram()
    (0.1 * m).print_histogram()
    m.to_time_unit("years", name="test (minutes)").print_histogram()
    for u in "years weeks days hours minutes seconds milliseconds microseconds".split():
        print(f"mean {m.mean()}  mean {m.to_time_unit(u).mean()} {u}")
    print(f"mean {m.to_years().mean()} years")
    print(f"mean {m.to_weeks().mean()} weeks")
    print(f"mean {m.to_days().mean()} days")
    print(f"mean {m.to_hours().mean()} hours")
    print(f"mean {m.to_minutes().mean()} minutes")
    print(f"mean {m.to_seconds().mean()} seconds")
    print(f"mean {m.to_milliseconds().mean()} milliseconds")
    print(f"mean {m.to_microseconds().mean()} microseconds")

    print(f"1 hour = {env.to_time_unit('minutes',1)} minutes")
    for u in "years weeks days hours minutes seconds milliseconds microseconds".split():
        print(f"1 hour = {env.to_time_unit(u,1)} {u}")
    print(env.to_time_unit("years", 10000))
    print(env.to_years(10000))


def test101():
    import matplotlib.pyplot as plt

    class X(sim.Component):
        def process(self):
            print("--", m.value, m.t)
            m.value = 5
            yield self.hold(10)
            m.tally(10)
            yield self.hold(1)
            m.tally(20)
            yield self.hold(2)
            m.tally(15)
            yield self.hold(10)

    env = sim.Environment()
    m = sim.Monitor(level=True)
    X()
    env.run(20)
    print(m.get())
    print(m())
    print("m.t", m.t)
    m.value += 100
    env.run(5)
    print(m.t)
    print(m.tx())
    print(m.xt())
    for t, x in zip(*m.tx()):
        print(f"{t:10.4f} {x:10.4f}")

    plt.plot(*m.tx(), drawstyle="steps-post")

    plt.show()


def test100():
    class X(sim.Component):
        def process(self):
            while True:
                self.enter(q)
                yield self.hold(1)
                self.leave(q)

    env = sim.Environment()
    q = sim.Queue("q")
    X()
    X()
    env.run(10)

    print(q.arrival_rate())
    print(q.departure_rate())
    q.arrival_rate(reset=True)
    q.departure_rate(reset=True)
    print(q.arrival_rate())
    print(q.departure_rate())


def test99():
    def show(d, n=None):
        print(d._x)
        print(d)
        for _ in range(10):
            if n is None:
                print(d.sample())
            else:
                print(d.sample(n))

    env = sim.Environment()
    show(sim.Pdf((1, 2, 3, 4), 1), 2)
    show(sim.Pdf((1, 2, 3, sim.Uniform(0, 1)), (1, 1, 1, 1)), 2)
    show(sim.Pdf((1, 1)), 0)
    show(sim.Pdf("a", (1,)))
    show(sim.CumPdf((1, 2, 3, 4)))


def test98():
    global d0, d1

    def test(s):
        print(s)
        d = eval(s)
        sum = 0
        for _ in range(1000):
            v = d.sample()
            sum += v
        print(sum / 1000, d.mean())

    #        d.print_info()

    env = sim.Environment()

    d0 = sim.Uniform(0, 10)
    d1 = sim.Uniform(0, 10)

    test("2 + d1")
    test("d1 + 2")
    test("d1 - 2")
    test("2 - d1")
    test("2 * d1")
    test("d1 * 2")
    test("2 / d1")
    test("d1 / 2")
    test("2 // d1")
    test("d1 // 2")
    test("+d1")
    test("-d1")

    test("d0 + d1")
    test("d1 + d0")
    test("d1 - d0")
    test("d0 - d1")
    test("d0 * d1")
    test("d1 * d0")
    test("d0 / d1")
    test("d1 / d0")
    test("d0 // d1")
    test("d1 // d0")


def test97():
    env = sim.Environment(time_unit="days")
    processingtime_dis = sim.Uniform(10, 20, "minutes")
    dryingtime_dis = sim.Normal(2, 0.1, "hours")
    processingtime_dis.print_info()
    dryingtime_dis.print_info()
    d2 = sim.Pdf((0, 1, 2, 3, 4, 5, 6), (18, 18, 18, 18, 18, 8, 2), "days") + sim.Cdf((0, 0, 8, 10, 17, 90, 24, 100), "hours")
    for i in range(0):
        print(d2())
    a = sim.Bounded(sim.Uniform(0, 10), upperbound=0.1, fail_value="fail", number_of_retries=30)
    a.print_info()
    for _ in range(10):
        print(a())

    a = sim.Bounded(
        sim.Pdf((0, 1, 2, 3, 4, sim.Uniform(1, 4), "ab"), 1),
        lowerbound=1,
        include_lowerbound=False,
        upperbound=4,
        include_upperbound=True,
        fail_value="fail",
        number_of_retries=10,
    )
    a.print_info()
    sim.random_seed(1)
    for _ in range(10):
        print(a())

    sim.random_seed(1)
    for _ in range(10):
        print(
            sim.Pdf((0, 1, 2, 3, 4, sim.Uniform(1, 4), "ab"), 1).bounded_sample(
                lowerbound=1, include_lowerbound=False, upperbound=4, include_upperbound=True, fail_value="fail", number_of_retries=10
            )
        )


def test96():
    env = sim.Environment()
    m = sim.Monitor(name="m")

    ml = sim.Monitor(name="ml", level=True)
    ml.tally(5)
    m.tally(10, 7)
    ml.tally(10)
    env.run(1)
    m.tally(11)
    #    ml.tally(ml.off)
    env.run(2)
    m.tally(5)
    ml.tally(5)
    env.run(8)
    print(m[:1].xt())
    print("***")
    m[0:0.1].print_histogram()
    print(m.slice(0, 3.1).xweight())
    print(ml.xt())
    print(ml.slice(0, 0.5, 1).xt())
    print(ml.mean())
    (0 + ml + ml + ml + ml + 0).print_statistics()
    mls = (ml, ml, ml, ml)
    sum(ml for i in range(4)).print_statistics()
    sum((ml, ml, ml, ml)).print_statistics()
    print("ml", ml.xt(exoff=True))
    print("ml+ml", (ml + ml).xt(exoff=True))


def test95():
    env = sim.Environment(time_unit="hours")
    #    env = sim.Environment()
    print(sim.Distribution("Uniform(1,2, 'days')").mean())
    print(env.get_time_unit())
    print(env.years(1))
    print(env.weeks(1))
    print(env.days(1))
    print(env.hours(1))
    print(env.minutes(1))
    print(env.seconds(1))
    print(env.milliseconds(1))
    print(env.microseconds(1))
    print()
    print(env.to_years(1))
    print(env.to_weeks(1))
    print(env.to_days(1))
    print(env.to_hours(1))
    print(env.to_minutes(1))
    print(env.to_seconds(1))
    print(env.to_milliseconds(1))
    print(env.to_microseconds(1))
    print("samples")
    d = sim.CumPdf((0, 5, 10), (60, 80, 100), time_unit="days")
    print(d.mean())
    d.print_info()
    for i in range(10):
        print(d())


def test94():
    class X(sim.Component):
        def process(self):
            while env.now() < 1000:
                yield self.hold(1)
                env.speed(env.speed() + 1)

    env = sim.Environment(trace=True)
    #    env.animate(True)
    X()
    sim.AnimateRectangle((0, 0, 10, 10), x=lambda t: t, y=100, fillcolor="red")
    env.time_to_str_format("{:7.5f}")
    env.run(till=sim.inf)


def test93():
    env = sim.Environment()
    m = sim.Monitor("m", weight_legend="gewicht")
    ml = sim.Monitor("ml", level=True, initial_tally=5, weight_legend="minutes")
    #    ml = sim.MonitorTimestamp('ml', initial_tally=5)
    m.print_histogram()
    m.tally(1)
    m.tally(2)
    m.tally("h5")
    m.print_histogram(values=True)
    m.tally("h4", 2)
    m.print_histogram(values=True)
    env.run(5)
    ml.monitor(False)
    env.run(5)
    ml.monitor(True)
    ml.print_histogram(values=True)
    ml.tally("6a")
    m.tally(100, 0.5)
    m.tally(100, 0.5)
    env.run(1.7)
    ml.print_histogram(values=True)
    print(ml.xt(add_now=True, force_numeric=False))
    print(m.xt(ex0=True))
    print(ml)
    print(m)
    mx = m.merge(m)
    mlx = ml.merge(ml)
    print(mlx.print_histogram(values=True))
    print(mx.xweight())
    mx.print_histogram()
    print(ml())


def weighted_percentile(a, percentile=None, weights=None):
    """
    O(nlgn) implementation for weighted_percentile.
    """
    import numpy as np

    a = np.array(a)
    percentile = np.array(percentile) / 100.0
    if weights is None:
        weights = np.ones(len(a))
    else:
        weights = np.array(weights)
    a_indsort = np.argsort(a)
    a_sort = a[a_indsort]
    weights_sort = weights[a_indsort]
    ecdf = np.cumsum(weights_sort)

    percentile_index_positions = percentile * (weights.sum() - 1) + 1
    # need the 1 offset at the end due to ecdf not starting at 0
    locations = np.searchsorted(ecdf, percentile_index_positions)

    out_percentiles = np.zeros(len(percentile_index_positions))

    for i, empiricalLocation in enumerate(locations):
        # iterate across the requested percentiles
        if ecdf[empiricalLocation - 1] == np.floor(percentile_index_positions[i]):
            # i.e. is the percentile in between 2 separate values
            uppWeight = percentile_index_positions[i] - ecdf[empiricalLocation - 1]
            lowWeight = 1 - uppWeight

            out_percentiles[i] = a_sort[empiricalLocation - 1] * lowWeight + a_sort[empiricalLocation] * uppWeight
        else:
            # i.e. the percentile is entirely in one bin
            out_percentiles[i] = a_sort[empiricalLocation]

    return out_percentiles


def test92():
    import numpy as np

    env = sim.Environment()
    monitor = sim.Monitor(weighted=True)

    #    for i in [1,3,7,9,1000]:
    #        monitor.tally(i,1)
    monitor.tally(1, 1)
    monitor.tally(5, 60)
    monitor.tally(7, 1)
    monitor.tally(10, 60)

    for p in (0.1, 1, 2, 3, 50, 90, 95, 100):
        print(f"{p:5.1f}% percentile  {monitor.percentile(p):10.4f}  {np.percentile(monitor.x(), p):10.4f}")
        r = weighted_percentile(monitor.xweight()[0], [p], monitor.xweight()[1])[0]
        print(r)


def test91():
    env = sim.Environment(trace=True)
    env.animation_parameters(animate=True, x0=-10, x1=10, y0=-10)
    #    sim.AnimateLine((0,0,5,5))
    print(env.scale())
    print(
        (env.screen_to_usercoordinates_x(0), env.screen_to_usercoordinates_y(0), env.screen_to_usercoordinates_x(1024), env.screen_to_usercoordinates_y(768)),
        env.screen_to_usercoordinates_size(1),
    )
    sim.AnimateLine(
        (env.screen_to_usercoordinates_x(0), env.screen_to_usercoordinates_y(0), env.screen_to_usercoordinates_x(1024), env.screen_to_usercoordinates_y(768)),
        linewidth=env.screen_to_usercoordinates_size(1),
    )
    sim.AnimateLine(
        (env.user_to_screencoordinates_x(10), env.user_to_screencoordinates_y(-10), env.user_to_screencoordinates_x(-10), env.user_to_screencoordinates_y(10)),
        linewidth=env.user_to_screencoordinates_size(env.screen_to_usercoordinates_size(1)),
        screen_coordinates=True,
    )
    print("start")
    env.run(sim.inf)


def test90():
    class X(sim.Component):
        def process(self):
            while True:
                yield self.hold(sim.Uniform(0, 20)())
                self.enter(q)
                yield self.hold(sim.Uniform(0, 20)())
                self.leave()

    class Y(sim.Component):
        def process(self):
            while True:
                yield self.standby()

    class PeriodMonitor(sim.Component):
        @staticmethod
        def new_tally(self, x):
            for m in self.period_monitors:
                m.perperiod[m.iperiod].tally(x)
            self.org_tally(x)

        @staticmethod
        def new_reset(self, monitor=None):
            for m in self.period_monitors:
                for iperiod in range(len(m.periods)):
                    m.perperiod[iperiod].reset()
            self.org_reset(monitor=monitor)

        def __getitem__(self, i):
            return self.perperiod[i]

        def setup(self, monitor, periods=None):
            try:  # salabim version <= 2.3.3.2 does not support skip_standby
                self.skip_standby(True)
            except AttributeError:
                pass
            if periods is None:
                periods = 24 * [1]
            self.m = monitor
            if not hasattr(self, "period_monitors"):
                self.m.period_monitors = []
                self.m.org_tally = self.m.tally
                self.m.tally = types.MethodType(self.new_tally, self.m)
                self.m.org_reset = self.m.reset
                self.m.reset = types.MethodType(self.new_reset, self.m)
                self.m.period_monitors.append(self)

            self.iperiod = 0
            self.periods = periods
            if self.m._timestamp:
                self.perperiod = [sim.MonitorTimestamp(name=self.m.name() + ".period[" + str(i) + "]", monitor=False) for i in range(len(self.periods))]
            else:
                self.perperiod = [sim.Monitor(name=self.m.name() + ".period[" + str(i) + "]", monitor=False) for i in range(len(self.periods))]

        def process(self):

            while True:
                for iperiod, duration in enumerate(self.periods):
                    self.perperiod[self.iperiod].monitor(False)
                    self.iperiod = iperiod
                    if self.m._timestamp:
                        self.perperiod[self.iperiod].tally(self.m())
                    self.perperiod[self.iperiod].monitor(True)
                    yield self.hold(duration)

    env = sim.Environment(trace=False)
    env.suppress_trace_standby(False)
    q = sim.Queue(name="q")

    qlength_per_hour = PeriodMonitor(monitor=q.length, periods=(24 * [1]), suppress_trace=True)
    qlength_of_stay_per_hour = PeriodMonitor(monitor=q.length_of_stay, periods=(24 * [1]), suppress_trace=True)
    [X() for i in range(15)]
    Y()
    env.run(2 * 24)
    q.reset_monitors()
    env.run(30 * 24)
    q.length.print_histogram()
    t = 0
    for hour in range(24):
        qlength_per_hour[hour].print_histogram()
        t += qlength_per_hour[hour].mean()
    #        qlength_of_stay_per_hour[hour].print_histogram()
    print(t / 24)
    print(q.length.mean())


def test89():
    class X(sim.Component):
        pass

    env = sim.Environment()
    all_components = []
    for _ in range(5):
        X().register(all_components)
    print(next((x for x in all_components if x.name() == "x.8"), None))


def test88():
    class Y(sim.Component):
        def process(self):
            yield self.hold(10)
            yield self.hold(3)

    class X(sim.Component):
        def process(self, d):
            env.print_trace("", "entering", str(d))
            yield self.hold(1)
            return
            pass

        def p1(self):
            pass

    env = sim.Environment(trace=True)
    Y()
    x = X(d=3, at=3, process="process")
    env.run(4)
    x.passivate()
    env.run(1)
    x.activate(process="p1", at=50)
    env.run(1)
    x.standby()

    env.run()
    print(sim.random.sample(range(6), 2))


def test87():
    def dump_an_objects():
        print("dump")
        for ao in env.an_objects:
            print(ao.type, ao.text(env.t) if ao.type == "text" else "")

    class X(sim.Component):
        def process(self):
            start = env.t
            an = sim.AnimateText("Hello", x=lambda t: (t - start) * 100, y=100)
            dump_an_objects()
            yield self.hold(5)
            an.remove()
            dump_an_objects()
            yield self.hold(6)

    env = sim.Environment(trace=False)
    env.animate(True)
    sim.AnimateText("abc", x=100, y=200)
    X()

    env.run(6)


def test86():
    class X(sim.Component):
        def setup(self, i):
            self.i = i

        def process(self):
            for i in range(2):
                yield self.hold(sim.Uniform(0, 2)())
                self.enter(q)
                yield self.hold(sim.Uniform(0, 2)())
                self.leave(q)

    env = sim.Environment(trace=False)
    q = sim.Queue("wachtrij")
    qa0 = sim.AnimateQueue(q, x=500, y=300, direction="n")
    [X(i=i) for i in range(15)]
    env.animate(True)

    env.run()


def test85():
    env = sim.Environment(trace=True)
    q = sim.Queue(name="queue")
    with open("test.txt", "w") as f:
        q.print_statistics(file=f)
    env.run()


def test84():
    def action():
        print(en.get())
        en.remove()

    class carAnimateCircle1(sim.Animate):
        def __init__(self, car):
            self.car = car
            sim.Animate.__init__(self, circle0=(car.R,), linecolor0="magenta", fillcolor0="white", linewidth0=1)

        def circle(self, t):
            if self.car.mode() == "Driving":
                return (self.car.R,)
            else:
                return (0.1,)

        def fillcolor(self, t):
            if self.car.mode() == "Driving":
                return ("yellow", 75)
            else:
                return ("white", 75)  # 'white'

    class carAnimateCircle(sim.Animate):
        def __init__(self, car):
            self.car = car
            sim.Animate.__init__(self, circle0=(car.R,), linecolor0="magenta", fillcolor0="white", linewidth0=1)

        def circle(self, t):
            if self.car.mode() == "Driving":
                return (self.car.R,)
            else:
                return (0.1,)

        def fillcolor(self, t):
            if self.car.mode() == "Driving":
                return ("yellow", 75)
            else:
                return ("white", 75)  # 'white'

    class Car(sim.Component):
        def setup(self, R):
            self.R = R
            sim.AnimateCircle(
                linecolor="magenta",
                radius=lambda car, t: self.R if car.mode() == "Driving" else 0.1,
                fillcolor=lambda car, t: ("yellow", 75) if car.mode() == "Driving" else ("white", 75),
                arg=self,
            )

        def process(self):
            while True:
                yield self.hold(1, mode="Driving")
                yield self.hold(1, mode="Stand still")

    env = sim.Environment()
    Car(R=100)
    env.animate(True)
    env.x0(-200)
    env.x1(200)
    env.y0(-150)
    sim.AnimateLine((0, 0, 100 - 3, 100 - 3), screen_coordinates=True)

    en = sim.AnimateEntry(x=100, y=100, action=action)

    env.run()


def test83():
    l1 = []

    test_input = """
    1   \t\t  {2 3 67} 4  12000
    4 5 6
    7
    """
    with sim.ItemFile(test_input) as f:
        while True:
            try:
                print(f.read_item_int())
            except EOFError:
                break


def test82():
    env = sim.Environment(retina=True)
    env.width()
    sim.AnimateButton(x=200, y=200, width=50, xy_anchor="c", text="Next", fillcolor="red", action=None)

    y = sim.AnimateCircle(radius=100, x=900, y=600, linewidth=1 / env.scale(), fillcolor=("red", 100), linecolor="black", draw_arc=True)
    #    x = sim.Animate(circle0=(100,100, 0, 60, False), x0=900, y0=600, linewidth0=3, fillcolor0='red', linecolor0='black')
    a = sim.Animate(
        circle0=(100, 100, 0, 0, True), circle1=(100, None, 0, 720, True), x0=200, y0=200, linewidth0=3, fillcolor0="blue", fillcolor1="green", t1=10
    )
    b = sim.Animate(rectangle0=(-100, -10, 100, 10), x0=300, y0=600, angle1=360, t1=10)
    b = sim.Animate(rectangle0=sim.centered_rectangle(10, 10), x0=200, y0=200, fillcolor0="red")
    #    b = sim.Animate(rectangle0=(-100,-10, 100, 10), x0=300, y0=600)
    sim.AnimateCircle(
        radius=100,
        radius1=300,
        x=lambda t: 700 - t * 10,
        y=200,
        fillcolor=lambda t: env.colorinterpolate(t, 0, 10, "yellow", "blue"),
        arc_angle0=0,
        arc_angle1=lambda t: t * 10,
        draw_arc=True,
        linewidth=1,
        linecolor="red",
        text="Piet",
        angle=lambda t: t * 10,
        textcolor="black",
        text_anchor="e",
    )

    env.animate(True)
    env.run(till=sim.inf)


def test81():
    def mtally(x, n):
        for i in range(n):
            m.tally(x)
        mw.tally(x, n)

    class X(sim.Component):
        def process(self):
            mt.tally("abc")
            for i in range(10):
                yield self.hold(1)
                mt.tally(i)
            env.main().activate()

    sim.reset()
    env = sim.Environment()
    X()
    mt = sim.MonitorTimestamp(name="mt")
    mw = sim.Monitor(name="mw", weighted=True, weight_legend="de tijd")
    m = sim.Monitor(name="m")

    mtally(3, 1)
    mtally(5, 2)
    mtally(6, 2)
    mtally("test", 2)
    m.tally(3, 1)

    print(m.mean())
    print(m.std())
    print(mw.mean())
    print(mw.std())
    env.run()
    m.monitor(False)
    mt.monitor(False)
    print(mt.mean(), mt.std())
    for values in (True, False):
        m.print_histogram(values=values)
        mw.print_histogram(values=values)
        mt.print_histogram(values=values)
    print(m.weight(ex0=True))
    print(mw.weight(ex0=True))
    print(mt.duration(ex0=True))
    print(mt.xt(exoff=True))


def test80():
    env = sim.Environment(trace=False)

    class X(sim.Component):
        def process(self):
            yield self.hold(1)
            env.snapshot("manual/source/Pic1.png")

    env.animate(True)
    env.background_color("20%gray")

    sim.AnimatePolygon(spec=(100, 100, 300, 100, 200, 190), text="This is\na polygon")
    sim.AnimateLine(spec=(100, 200, 300, 300), text="This is a line")
    sim.AnimateRectangle(spec=(100, 10, 300, 30), text="This is a rectangle")
    sim.AnimateCircle(radius=60, x=100, y=400, text="This is a cicle")
    sim.AnimateCircle(radius=60, radius1=30, x=300, y=400, text="This is an ellipse")
    sim.AnimatePoints(spec=(100, 500, 150, 550, 180, 570, 250, 500, 300, 500), text="These are points")
    sim.AnimateText(text="This is a one-line text", x=100, y=600)
    sim.AnimateText(
        text="""\
Multi line text
-----------------
Lorem ipsum dolor sit amet, consectetur
adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud
exercitation ullamco laboris nisi ut
aliquip ex ea commodo consequat. Duis aute
irure dolor in reprehenderit in voluptate
velit esse cillum dolore eu fugiat nulla
pariatur.

Excepteur sint occaecat cupidatat non
proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.
""",
        x=500,
        y=100,
    )

    sim.AnimateImage("Pas un pipe.jpg", x=500, y=400)
    X()
    env.run(100)


def test79():
    env = sim.Environment(trace=True)

    class X(sim.Component):
        def process(self):
            yield self.hold(3)
            yield self.hold(5)

    env.reset_now(-1000)
    X(at=-500)
    env.run()


def test78():
    class X(sim.Component):
        def process(self):
            while True:
                yield self.hold(sim.Uniform(0, 2)())
                self.enter(q)
                yield self.hold(sim.Uniform(0, 2)())
                self.leave(q)

    env = sim.Environment(trace=False)
    for _ in range(15):
        x = X()
    q = sim.Queue("q")
    r = sim.Resource()
    s = sim.State()
    env.run(500)
    as_str = False
    f = open("test.txt", "w")
    f = None
    d = sim.Normal(4)
    d1 = sim.Distribution("Normal(4)")
    print(q.length.print_histograms(as_str=True))
    assert False
    q.print_histograms(as_str=as_str, file=f)
    q.print_statistics(as_str=as_str, file=f)
    q.print_info(as_str=as_str, file=f)
    env.print_info(as_str=as_str, file=f)
    x.print_info(as_str=as_str, file=f)
    s.print_info(as_str=as_str, file=f)
    r.print_info(as_str=as_str, file=f)
    d.print_info(as_str=as_str, file=f)
    d1.print_info(as_str=as_str, file=f)
    f.close()


def test77():
    def myy(self, t):
        print(env.t, env.now())
        return 600

    def y(self, t):
        if self == qa0:
            return 50
        if self == qa1:
            return 100
        if self == qa2:
            return 150
        return 600

    class X(sim.Component):
        def setup(self, i):
            self.i = i

        def animation_objects1(self, id):
            if id == "text":
                ao0 = sim.AnimateText(text=self.name(), textcolor="black")
                return 0, 20, ao0
            ao0 = sim.AnimateRectangle(
                spec=lambda c, t: (0, 0, 40 + 10 * t if c.index(q) <= 2 else 40, 20), text=self.name(), fillcolor=id, textcolor="white", arg=self
            )
            return lambda c, t: 45 + 10 * t if c.index(q) <= 2 else 45, 0, ao0

        def process(self):
            while True:
                yield self.hold(sim.Uniform(0, 2)())
                self.enter(q)
                yield self.hold(sim.Uniform(0, 2)())
                self.leave(q)

    env = sim.Environment(trace=False)
    sim.AnimateText("abcb", x=500, y=myy)
    q = sim.Queue("q")
    qa0 = sim.AnimateQueue(q, x=lambda t: 100 + t * 10, y=y, direction="e", reverse=False, id="blue")
    qa1 = sim.AnimateQueue(q, x=100, y=y, direction="e", reverse=False, max_length=6, id="red")
    qa2 = sim.AnimateQueue(q, x=100, y=y, direction="e", reverse=True, max_length=6, id="green")
    qa3 = sim.AnimateQueue(q, x=100, y=200, direction="n", id="text", title="A very long title")
    [X(i=i) for i in range(15)]
    env.animate(True)
    env.run(5)
    qa1.remove()
    env.run(5)


def test76():
    class X(sim.Component):
        def process(self):
            for i in range(100):
                yield self.hold(0.3)
                testline = ["Line" + str(i) for i in range(i)]
                testanim.line = testline

    env = sim.Environment()
    env.modelname("test many")
    env.background_color("10%gray")
    #    an = sim.Rectangle(spec=(0,0,400,200),x=100, y=100, text='ABCabcopqxyz\nABCabcopqxyz              \nABCabcopqxyz\n', text_anchor='sw', font='narrow', fontsize=40, textcolor='blue')
    #    an = sim.Rectangle(spec=(0,0,400,200),x=100, y=400, text='ABCabcopqxyz\nABCabcopqxyz           \nABCabcopqxyz\n', text_anchor='nw', font='narrow', fontsize=40, textcolor='blue')

    #    an = sim.Text(x=600, y=100, text='ABCabcopqxyz', anchor='sw', font='', fontsize=40, textcolor='blue')
    #    an = sim.Text(x=600, y=100, text='ABCabcopqxyz', anchor='nw', font='', fontsize=40, textcolor='blue')
    #    an = sim.Text(x=600, y=100, text='ABCabcopqxyz', anchor='e', font='', fontsize=40, textcolor='blue')

    for dir in ("nw", "w", "sw", "s", "se", "e", "ne", "n", "c"):
        an = sim.AnimateRectangle(
            spec=(-250, -250, 250, 250),
            x=300,
            y=300,
            fillcolor="",
            linewidth=1,
            linecolor="white",
            text="A1y" + dir,
            text_anchor=dir,
            textcolor="white",
            angle=lambda t: t * 5,
        )

    x = 600
    for c in "ABCabcopqxyz":
        sim.AnimateText(text=c, y=100, x=x, textcolor="white", text_anchor="s")
        x += 10

    an = sim.AnimateLine(spec=(0, 0, 1000, 0), x=500, y=100, linecolor="red")
    an = sim.AnimateCircle(radius=100, fillcolor=("red", 100), text="Hallo", textcolor="yellow", angle=45, x=500, y=500)

    an = sim.AnimateText(text=("cc\n\nx", "abc", "def", "", "ghi"), x=300, y=300, textcolor="white", text_anchor="c")

    testanim = sim.AnimateText(text=("Line1", "Line2", "Line3", "Line4"), x=600, y=10, text_anchor="sw", max_lines=0)

    X()

    env.animate(True)
    env.run()


def test75():
    class MyText(sim.Text):
        def __init__(self, my="Abc", *args, **kwargs):
            sim.Text.__init__(self, text=None, *args, **kwargs)
            self.my = my

        def text(self, t):
            return self.my + str(env.now())

        def anchor(self, t):
            if t > 50:
                return "w"
            else:
                return "e"

    def xx(self, t):
        return self.sequence_number() * 75 + 600 + t

    class Comp(sim.Component):
        def setup(self):
            i = self.sequence_number()
            sim.Rectangle(spec=sim.centered_rectangle(50, 50), y=100 + i * 75, fillcolor="orange", x=xx, arg=self)

        def x(self, t):
            return self.sequence_number() * 75 + 600 + t

        def process(self):
            yield self.cancel()

    class CompGenerator(sim.Component):
        def process(self):
            while True:
                yield self.hold(sim.Uniform(20, 20)())
                c = Comp()

    env = sim.Environment()
    env.modelname("test")
    env.background_color("10%gray")
    env.speed(16)
    CompGenerator()
    for s in ("a", "b", "p", "A", "A1yp"):
        print(s, env.getwidth(s, font="", fontsize=20), env.getheight(font="", fontsize=20))

    for text_anchor in ("s", "sw", "w", "nw", "n", "ne", "e", "se", "c"):
        sim.Text(x=200, y=200, text=text_anchor, text_anchor=text_anchor)

    anpanel = sim.Rectangle(
        spec=(0, 0, 400, 200),
        x=lambda: 50,
        y=500,
        text="This is a test with\ntwo lines\nline three ",
        text_anchor="sw",
        font="narrow",
        fontsize=40,
        textcolor="blue",
    )
    anpanel1 = MyText(x=50, y=20, my="MY")
    anpanel2 = sim.Rectangle(x=0, y=200, text="abcde", spec=(0, 0, 500, 100), angle=20, xy_anchor="n")
    sim.Circle(x=400, y=100, radius=100, text="Circle", fontsize=30, angle=45, xy_anchor="w")
    sim.Line(spec=(200, 750, 210, 700, 220, 730, 240, 730, 250, 700, 1000, 0))
    sim.Points(spec=(200, 750, 210, 700, 220, 730, 240, 730, 250, 700, 1000, 0))
    sim.Image(spec="Cogwheel.png", x=500, y=500, anchor="c", width=lambda t: t, text="cogwheel", angle=lambda t: t)
    angle = 0
    an = sim.Rectangle(spec=(-150, -25, 150, 25), x=300, y=125, fillcolor="red", angle=lambda t: t * 360 / 200, text="test", textcolor="white", text_anchor="e")
    sim.Line(
        spec=(0, 0, 900, 0),
        x=100,
        y=700,
        offsetx=0,
        offsety=0,
        text="hallo",
        text_anchor="nw",
        textcolor="white",
        text_offsetx=0,
        text_offsety=0,
        angle=lambda t: sim.interpolate(t, 0, 200, 0, 360),
    )

    env.animate(True)
    env.run(100)

    env.run()


def test74():
    class Comp(sim.Component):
        def process(self):
            a.tally(env.now())
            self.enter(stage1)
            yield self.hold(sim.Uniform(10, 20)())

            self.leave()
            b.tally(env.now())
            self.enter(stage2)
            yield self.hold(sim.Uniform(20, 30)())
            self.leave()

    class CompGenerator(sim.Component):
        def process(self):
            while True:
                yield self.hold(sim.Uniform(2, 6)())
                c = Comp()

    env = sim.Environment()
    env.modelname("test")
    env.background_color("10%gray")
    stage1 = sim.Queue("stage1")
    stage2 = sim.Queue("stage2")
    sim.aMonitor(monitor=stage2.length, x=100, y=100, as_points=True, as_level=True, linewidth=1, vertical_scale=5, fillcolor=("blue", 100))
    s2 = sim.aMonitor(monitor=stage2.length, x=300, y=100, linewidth=2, horizontal_scale=2)
    s1 = sim.aMonitor(monitor=stage1.length_of_stay, x=100, y=400, as_points=False, height=200)
    sim.aMonitor(stage2.length_of_stay, x=300, y=400, height=200)
    a = sim.Monitor(name="a")
    b = sim.Monitor(name="")
    a1 = sim.aMonitor(a, x=500, y=100, vertical_scale=1, horizontal_scale=10, height=200, as_points=True)
    sim.aMonitor(b, x=500, y=100, vertical_scale=1, linecolor="blue", height=200, as_points=True)

    CompGenerator()
    env.animate(True)
    env.speed(16)

    env.run(100)
    #    s2.remove()
    #    s1.remove()
    env.run()


def test73():
    class X(sim.Component):
        def process(self):
            while True:
                yield self.hold(1)
                mon.tally(sim.Uniform(0, 50)())

    env = sim.Environment(trace=True)
    env.background_color("white")
    env.modelname("Test")
    X()
    mon = sim.Monitor("monitor", level=True)
    sim.AnimateText(text="abc", x=100, y=1000)
    sim.AnimateRectangle(x=100, y=100, spec=(-5, -5, 5, 5))
    for angle in (0, 45, 90, 135, 180, 225, 270, 315):
        sim.AnimateRectangle(x=100, y=100, spec=(0, 0, 50, 50), fillcolor="", linecolor="red", angle=angle)
        a = mon.animate(x=500, y=350, width=300, height=300, vertical_scale=10, horizontal_scale=10, angle=angle / 10)
    env.animate(True)
    env.run(100)
    a.remove()
    env.run()


def test72():
    env = sim.Environment()
    p = sim.CumPdf((0, 0.5, 1, 0.5))
    p.print_info()
    print(p.mean())
    r = sim.Resource(name="resource")
    s = sim.State(name="state")
    q = sim.Queue("rij")
    r.name("bron")
    s.name("staat")
    as_str = False
    print("---")
    r.print_histograms(as_str=as_str)
    s.print_histograms(as_str=as_str)
    q.print_histograms(as_str=as_str)
    r.print_statistics(as_str=as_str)
    s.print_statistics(as_str=as_str)
    q.print_statistics(as_str=as_str)
    print("---")


def test71():
    env = sim.Environment()
    env.animate(True)
    p = (100, 100, 300, 100, 300, 500)
    r = (400, 400, 600, 600)
    po = (800, 400, 1000, 400, 1000, 650)
    sim.Animate(line0=p, linecolor0="red", linewidth0=1)
    sim.Animate(line0=p, linecolor0="red", linewidth0=1, linewidth1=10, as_points=True, t1=10)
    sim.Animate(rectangle0=r, linecolor0="green", linewidth0=1, as_points=False, fillcolor0="", t1=10)
    sim.Animate(rectangle0=r, linecolor0="blue", linewidth0=10, linewidth1=10, as_points=True, t1=10)
    sim.Animate(polygon0=po, linecolor0="orange", as_points=False, t1=10)
    sim.Animate(polygon0=po, linecolor0="pink", linewidth1=10, as_points=True, t1=10)
    sim.Animate(rectangle0=(500, 500, 600, 600))
    sim.Animate(circle0=100, x0=800, y0=300)
    env.run()


def test70():
    class X(sim.Component):
        def setup(self, start, durations, xs):
            self.start = start
            self.xs = xs
            self.durations = durations
            self.monitor = sim.MonitorTimestamp(name=self.name() + ".monitor", type="any", monitor=False)

        def process(self):
            yield self.hold(self.start)
            self.monitor.monitor(True)
            for x, duration in zip(self.xs, self.durations):
                self.monitor.tally(x)
                yield self.hold(duration)
            self.monitor.monitor(False)

    env = sim.Environment()
    x0 = X(start=0, xs=(1, 3, "a", "7"), durations=(1, 1, 1, 1))
    x1 = X(start=0, xs=("a", 2, 5), durations=(3, 3, 8))
    env.run(20)
    x0.monitor.print_histograms()
    x1.monitor.print_histograms()
    m = sim.MonitorTimestamp(name="combined", merge=(x0.monitor, x1.monitor))
    m.print_histogram()

    a1 = sim.Monitor(name="a1", type="int8")
    a1.tally(1)
    a1.tally(2)
    a1.tally(2)
    a1.tally(0)
    a2 = sim.Monitor(name="a2", type="int8")
    a2.tally(1)
    a2.tally(20)
    a2.tally(18)
    a2.tally(0)
    a2.tally(2)
    a1.print_histogram()
    a2.print_histogram()
    a = sim.Monitor(name="combined", merge=(a1, a2), type="int8")
    a.print_histogram()


def test69():
    class X(sim.Component):
        pass

    sim.reset()
    env = sim.Environment()
    q = sim.Queue("q")
    #    X().enter_sorted(q, (1,1))
    #    X().enter_sorted(q, (0,2))
    #    X().enter_sorted(q, (1,0))
    #    X().enter_sorted(q, (1,3))
    #    q.print_info()

    q = sim.Queue("q")
    X().enter_sorted(q, "one")
    X().enter_sorted(q, "two")
    X().enter_sorted(q, "three")
    X().enter_sorted(q, "four")
    q.print_info()


def test68():
    class X(sim.Component):
        def process(self):
            self.enter(q1).enter(q2)
            self.enter(q3)
            yield self.request(r)
            self.leave().enter(q2)
            self.leave(q2).leave().leave().enter(q1)

    env = sim.Environment(trace=True)
    q1 = sim.Queue("q1")
    q2 = sim.Queue("q2")
    q3 = sim.Queue("q3")
    components = []
    somecomponents = []
    x = [X().register(components).register(somecomponents) for _ in range(5)]

    r = sim.Resource().register(components)
    env.run()

    x[3].deregister(components)

    for c in components:
        print(c.name())
    for c in somecomponents:
        print(c.name())


def test67():
    env = sim.Environment()
    m = sim.Monitor("normal distribution")
    m.name("test")
    for i in range(100_000):
        m.tally(sim.Normal(10, 2)())
    m.print_histogram()


def test66():
    class Poly(sim.Animate):
        def __init__(self, radius, number_of_sides, *args, **kwargs):
            self.radius = radius
            self.number_of_sides = number_of_sides
            sim.Animate.__init__(self, polygon0=(), *args, **kwargs)

        def polygon(self, t):
            return sim.regular_polygon(radius=self.radius, number_of_sides=self.number_of_sides, initial_angle=t * 1)

    env = sim.Environment()
    env.animate(True)
    for i in range(3, 10):
        #        sim.Animate(polygon0=sim.regular_polygon(radius=60, number_of_sides=i, initial_angle=90), x0=50+(i-3)*150, y0=300
        Poly(radius=60, number_of_sides=i, x0=50 + (i - 3) * 150, y0=300)

    env.run()


def test65():
    class X(sim.Component):
        def process(self):
            while True:
                mt.tally("idle")
                yield self.hold(10)
                for i in range(6):
                    st = sim.Pdf(("prepare", "stage A", "stage B", "stage C", "stage D", "package"), 1)()
                    mt.tally(st)
                    yield self.hold(sim.Uniform(6, 6)())

    env = sim.Environment(trace=False)
    mt = sim.Monitor("Status", level=True)

    X()
    env.run(300)
    mt.print_histogram(values=True)


def test64():
    class X(sim.Component):
        def process(self):
            for i in list(range(70)):
                mt.tally(i)
                yield self.hold(2)
            env.main().activate()

    env = sim.Environment(trace=False)
    m = sim.Monitor("m")
    mt = sim.MonitorTimestamp("mt")

    X()
    env.run()
    m.print_histograms()
    for i in (0, 1, 1, 2, 3, 1, 1, 1, 10, 20, 300):
        m.tally(i)
    m.print_histograms()
    mt.print_histograms(ex0=True)


def test63():
    class X(sim.Component):
        def process(self):
            for i in (1, 2, 3, 1, 1, 1, "1", "jan", "a", 1, 2, "2"):
                mt.tally(i)
                try:
                    x = int(i)
                except Exception:
                    x = 1.5
                yield self.hold(2.1 * x)
            env.main().activate()

    env = sim.Environment(trace=True)
    m = sim.Monitor("m")
    mt = sim.MonitorTimestamp("mt")

    X()
    env.run()
    m.print_histogram(values=True)
    for i in (1, 2, 3, 1, 1, 1, 1.1, 1.2, "1.2", 0, "", " ", " 1000 ", 1000, 600, 6.8, 5, "2", "1", "jan", "piet", "x", "y", "b", "a", 1, 2, "2"):
        m.tally(i)
    m.print_histogram(values=True, ex0=False)
    mt.print_histogram(values=True)
    print(mt.xduration())

    mt.print_histogram()


def test62():
    class X1(sim.Component):
        def process(self):
            yield self.hold(100)

    class X2(sim.Component):
        def process(self):
            yield self.request(res, fail_at=100)
            yield self.hold(50)

    class X3(sim.Component):
        def process(self):
            yield self.passivate()

    class X4(sim.Component):
        def process(self):
            while True:
                yield self.standby()

    class X5(sim.Component):
        def process(self):
            yield self.wait(st, fail_at=100)
            yield self.hold(50)

    class Z(sim.Component):
        def process(self):
            for i in range(20):
                yield self.hold(1)

    class Y(sim.Component):
        def process(self):
            yield self.hold(4)
            x1.remaining_duration(100)
            yield self.hold(1)
            x1.interrupt()
            x2.interrupt()
            x2.interrupt()
            x3.interrupt()
            x4.interrupt()
            x5.interrupt()
            yield self.hold(2)
            res.set_capacity(0)
            st.set()
            yield self.hold(3)
            x1.resume()
            x2.resume()
            x3.resume()
            x4.resume()
            x5.resume()
            x2.resume()

    env = sim.Environment(trace=True)
    env.suppress_trace_standby(False)
    x1 = X1()
    x1.name("abc")
    x2 = X2()
    x3 = X3()
    x4 = X4()
    x5 = X5()

    y = Y()
    z = Z()
    res = sim.Resource("res", capacity=0)
    st = sim.State("st")

    env.run(urgent=True)


def test61():
    class X(sim.Component):
        def process(self):
            yield self.request(r1, r2, r3, oneof=True, mode="test")
            for r in (r1, r2, r3):
                r.claimers().print_info()
            yield self.hold(1)

    class Y(sim.Component):
        def process(self):
            yield self.request(r1)
            yield self.hold(1)
            #            self.cancel()
            a = 1

    env = sim.Environment(trace=True)
    r1 = sim.Resource("r1", capacity=2)
    r2 = sim.Resource("r2", capacity=2)
    r3 = sim.Resource("r3", capacity=2)
    X()
    Y()
    env.run()


def test60():
    class X(sim.Component):
        def process(self):
            yield self.request(r)
            yield self.hold(sim.Uniform(0, 2)())

    env = sim.Environment()
    r = sim.Resource(name="r", capacity=1)
    for i in range(5):
        X()
    env.trace(True)
    env.run(10)
    occupancy = r.claimed_quantity.mean() / r.capacity.mean()
    r.print_statistics()
    print(r.available_quantity.bin_duration(0, sim.inf))
    print(r.claimed_quantity.bin_duration(0, sim.inf))

    env.run(urgent=True)


def test59():
    def do_next():
        global ans
        global min_n

        for an in ans:
            an.remove()
        ans = []

        x = 10
        y = env.height() - 80
        sx = 230
        sy = 14
        y -= 30
        fontnames = []
        n = 0

        for fns, ifilename in sim.fonts():
            for fn in fns:
                fontnames.append(fn)
        fontnames.extend(sim.standardfonts().keys())
        last = ""
        any = False
        for font in sorted(fontnames, key=sim.normalize):
            if font != last:  # remove duplicates
                last = font
                n += 1
                if n >= min_n:
                    any = True
                    ans.append(sim.Animate(text=font, x0=x, y0=y, anchor="sw", fontsize0=15, font=font))
                    x += sx + 5
                    if x + sx > 1024:
                        y -= sy + 4
                        x = 10
                        if y < 0:
                            break
        min_n = n + 1
        if not any:
            env.quit()

    global ans
    global min_n

    env = sim.Environment()
    ans = []
    min_n = 0
    #    sim.Animate(text='Salabim fontnames', x0=x, y0=y, fontsize0=20, anchor='sw', textcolor0='white')

    do_next()
    env.background_color("20%gray")

    env.animate(True)
    env.run()


def test58():
    env = sim.Environment()
    names = sorted(sim.colornames().keys())
    x = 10
    y = env.height() - 80
    sx = 155
    sy = 23
    sim.Animate(text="Salabim colornames", x0=x, y0=y, fontsize0=20, anchor="sw", textcolor0="white")
    y -= 30
    for name in names:
        if env.is_dark(name):
            textcolor = "white"
        else:
            textcolor = "black"
        sim.Animate(rectangle0=(x, y, x + sx, y + sy), fillcolor0=name)
        sim.Animate(text="<null string>" if name == "" else name, x0=x + sx / 2, y0=y + sy / 2, anchor="c", textcolor0=textcolor, fontsize0=15)
        x += sx + 5
        if x + sx > 1024:
            y -= sy + 4
            x = 10

    env.background_color("20%gray")
    env.animate(True)
    env.run()


def test57():
    class X(sim.Component):
        def process(self):
            while env.now() < run_length:
                an.update(text=str(run_length - env.now()))
                yield self.hold(1)
            env.animation_parameters(animate=False)
            print(self.env._animate)
            #            yield self.hold(0)
            env.video("")
            env.main().activate()

    env = sim.Environment()
    env.delete_video("a.gif")

    env.animation_parameters(background_color="blue", modelname="test")
    env.video("a.jpg")
    env.video_pingpong(False)
    env.video_repeat(2)

    #    env.animation_parameters(video='test.avi+MP4V', speed=0.5)
    an = sim.Animate(text="", x0=100, y0=100, fontsize0=100)
    run_length = 1

    X()
    sim.Animate(line0=(0, 50, None, None), line1=(0, 50, 1024, None), linewidth0=4, t1=run_length)
    sim.Animate(circle0=(40,), x0=200, y0=200)
    sim.Animate(circle0=40, x0=300, y0=200)
    env.run()
    print("done")
    env.quit()


def test56():
    env = sim.Environment()
    mon = sim.Monitor("number per second")
    for i in range(100):
        sample = sim.Normal(0.083, 0.00166)()
        mon.tally(sample)

    mon = sim.Monitor("number per second")
    env.run(100)
    mon.print_histogram()


def test55():
    class X(sim.Component):
        def process(self):
            while True:
                yield self.hold(sim.Exponential(rate=0.83)())
                env.count += 1

    class Y(sim.Component):
        def process(self):
            while True:
                env.count = 0
                yield self.hold(1)
                print(env.count)
                mon.tally(env.count)

    env = sim.Environment()
    env.count = 0
    X()
    Y()
    mon = sim.Monitor("number per second")
    env.run(100)
    mon.print_histogram()


def test54():
    import test_a
    import test_b

    env = sim.Environment(trace=True)
    test_a.X()
    test_b.X()

    env.run(10)


def test53():
    en = sim.Environment()
    d = sim.Normal(10, 3)
    d.print_info()
    d = sim.Normal(10, coefficient_of_variation=0.3)
    d.print_info()
    d = sim.Normal(0, standard_deviation=3)
    d.print_info()
    d = sim.Normal(0, coefficient_of_variation=4)
    d.print_info()


def test52():
    class X(sim.Component):
        def process(self):
            #            env.animation_parameters(animate=False)
            while env.now() <= 6:
                an.update(text=str(env.now()), x0=env.now() * 10)
                yield self.hold(1)
            env.animate(True)
            while env.now() <= 12:
                an.update(text=str(env.now()), x0=env.now() * 10)
                yield self.hold(1)
            env.animation_parameters(animate=False)
            while env.now() <= 20:
                an.update(text=str(env.now()), x0=env.now() * 10)
                yield self.hold(1)
            env.animation_parameters(animate=True, modelname="something else", background_color="90%gray", x0=-100, width=500, height=500)
            env.x0(-100)
            while env.now() <= 25:
                an.update(text=str(env.now()), x0=env.now() * 10, textcolor0="red")
                yield self.hold(1)

    def printt(str2prn):
        return "[" + str(env.now()) + "]", str2prn

    sim.reset()
    logging.basicConfig(filename="sim.log", filemode="w", level=logging.DEBUG)
    print("***can_animate", sim.can_animate(try_only=True))

    try:
        print("***can_animate", sim.can_animate(try_only=False))
    except:
        print("failed")
    print("***can_video", sim.can_video())
    print("passed.")
    env = sim.Environment(trace=True)
    logging.debug(printt("piet"))
    env.animation_parameters(animate=True, modelname="test52", video="")
    s = sim.AnimateSlider(x=300, y=-50, xy_anchor="nw")
    a = sim.Animate(line0=(0, -50, 300, -50), xy_anchor="nw", screen_coordinates=True)
    #    env.animate(True)

    X()
    an = sim.Animate(text="Test", x0=100, y0=100)
    r = sim.Animate(rectangle0=(100, 100, 200, 200), x0=0, y0=10)
    r = sim.Animate(circle0=(1.11,), x0=0, y0=10, fillcolor0="red")
    l = sim.Animate(polygon0=(10, 10, 20, 20, 10, 20), fillcolor0="bg", linecolor0="fg", linewidth0=0.1)
    b = sim.AnimateButton(text="My button", x=-100, y=-20, xy_anchor="ne")
    env.run(10)
    env.run(20)
    env.quit()


def test51():
    env = sim.Environment()
    d = sim.Poisson(2)
    x = []
    m = sim.Monitor(name="samples")
    for i in range(10000):
        m.tally(d())
    m.print_histogram(15, 0, 1)


def test50():
    env = sim.Environment()
    for i, c in enumerate(string.printable):
        if i <= 94:
            print(i, c)
            sim.Animate(text=c, x0=10 + i * 10, y0=100, anchor="w")
    sim.Animate(line0=(0, 100, 1024, 100), linecolor0="red")

    env.animation_parameters(modelname="Test")
    env.animating = True
    env.trace(True)
    env.run(5)
    print(env.main()._scheduled_time)


def test49():
    l1 = []

    test_input = """
    one two
    three four
    five
    """
    with sim.ItemFile(test_input) as f:
        while True:
            try:
                print(f.read_item())
            except EOFError:
                break

    with sim.ItemFile("test.txt") as f:
        while True:
            try:
                l1.append(f.read_item_bool())
            except EOFError:
                break

        print("------------------------")

        f = sim.ItemFile("test.txt")
        l2 = []
        while True:
            try:
                l2.append(f.read_item())
            except EOFError:
                break

    for x1, x2 in zip(l1, l2):
        print(x1, x2)


def test48():
    class A(sim.Component):
        def myhold(self, t):
            print("**")
            yield self.hold(t)

        def process(self):
            while env.now() < 5:
                if env.now() > 30:
                    env.main().activate()
                print("aa")
                self.myhold(1)
                yield self.hold(1)

    class B(sim.Component):
        def process(self):
            while True:
                yield self.hold(1)

    env = sim.Environment(trace=True)
    env.suppress_trace_standby(True)
    A()
    B()
    env.run(8)
    print("ready")


def test47():
    class Dodo(sim.Component):
        pass

    class Car(sim.Component):
        def setup(self, color="unknown"):
            self.color = color
            print(self.name(), color)

        def process(self, duration):
            yield self.hold(duration)
            yield self.activate(process="process", duration=50)

        def other(self):
            yield self.hold(1)

    env = sim.Environment(trace=True)
    Car(process=None)
    Car(color="red", duration=12, mode="ABC")
    Car(color="blue", process="other")

    Dodo()

    env.run(100)


def test46():
    class Y(sim.Component):
        pass

    class X(sim.Component):
        def process(self):
            x = 0

            for i in range(10):
                q.add(Y())
                print("q.length=", q.length())
                if i == 3:
                    monx.monitor(False)
                    monx.tally(x)
                if i == 6:
                    monx.monitor(True)
                yield self.hold(1)
                x += 1

    env = sim.Environment()
    env.beep()
    monx = sim.MonitorTimestamp("monx")
    q = sim.Queue("q")
    X()

    env.run(20)
    print(monx.xt())
    print(q.length.xt())


def test45():
    def test(d, lowerbound=-sim.inf, upperbound=sim.inf):
        d.print_info()
        print("mean=", d.mean())
        l = [d(lowerbound, upperbound) for i in range(10000)]
        print("one sample", d())
        print("mean sampled =", sum(l) / (len(l) + 1))
        print("-" * 79)

    env = sim.Environment()
    mon = sim.Monitor()
    d = sim.Cdf((5, 0, 10, 50, 15, 90, 30, 95, 60, 100))
    for _ in range(10000):
        mon.tally(d.bounded_sample(lowerbound=5, upperbound=sim.inf, number_of_retries=300))

    mon.print_histogram(30, -5, 1)


def test44():
    import newqueue
    import newerqueue
    import newcomponent

    class X(sim.Component):
        def process(self):
            yield self.hold(10, mode="ok")
            if self == x1:
                yield self.passivate()
            yield self.hold(10, urgent=True)

    class Y(sim.Component):
        def setup(self, a="a"):
            print("a=", a)

        def process(self, text):
            print("-->", text)
            yield self.request((res, 4), fail_at=15)
            x1.activate(mode=5)

    env = sim.Environment(trace=True)
    res = sim.Resource()

    x0 = X()
    x1 = X(name="")
    x2 = X(name=",")
    z = newcomponent.NewComponent()
    q0 = sim.Queue()
    q1 = newqueue.NewQueue()
    q2 = newerqueue.NewerQueue()
    Y(process="process", text="Hello")
    q0.add(x1)
    q1.add(x1)
    q2.add(x1)

    env.run(50)
    env.print_trace_header()


def test43():
    def test(d):
        d.print_info()
        print("mean=", d.mean())
        l = [d() for i in range(10000)]
        print("one sample", d())
        print("mean sampled =", sum(l) / (len(l) + 1))
        print("-" * 79)

    env = sim.Environment()

    test(sim.IntUniform(1, 6))
    test(sim.Weibull(2, 1))
    test(sim.Gamma(5, 9))
    test(sim.Erlang(2, scale=3))
    test(sim.Exponential(rate=2))
    test(sim.Beta(32, 300))
    test(sim.Normal(5, 7))
    test(sim.Normal(5, 7, use_gauss=True))

    test(sim.Distribution("Exponential(rate=2)"))
    test(sim.Normal(5, 5))


def test42():
    class Rij(sim.Queue):
        pass

    class Komponent(sim.Component):
        pass

    class Reg(sim.Monitor):
        pass

    env = sim.Environment(trace=True)

    q1 = sim.Queue("q1")
    q2 = sim.Queue("q2")
    for i in range(15):
        c = sim.Component(name="c.")
        if i < 10:
            q1.add_sorted(c, priority=20 - i)
        if i > 5:
            q2.add_sorted(c, priority=i + 100)
    env.run(1000)
    del q1[1]
    print("length", q1.length.number_of_entries())
    print("length_of_stay", q1.length_of_stay.number_of_entries())

    q1.print_info()
    q2.print_info()

    (q1 - q2).print_info()
    (q2 - q1).print_info()
    (q1 & q2).print_info()
    (q1 | q2).print_info()
    (q2 | q1).print_info()
    (q1 ^ q2).print_info()
    q3 = sim.Queue(name="q3", fill=q1)
    q4 = sim.Queue(name="q4", fill=q1)
    print("before")
    q3.print_info()
    del q3[-1:-4:-1]
    print("after")
    q3.print_info()
    q4.pop(3)
    for c in q3:
        print(c.name(), c.count(q2), c.count(), q4.count(c), c.queues())


def test41():
    class Airplane(sim.Component):
        pass

    class Boat(sim.Component):
        pass

    class Car(sim.Component):
        pass

    env = sim.Environment()
    for i in range(2):
        a = Airplane(name="airplane")
        b = Boat(name="boat,")
        c = Car()
        print(a.name(), b.name(), c.name())


def test40():
    class C(sim.Component):
        def process(self):
            yield self.hold(10)

    class Disturber(sim.Component):
        def process(self):
            yield self.hold(5)
            c.passivate()
            yield self.hold(2)
            c.hold(c.remaining_duration())

    env = sim.Environment(trace=True)
    c = C(name="c")
    Disturber(name="disturber")
    env.run()


def test39():
    class C(sim.Component):
        def process(self):
            yield self.request(r, s="y")

    env = sim.Environment(trace=True)
    x = sim.Uniform(4)
    r = sim.Resource()
    C()
    env.run(4)


def test38():
    def animation_objects(self, value):
        if value == "blue":
            an1 = sim.Animate(circle0=(40,), fillcolor0=value, linewidth0=0)
        else:
            an1 = sim.Animate(rectangle0=(-40, -20, 40, 20), fillcolor0=value, linewidth0=0)
        an2 = sim.Animate(text=value, textcolor0="white")
        return (an1, an2)

    class X(sim.Component):
        def process(self):

            while True:
                for i in ("red", "green", "blue", "yellow", "red"):
                    letters.set(i[0])
                    light.set(i)
                    yield self.hold(1)

    class Q(sim.Queue):
        pass

    env = sim.Environment(trace=True)
    for i in range(3):
        q = Q(name="rij.")
    X()
    light = sim.State("light")
    light.animate()
    letters = sim.State("letters")
    letters.animate(x=100, y=100)

    env.animation_parameters(synced=False)
    env.run()


def test37():
    env = sim.Environment()
    s = sim.Monitor("s")

    s.tally(1)
    s.tally(2)
    s.tally(3)
    s.tally(0)
    s.tally(4)
    s.tally("a")

    print(s.x(ex0=False, force_numeric=True))


def test36():
    l = (1, 2, 3, 4, 5, 5, "6", "x", "6.1")
    print(sim.list_to_array(l))


def test35():
    env = sim.Environment()
    sim.show_fonts()
    sim.fonts()


def test34():
    class X(sim.Component):
        def process(self):

            try:
                yield self.hold(-1)
            except sim.SalabimError:
                yield self.hold(1)
            s1.set(1)
            yield self.hold(1)
            s1.set(2)
            s2.set("red")
            yield self.hold(2)
            s1.set(30)

    class Y(sim.Component):
        def process(self):
            while True:
                yield self.wait((s1, "$==2"))
                yield self.hold(1.5)

    class Z(sim.Component):
        def process(self):
            while True:
                yield self.wait((s2, '"$" in ("red","yellow")'), all=True)
                yield self.hold(1.5)

    env = sim.Environment(trace=True)
    env.print_info()
    s1 = sim.State(name="s.", value=0)
    s2 = sim.State(name="s.", value="green")
    s3 = sim.State(name="s.")
    s1.name("piet")
    q = sim.Queue("q.")
    x = X()
    y = Y()
    z = Z()
    env.run(10)
    s1.print_statistics()


def test33():
    class X(sim.Component):
        def process(self):

            yield self.hold(1)
            s1.set(1)
            yield self.hold(1)
            s1.set(2)
            s2.set("red")
            yield self.hold(2)
            s1.set(30)

    class Y(sim.Component):
        def process(self):
            while True:
                yield self.wait((s1, lambda x, component, state: x / 2 > self.env.now()))
                yield self.hold(1.5)

    class Z(sim.Component):
        def process(self):
            while True:
                yield self.wait((s2, lambda x, component, state: x in ("red", "yellow")))
                yield self.hold(1.5)

    env = sim.Environment(trace=True)
    env.print_info()
    s1 = sim.State(name="s.", value=0)
    s2 = sim.State(name="s.", value="green")
    s3 = sim.State(name="s.")
    q = sim.Queue("q.")
    x = X()
    y = Y()
    z = Z()
    env.run(10)


def test32():
    class X(sim.Component):
        def process(self):
            yield self.wait(go)
            print("X after wait")
            yield self.hold(10)

        def p1(self):
            print("X in p1")
            yield self.passivate()

    class Y(sim.Component):
        def process(self):
            yield self.hold(2)
            x.activate(keep_wait=True, at=20)

    env = sim.Environment(trace=True)
    go = sim.State()
    x = X()
    y = Y()
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
                yield self.wait(s1, (s2, "red"), (s2, "green"), s3)
                yield self.hold(1.5)

    env = sim.Environment(trace=True)
    env.print_info()
    s1 = sim.State(name="s.")
    s2 = sim.State(name="s.")
    s3 = sim.State(name="s.")
    q = sim.Queue("q.")
    x = X()
    y = Y()
    env.run(10)
    print("value at ", env.now(), s1.get())
    print(s1.value.xduration())
    print(s1.value.tx())
    print(env)
    print(y)
    print(q)
    print(s1)
    s1.print_info()
    s2.print_info()


def test30():
    env = sim.Environment()
    m = sim.Monitor("m")
    print(m.x(ex0=True))
    m.tally(1)
    m.tally(2)
    m.tally(3)
    m.tally(0)
    m.tally("0")
    m.tally("12")
    m.tally("abc")
    print(m.x(ex0=True))


def test29():
    global light

    class Light(sim.Component):
        def setup(self):
            self.green = sim.State(name="green")

        def process(self):
            while True:
                yield self.hold(1)
                self.green.trigger(max=2)
                yield self.hold(1)
                self.green.reset()

    class Car(sim.Component):
        def process(self):
            while True:
                yield self.wait((light.green, True, 1), (light.green, True, 1), fail_delay=8, all=True)
                yield self.hold(sim.Uniform(1, 3).sample())

    de = sim.Environment(trace=True)
    for i in range(10):
        car = Car()
    light = Light()
    de.run(10)
    light.green.print_statistics()
    print(light.green.value.xt())
    print(light.green.waiters())


def test28():
    de = sim.Environment(trace=True)
    wait = {}
    for i in range(3):
        wait[i] = sim.Queue("wait.")


def test27():
    m1 = sim.Monitor("m1")
    print(m1.mean(), m1.std(), m1.percentile(50), m1.histogram())
    m1.tally(10)
    print(m1.mean(), m1.std(), m1.percentile(50), m1.histogram())


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
            self.a = 4
            m2.tally()
            m2.monitor(True)
            print("3", m2.xt())
            yield self.hold(1)
            self.a = 20
            m2.tally()
            yield self.hold(1)
            self.a = 0
            m2.tally()
            yield self.hold(1)
            m3.tally()
            m2.monitor(True)

    de = sim.Environment()
    m1 = sim.Monitor("m1", type="uint8")
    print(m1.mean())
    m1.tally(10)
    m1.tally(15)
    m1.tally(20)
    m1.tally(92)
    m1.tally(0)
    m1.tally(12)
    m1.tally(0)
    print("m1.x()", m1.x(force_numeric=False))

    print("m1", m1.mean(), m1.std(), m1.percentile(50))
    print("m1 ex0", m1.mean(ex0=True), m1.std(ex0=True), m1.percentile(50, ex0=True))
    x = X()
    x.a = 10
    m2 = sim.MonitorTimestamp("m2", getter=x._get_a, type="int8")
    print("1", m2.xt())
    m2.monitor(True)
    m2.tally()
    print("a", m2.xt())
    #    m2.monitor(True)
    m2.tally()
    print("2", m2.xt())

    m3 = sim.MonitorTimestamp("m3", getter=x._now)
    print(m3())

    de.run(10)
    print("4", m2.xt())
    print("5", m2.xduration())
    print(m2.mean(), m2.std(), m2.percentile(50))
    m1.print_histogram(10, 0, 10)
    m2.print_histogram(10, 0, 10)
    print(m3.xduration())

    m3.print_histogram(10, 0, 10)
    print("done")

    #    for i in range(101):
    #        print(i,m1.percentile(i),m2.percentile(i))
    m3 = sim.Monitor("m3")
    m3.tally(1)
    m3.tally(3)
    print("xx")


def test25():
    de = sim.Environment()
    q = sim.Queue("q")
    c = {}
    for i in range(8):
        c[i] = sim.Component(name="c.")
        c[i].enter(q)
    print(q)
    for c in q:
        c.priority(q, -c.sequence_number())
    print(q)


def test24():
    class X1(sim.Component):
        def process(self):
            print("**x1 active")
            yield self.request((r, 2))
            yield self.hold(100)
            yield self.passivate()

        def p1(self):
            yield self.hold(0.5)
            yield self.activate(process=self.process())
            yield self.hold(100)
            yield self.passivate()

    class X2(sim.Component):
        def process(self):
            yield self.hold(1)
            x1.activate(at=3, keep_request=True)
            yield self.hold(5)
            x1.request(r)
            yield self.hold(1)
            x1.passivate()
            de.main().passivate()
            yield self.hold(5)
            x1.activate(at=20)

    class X3(sim.Component):
        def process(self):
            a = 1
            yield self.hold(1)

        pass

    de = sim.Environment(trace=True)
    x1 = X1(process="p1")
    x1.activate(at=0.5, process="process", urgent=True, mode="blabla")
    x2 = X2()
    x3 = X3()
    print("***name=", x3.running_process())
    x4 = sim.Component()
    x3.activate(process="process")
    r = sim.Resource("resource")
    de.run(till=sim.inf)


def test1():
    print("test1")

    class X(sim.Component):
        def __init__(self, extra=1, *args, **kwargs):
            sim.Component.__init__(self, *args, **kwargs)
            self.extra = extra

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
            x[3].reactivate(process=x[3].action2(), at=30)
            x[4].cancel()
            yield self.hold(0.5)
            yield self.standby()
            yield self.activate(process=self.action2(0.3))

        def action2(self, param):
            yield self.hold(param)

    class Monitor(sim.Component):
        def process(self):
            while env.now() < 30:
                yield self.standby()

    de = sim.Environment(trace=True)
    q = sim.Queue()

    x = [0]
    for i in range(10):
        x.append(X(name="x.", at=i * 5))
        #        x[i+1].activate(at=i*5,proc=x[i+1].action())
        x[i + 1].enter(q)

    x[6].suppress_trace(True)
    i = 0
    for c in q:
        print(c._name)
        i = i + 1
        if i == 4:
            x[1].leave(q)
            x[5].leave(q)
            x[6].leave(q)

    y = Y(name="y")
    #    y.activate(at=20)
    env.run(till=35)


#    env.run(4)


def test2():
    de = sim.Environment()
    print("test2")
    x = [None]
    q = [None]
    for i in range(5):
        x.append(sim.Component(name="x."))
        q.append(sim.Queue(name="q."))
    y = sim.Component(name="y")
    x[1].enter(q[1])
    y.enter(q[1])
    x[1].enter(q[2])
    x[2].enter(q[2])
    x[2].enter(q[1])
    x[3].enter(q[2])
    q[1].print_statistics()

    q[2].print_statistics()
    q[1].union(q[2], "my union").print_statistics()

    q[1].difference(q[2], "my difference").print_statistics()
    q[1].intersect(q[2], "my intersect").print_statistics()
    q[1].copy("my copy").print_statistics()
    #    q[1].move('my move').print_statistics()
    q[1].print_statistics()

    print(q[1])

    yy = q[1].component_with_name("y")
    ii = q[1].index(y)
    print(yy, ii)


def sample_and_print(dist, n):
    s = []

    for i in range(n):
        s.append(dist.sample())
    print("mean=", dist.mean(), "samples", s)


def test3():
    print("test3")

    sim.Environment(random_seed=1_234_567)
    print("string")
    d = sim.Distribution("Exponential (1000)")
    sample_and_print(d, 5)
    sim.random_seed(1_234_567)
    sample_and_print(d, 5)
    sim.random_seed(None)
    sample_and_print(d, 5)

    print("triangular")
    tr = sim.Triangular(1, 5, 3)
    sample_and_print(tr, 5)

    print("uniform")
    u = sim.Uniform(1, 1.1)
    sample_and_print(u, 5)
    print("constant")
    c = sim.Constant(10)
    sample_and_print(c, 5)

    print("normal")
    n = sim.Normal(1, 2)
    sample_and_print(n, 5)
    sample_and_print(n, 5)

    print("poisson")
    n = sim.Poisson(2)
    sample_and_print(n, 5)
    sample_and_print(n, 5)

    print("cdf")
    cdf = sim.Cdf((1, 0, 2, 25, 2, 75, 3, 100))
    sample_and_print(cdf, 5)
    sample_and_print(cdf, 5)

    print("pdf list")
    pdf = sim.Pdf((1, 2), 1)
    sample_and_print(pdf, 5)

    print("pdf dict")
    d = {1: "een", 2: "twee"}
    pdf = sim.Pdf(d, 1)
    sample_and_print(pdf, 5)

    print("pdf x")
    pdf = sim.Pdf((1, 1, 2, 1))
    sample_and_print(pdf, 5)

    print("pdf 1")
    pdf = sim.Pdf((sim.Uniform(10, 20), 10, sim.Uniform(20, 30), 80, sim.Uniform(30, 40), 10))
    sample_and_print(pdf, 5)

    print("pdf 2")
    pdf = sim.Pdf((sim.Uniform(10, 20), sim.Uniform(20, 30), sim.Uniform(30, 40)), (10, 80, 10))
    sample_and_print(pdf, 5)

    print("pdf 3")
    pdf = sim.Pdf(("red", "green", 1000), (10, 1, 10))
    sample_and_print(pdf, 5)

    print("pdf 4")
    pdf = sim.Pdf(("red", 10, "green", 1, 1000, 10))
    sample_and_print(pdf, 5)


def test4():
    print("test4")

    class X(sim.Component):
        def process(self):
            yield self.hold(10)
            yield self.request(res, 4)
            yield self.hold(20)
            res.requesters().print_statistics()
            res.claimers().print_statistics()
            for i in range(1):
                self.release(res, 4)

    class Y(sim.Component):
        def process(self):
            yield self.hold(11)
            yield self.request(res, 1, priority=1 - self.i)
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

    de = sim.Environment()
    res = sim.Resource(name="res.", capacity=4)
    res.x = 0
    x = X(name="x")
    y = [0]
    for i in range(6):
        c = Y(name="y.")
        c.i = i
        y.append(c)

    z = Z(name="z")
    env.run(till=1000)


def test5():
    print("test5")

    class X1(sim.Component):
        def process(self):
            while True:
                while True:
                    yield self.request(r1, 2, 5, r2, greedy=True, fail_at=de.now() + 6)
                    if not self.request_failed()():
                        break
                yield self.hold(1)
                self.release(r1, r2)
                yield self.passivate()

    class X2(sim.Component):
        def process(self):
            while True:
                yield self.request((r1, 3), (r2, 1, 1))
                yield self.hold(1)
                self.release(r1)
                yield self.passivate()

    class X3(sim.Component):
        def process(self):
            while True:
                yield self.request(r1, r2)
                yield self.hold(1)
                self.release(r1, r2)
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

    de = sim.Environment(trace=True)
    q = sim.Queue(name="q")
    r1 = sim.Resource(name="r1", capacity=3)
    r2 = sim.Resource(name="r2", capacity=0)
    r3 = sim.Resource(name="r3", capacity=1)

    x1 = X1()
    x2 = X2()
    x3 = X3()

    y = Y(name="y")
    env.run(till=21)


def test6():
    print("test6")

    class X(sim.Component):
        def process(self):
            yield self.passivate()
            yield self.hold(1)

    de = sim.Environment(trace=True)
    x = X()
    print(x.status()())
    q = sim.Queue(name="Queue.")
    q.name("Rij.")
    print(q.name())
    q.clear()
    env.run(till=10)
    x.reactivate()
    env.run()


def test7():
    print("test7")

    class X1(sim.Component):
        def process(self):
            yield self.request((r1, 5), (r2, 2), fail_at=5)
            yield self.passivate()

    class X2(sim.Component):
        def process(self):
            yield self.request((r1, 8), r2)
            yield self.passivate()

    class X3(sim.Component):
        def process(self):
            yield self.request((r1, 7))
            yield self.passivate()

    env = sim.Environment(trace=True)

    r1 = sim.Resource(capacity=10, anonymous=True)
    r2 = sim.Resource()
    r3 = sim.Resource()
    env.run(5)

    x1 = X1()
    x2 = X2()
    x3 = X3()
    X4 = sim.Component()

    q = {}
    for i in range(1, 5):
        q[i] = sim.Queue()

    x1.enter(q[1])
    x1.enter(q[2])
    x1.enter(q[3])

    x2.enter(q[1])
    x3.enter(q[1])

    env.run(10)
    r2.capacity(2)
    env.run(20)

    r1.print_statistics()
    r2.print_statistics()
    r3.print_statistics()


def test8():
    print("test8")

    class AnimatePolar(sim.Animate):
        def __init__(self, r, *args, **kwargs):
            self.r = r
            super().__init__(*args, **kwargs)

        def x(self, t):
            tangle = sim.interpolate(t, self.t0, self.t1, 0, 2 * math.pi)
            sint = math.sin(tangle)
            cost = math.cos(tangle)
            x, y = (100 + self.r * cost - 0 * sint, 100 + self.r * sint + 0 * cost)
            return x

        def y(self, t):
            tangle = sim.interpolate(t, self.t0, self.t1, 0, 2 * math.pi)
            sint = math.sin(tangle)
            cost = math.cos(tangle)
            x, y = (100 + self.r * cost - 0 * sint, 100 + self.r * sint + 0 * cost)
            return y

        def angle(self, t):
            return sim.interpolate(t, self.t0, self.t1, 0, 360)

        def fillcolor(self, t):
            f = sim.interpolate(t, self.t0, self.t1, 0, 1)
            if f < 0.5:
                return sim.colorinterpolate(f, 0, 0.5, sim.colorspec_to_tuple("red"), sim.colorspec_to_tuple("blue"))
            else:
                return sim.colorinterpolate(f, 0.5, 1, sim.colorspec_to_tuple("blue"), sim.colorspec_to_tuple("green"))

        def text(self, t):
            angle = sim.interpolate(t, self.t0, self.t1, 0, 360)
            return "{:3.0f}".format(angle)

    class X(sim.Component):
        def slideraction(self):
            print("value=" + str(self.myslider.v))

        def process(self):

            AnimatePolar(r=100, text="A", t1=10)

            x = 0
            for fontsize in range(8, 30):
                sim.Animate(x0=x, y0=height - 100, text="aA1", font=("Calibri,calibri"), fontsize0=fontsize)
                x += fontsize * 2
            x = 0
            for fontsize in range(8, 30):
                sim.Animate(x0=x, y0=height - 200, text="aA1", font="CabinSketch-Bold", fontsize0=fontsize)
                x += fontsize * 2

            self.rx = sim.Animate(x0=600, y0=300, linewidth0=1, rectangle0=(-200, -200, 200, 200), t1=10, fillcolor0="green#7f", angle1=0)
            self.rx = sim.Animate(x0=500, y0=500, linewidth0=1, line0=(-500, 0, 500, 0), t1=10, fillcolor0="black")
            self.rx = sim.Animate(x0=500, y0=500, linewidth0=1, line0=(0, -500, 0, 500), t1=10, fillcolor0="black")

            self.rx = sim.Animate(
                x0=500,
                y0=500,
                linewidth0=10,
                polygon0=(0, 0, 100, 0, 100, 100, 50, 50, 0, 100),
                offsetx1=100,
                offsety1=100,
                t1=10,
                fillcolor0="red#7f",
                angle1=360,
            )
            self.rx = sim.Animate(x0=600, y0=300, linewidth0=1, rectangle0=(-200, -200, 200, 200), t1=10, fillcolor0="blue#7f", angle1=360)

            #            self.t1=sim.Animate(x0=500,y0=500,fillcolor0='black',
            #                text='Test text',x1=500,y1=500,t1=25,font='CabinSketch-#Bold',fontsize0=20,anchor='ne',angle1=0,fontsize1=50)

            self.i1 = sim.Animate(
                x0=250,
                y0=250,
                offsetx0=100,
                offsety0=100,
                angle0=0,
                angle1=360,
                circle0=(20,),
                fillcolor0=("red", 0),
                linewidth0=2,
                linecolor0="blue",
                circle1=(20,),
                t1=15,
            )

            #            self.ry=sim.Animate(x0=500,y0=300,linewidth0=1,polygon0=(-100,-100,100,-100,0,100),t1=10,fillcolor0='blue',angle1=90)

            self.i1 = sim.Animate(x0=500, y0=500, angle0=0, layer=1, image="salabim.png", width0=300, x1=500, y1=500, angle1=360, t1=20, anchor="center")

            yield self.hold(3)
            self.i1.update(image="Upward Systems.jpg", angle1=self.i1.angle1, t1=self.i1.t1, width0=self.i1.width0)
            return
            self.myslider = sim.AnimateSlider(
                x=600, y=height, width=100, height=20, vmin=5, vmax=10, v=23, resolution=1, label="Test slider", action=self.slideraction
            )

            return

            self.p1 = sim.AnimatePolygon(
                x0=200, y0=200, polygon0=(-100, -100, 100, -100, 100, 100, -100, 100), t1=25, x1=100, y1=100, fillcolor1="red", linecolor0="blue", linewidth0=3
            )
            self.p2 = sim.Animate(
                linewidth0=2, linecolor0="black", linecolor1="white", x0=100, y0=600, fillcolor0="green", polygon0=(-50, -50, 50, -50, 0, 0), angle1=720, t1=8
            )
            self.r1 = sim.Animate(layer=1, x0=500, y0=500, rectangle0=(0, 0, 100, 100), fillcolor0="yellow", linecolor0="red", linewidth0=2, angle1=180, t1=10)
            self.t1 = sim.Animate(x0=200, y0=200, fillcolor0="black", text="Test text", x1=100, y1=100, anchor="center", t1=25, font="courier", fontsize1=50)
            self.r2 = sim.Animate(rectangle0=(-5, -5, 5, 5))

            i = 0
            for s in ["ne", "n", "nw", "e", "center", "w", "se", "s", "sw"]:
                sim.Animate(x0=200, y0=200, text=s, t0=i, t1=i + 1, anchor=s, keep=False, fillcolor0="red")
                i = i + 1

            self.p2 = sim.Animate(x0=500, y0=500, line0=(0, 0, 100, 100), angle1=360, t1=10, linecolor0="red", linewidth0=5)
            self.r2 = sim.Animate(x0=300, y0=700, rectangle0=(-300, -300, 300, 300), fillcolor0="", linecolor0="black", linewidth0=2)
            self.c1 = sim.Animate(x0=300, y0=700, circle0=(0,), fillcolor0="blue", circle1=(60,), t1=20)
            self.i1 = sim.Animate(x0=500, y0=500, angle0=0, layer=1, image="BOA.png", width0=300, x1=500, y1=500, angle1=360, t1=20, anchor="center")
            #            self.i1=sim.AnimateText(text='ABCDEF',x0=500,y0=200,angle0=0,layer=1,angle1=360,t1=20,anchor='center')
            yield self.hold(10)
            #            self.t1.update(color0='white',x1=100,y1=100,t1=25)
            self.r1.update()
            self.c1.update(t1=20, radius1=0)

    import os

    de = sim.Environment(trace=True)
    x = X()
    #    s='abcdefghijk'

    #    size=getfontsize_to_fit(s,10000)
    #    print ('--fontsize_to_fit',size)
    #    print('--width-1=', getwidth(s,'',size-1))
    #    print('--width  =', getwidth(s,'',size))
    #    print('--width+1=', getwidth(s,'',size+1))
    #    assert False

    height = 768
    env.animation_parameters(modelname="Salabim test")
    env.run(15)
    env.run(till=30)
    print("THE END")


def test9():
    print("test9")

    class X(sim.Component):
        def process(self):
            yield self.passivate(mode="One")
            yield self.passivate(mode="Two")
            yield self.passivate()
            yield self.hold(1)

    class Y(sim.Component):
        def process(self):
            while True:
                print("de.now()=", de.now())
                yield self.hold(1)
                print(x.mode())
                if self.ispassive():
                    x.reactivate()

    de = sim.Environment(trace=True)
    x = X()
    y = Y()
    env.run(till=6)


def test10():
    print("test10")
    for s in ("blue", "", "black#23", "#123456", "#12345678", (1, 2, 3), (4, 5, 6, 7), ("blue", 8), ("blue#67", 1), ("#123456", 23)):
        t = sim.colorspec_to_tuple(s)
        print(s, "==>", t)


def test11():
    class Do1(sim.Component):
        def process(self):
            while True:
                if q1.length() == 0:
                    yield self.passivate()
                print("------")
                for cc in q1:
                    print(de.now(), cc.name())
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

    de = sim.Environment(trace=True)
    d2 = Do2()
    d1 = Do1()

    q1 = sim.Queue("q1")
    q2 = sim.Queue("q2")
    c = {}
    for i in range(10):
        c[i] = sim.Component(name="c" + str(i))
        c[i].enter(q2)
    x = q2.pop()
    print("x=", x)
    print("head of q1", q1.head())
    print("q1[0]", q1[0])
    print("tail of q1", q1.tail())
    print("q1[-1]", q1[-1])

    print("head of q2", q2.head())
    print("q2[0]", q2[0])
    print("tail of q2", q2.tail())
    print("q2[-1]", q2[-1])

    print("**c[0]=", c[0])
    c[0].enter(q1)
    c[0].set_priority(q1, 10)
    print(q1)

    c[3].set_priority(q2, 10)

    c[1].set_priority(q2, -1)
    c[5].set_priority(q2, 10)
    for cx in q2:
        print(cx.name())
    for cx in reversed(q2):
        print(cx.name(), cx in q1)

    print("--")
    print(q2[-1])
    print("---")

    env.run(till=100)


def test12():
    class X(sim.Component):
        def process(self):
            sim.Animate(text="Piet", x0=100, y0=100, x1=500, y1=500, t1=10)
            while True:
                print(sim.default_env())
                yield self.hold(1)

    de = sim.Environment(trace=True)
    env.animation_parameters(speed=1)
    a = sim.Environment(name="piet.")
    b = sim.Environment(name="piet.")
    c = sim.Environment(name="piet.")
    print(a)
    print(b)
    print(c)

    X(auto_start=False)
    X(auto_start=False)
    X(auto_start=False)
    X()
    env.animation_parameters(speed=0.1, video="x.mp4")
    env.run(4)
    env.run(2)
    env.run(4)


def test13():
    de = sim.Environment()
    q = sim.Queue()
    for i in range(10):
        c = sim.Component(name="c.")
        q.add(c)

    print(q)
    for c in q:
        print(c.name())

    for i in range(20):
        print(i, q[i].name())


def test14():
    class X(sim.Component):
        def process(self):
            yield self.request(*r)
            print(self.claimed_resources())

    de = sim.Environment()
    X()
    r = [sim.Resource() for i in range(10)]
    de.run(till=10)


def test15():
    d = sim.Pdf(("r", 1, "c", 1))
    d = sim.Pdf((1, 2, 3, 4), 1)
    print(d.mean())
    s = ""
    for i in range(100):
        x = d.sample()
        s = s + str(x)
    print(s)


def test16():
    de = sim.Environment()
    env.animation_parameters()
    a = sim.Animate(text="Test", x0=100, y0=100, fontsize0=30, fillcolor0="red")
    a = sim.Animate(line0=(0, 0, 500, 500), linecolor0="white", linewidth0=6)
    env.run()


def test17():
    def actiona():
        bb.remove()
        sl.remove()

    def actionb():
        ba.remove()

    de = sim.Environment()

    for x in range(10):
        for y in range(10):
            a = sim.Animate(rectangle0=(0, 0, 95, 65), x0=5 + x * 100, y0=5 + y * 70, fillcolor0="blue", linewidth0=0)
    ba = sim.AnimateButton(x=100, y=700, text="A", action=actiona)
    bb = sim.AnimateButton(x=200, y=700, text="B", action=actionb)
    sl = sim.AnimateSlider(x=300, y=700, width=300)
    sim.Animate(text="Text", x0=700, y0=750, font="Times NEWRomian Italic", fontsize0=30)
    de.animation_parameters(animate=True)
    env.run(5)
    env.animation_parameters(animate=False)
    env.run(100)
    env.animation_parameters(animate=True, background_color="yellow")
    env.run(10)


def test18():
    for j in range(2):
        print("---")
        r = random.Random(-1)
        r1 = random.Random(-1)
        d = sim.Exponential(3, r1)
        sim.Environment(random_seed=-1)
        for i in range(3):
            print(sim.Exponential(3, r).sample())
            print(sim.Exponential(3).sample())
            print(d.sample())


def test19():
    sim.show_fonts()


def test20():
    de = sim.Environment()
    y = 650
    if Pythonista:
        for t in ("TimesNewRomanPSItalic-MT", "Times.NewRoman. PSItalic-MT", "TimesNewRomanPSITALIC-MT", "TimesNoRomanPSItalic-MT"):
            sim.Animate(text=t, x0=100, y0=y, font=t, fontsize0=30, anchor="w")
            y = y - 50
    else:
        for t in ("Times New Roman Italic", "TimesNEWRoman   Italic", "Times No Roman Italic", "timesi", "TIMESI"):
            sim.Animate(text=t, x0=100, y0=y, font=t, fontsize0=30, anchor="w")
            y = y - 50

    de.animation_parameters(animate=True)
    env.run()


def test21():
    #    d=sim.Pdf((sim.Uniform(10,20),10,sim.Uniform(20,30),80,sim.Uniform(30,40),10))
    d = sim.Pdf((sim.Uniform(10, 20), sim.Uniform(20, 30), sim.Uniform(30, 40)), (10, 80, 10))

    for i in range(20):
        print(d.sample())


def test22():
    class X(sim.Component):
        def process(self):
            yield self.hold(10)

    class Y(sim.Component):
        def process(self):
            while True:
                yield self.hold(1)
                print("status of x=", env.now(), x.status()())

    de = sim.Environment()
    x = X()
    Y()

    env.run(12)


def test23():
    sim.a = 100
    for d in ("uni(12,30)", "n(12)", "exponentia(a)", "TRI(1)", "(12)", "12", "  (  12,  30)  ", "a"):
        print(d)
        print(sim.Distribution(d))


if __name__ == "__main__":
    exp()
