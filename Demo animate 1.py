# Demo animate 1
import salabim as sim

class AnimateMovingText(sim.Animate):
    def __init__(self):
        super().__init__(text='',x0=100,x1=1000,y0=100,t1=env.now()+10)
        
    def x(self,t):
        return sim.interpolate(sim.interpolate(t,self.t0,self.t1,0,1)**2,0,1,self.x0,self.x1)
    
    def y(self,t):
        return int(t)*50
    
    def text(self,t):
        return '{:0.1f}'.format(t)
        

env=sim.Environment()

env.animation_parameters()

AnimateMovingText()

env.run()


