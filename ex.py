import salabim as sim


def salabim():
    class Control(sim.Component):
        def process(self):
            an1=sim.Animate(text='sim',x0=227,y0=768/2,fontsize0=200)
            an2=sim.Animate(text='ulation',x0=654,y0=768/2,fontsize0=200)
            yield self.hold(3)
            an2.update(y1=900, t1=env.now() + 3)
            an1.update(x1=176, t1=env.now() + 3)
            yield self.hold(3)
            an3 = sim.Animate(text='salabim', x0=676, y0= -100, y1=768/2, fontsize0=200, t1=env.now() + 3)
            yield self.hold(6)
            an1.update(x1=-130, t1=env.now() + 3)
            an3.update(x1=512, t1=env.now() + 1.5)
            yield self.hold(4)
            an3.update(fontsize1=300, t1=env.now() + 4, textcolor1='red')
            yield self.hold(6)
            an4 = sim.Animate(text='discrete event simulation', x0=512, y0=220, fontsize0=87)
    
    
    env = sim.Environment(trace=False)
    env.animation_parameters(x1=1024, background_color='30%gray')
    
    Control()
    
    env.run(30)

salabim()