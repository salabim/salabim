CLONED
from __future__ import print_function # compatibility with Python 2.x
from __future__ import division # compatibility with Python 2.x

'''
salabim  discrete event simulation module
'''

import platform
Pythonista=(platform.system()=='Darwin')

import heapq
import random
import time
import math
import copy

try:
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
except:
    pass

if Pythonista:
    import scene
    import sys
    import ui
else:
    import tkinter
    from PIL import ImageTk    
    
try:
    from numpy import inf,nan
except:
    inf=1e100
    nan='nan'

__version__='1.0.0'

data='data'
current='current'
standby='standby'
passive='passive'
scheduled='scheduled'

if Pythonista:
        
    class MyScene(scene.Scene):
        def __init__(self,*args,**kwargs):
            scene.Scene.__init__(self,*args,**kwargs)
            animation.scene=self

        def setup(self):
            pass
        
        def touch_ended(self,touch):
            for ao in animation.animation_objects:            
                if ao.type=='button':
                    if touch.location in \
                      scene.Rect(ao.x-2,ao.y-2,ao.width+2,ao.height+2):
                        ao.action()
                if ao.type=='slider':
                    if touch.location in\
                      scene.Rect(ao.x-2,ao.y-2,ao.width+4,ao.height+4):
                        xsel=touch.location[0]-ao.x
                        ao._v=ao.vmin+round(-0.5+xsel/ao.xdelta)*ao.resolution
                        if ao.action!=None:
                            ao.action()                        
                                  
        def draw(self):   
            global animation
            scene.background(pythonistacolor(animation.background_color))
                
            if animation.running:
                if animation.paused:
                    t = animation.start_animation_time
                else:
                    t = \
                      animation.start_animation_time+\
                      ((time.time()-\
                      animation.start_animation_clocktime)*\
                      animation.animation_speed)                
                animation.t=t
                while animation.env.peek<t:
                    animation.env.step()
                    if animation.env._current_component==animation.env._main:
                        animation.env.print_trace(\
                          '%10.3f' % animation.env._now,\
                          animation.env._main._name,'current')                            
                        animation.env._scheduled_time=inf
                        animation.env._status=current
                        animation.running=False
                        return
           
                animation.animation_objects.sort\
                  (key=lambda obj:(-obj.layer,obj.sequence))
                touchvalues=self.touches.values()
                for ao in animation.animation_objects:
                    if type(ao) == Component.Animate:
                        im,x,y=ao.pil_image(t)
                        if im!=None:
                            try:
                                ims=scene.load_pil_image(im)
                                scene.image(ims,x,y,*im.size)
                            except:
                                pass
                            
                    elif ao.type=='button':
                        linewidth=ao.linewidth
                            
                        scene.push_matrix()
                        scene.fill(pythonistacolor(ao.fillcolor))
                        scene.stroke(pythonistacolor(ao.linecolor))
                        scene.stroke_weight(linewidth)
                        scene.rect(ao.x,ao.y,ao.width,ao.height)
                        scene.tint(ao.color)
                        scene.translate(ao.x+ao.width/2,ao.y+ao.height/2)
                        scene.text(str_or_function(ao.text),\
                          ao.font,ao.fontsize,alignment=5)
                        scene.tint(1,1,1,1)
                          #required for proper loading of images 
                        scene.pop_matrix()
                    elif ao.type=='slider':
                        scene.push_matrix()
                        scene.tint(pythonistacolor(ao.labelcolor))   
                        v=ao.vmin
                        x=ao.x+ao.xdelta/2
                        y=ao.y
                        mindist=inf
                        v=ao.vmin
                        while v<=ao.vmax:
                            if abs(v-ao.v)<mindist:
                                mindist=abs(v-ao._v)
                                vsel=v
                            v+=ao.resolution
                        thisv=ao._v
                        for touch in touchvalues:
                            if touch.location in\
                              scene.Rect(ao.x,ao.y,ao.width,ao.height):
                                xsel=touch.location[0]-ao.x
                                vsel=round(-0.5+xsel/ao.xdelta)*ao.resolution
                                thisv=vsel
                        scene.stroke(pythonistacolor(ao.linecolor))
                        v=ao.vmin
                        xfirst=-1
                        while v<=ao.vmax:
                            if xfirst==-1:
                                xfirst=x
                            if v==vsel:
                                scene.stroke_weight(3)
                            else:
                                scene.stroke_weight(1)
                            scene.line(x,y,x,y+ao.height)
                            v+=ao.resolution
                            x+=ao.xdelta
                                
                                
                        scene.push_matrix()
                        scene.translate(xfirst,ao.y+ao.height+2)
                        scene.text(ao.label,ao.font,ao.fontsize,alignment=9)     
                        scene.pop_matrix()
                        scene.translate(ao.x+ao.width,y+ao.height+2)    
                        scene.text(str(thisv)+' ',\
                          ao.font,ao.fontsize,alignment=7)                 
                        scene.tint(1,1,1,1)
                          #required for proper loading of images later                                
                        scene.pop_matrix() 
                                  
class Qmember():
    def __init__(self):
        pass
        
    def insert_in_front_of(self,m2,c,q,priority):
        m1=m2.predecessor
        m1.successor=self
        m2.predecessor=self
        self.predecessor=m1
        self.successor=m2
        self.priority=priority
        self.component=c
        self.queue=q
        self.enter_time=c.env._now
        q._length+=1
        q._maximum_length=max(q._maximum_length,q._length)
        c._qmembers[q]=self
        q.env.print_trace('','',c._name,'enter '+q._name)            

class Queue(object):
    '''
    queue object
    
    arguments:
        name        name of the queue.
                    if the name ends with a period (.),
                      auto serializing will be applied
                    if omitted, the name queue (serialized)
        env         environment where the queue is defined
                    if omitted, default_env will be used
    '''
    def __init__(self,name=None,env=None):
        if env is None:
            self.env=default_env
        else:
            self.env = env
        if name is None:
            name='queue.'
        self._name,self._base_name,self._sequence_number=\
          self.env._reformatnameQ(name)
        self._head=Qmember()
        self._tail=Qmember()
        self._head.successor=self._tail
        self._head.predecessor=None
        self._tail.successor=None
        self._tail.predecessor=self._head
        self._head.component=None
        self._tail.component=None
        self._head.priority=0
        self._tail.priority=0
        self._resource=None #used to reorder request queues, if req'd
        self._length=0
        self.reset_statistics()
        
    def __repr__(self):
        lines=[]
        lines.append('Queue '+hex(id(self)))
        lines.append('  name='+self.name)
        if self._length==0:
            lines.append('  no components')
        else:
            lines.append('  component(s):')
            mx=self._head.successor
            while mx!=self._tail:
                lines.append('    '+pad(mx.component._name,20)+\
                  ' enter_time'+time_to_string(mx.enter_time)+\
                  ' priority='+str(mx.priority))
                mx=mx.successor
        return '\n'.join(lines)
            
    @property
    def name(self):
        '''
        returns and/or sets the name of a queue
        
        arguments:
            txt         name of the queue
                        if txt ends with a period, the name will be serialized
        '''
        return self._name
        
    @name.setter
    def name(self,txt):
        self._name,self._base_name,self._sequence_number=\
          self.env._reformatnameQ(txt)
        
    @property
    def base_name(self):
        '''
        returns the base name of a queue (the name used at init or name)
        '''
        return self._base_name        

    @property
    def sequence_number(self):
        '''
        returns the sequence_number of a queue 
          (the sequence number at init or name)

        normally this will be the integer value of a serialized name,
        but also non serialized names (without a dot at the end)
          will be numbered)
        '''
        return self._sequence_number        

    def print_statistics(self):
        '''
        prints a summary of statistics of a queue
        ''' 
        
        print('Info on',self._name,'@',self.env._now)
        print('  length                ',self._length)
        print('  mean_length           ',self.mean_length)
        print('  minimum_length        ',self.minimum_length)
        print('  maximum_length        ',self.maximum_length)
        print('  mean_length_of_stay   ',self.mean_length_of_stay)                
        print('  maximum_length_of_stay',self.minimum_length_of_stay)                
        print('  maximum_length_of_stay',self.maximum_length_of_stay)                        
        print('  number_passed         ',self.number_passed)                                    
        print('  number_passed_direct  ',self.number_passed_direct)                                        
      
                
    def add(self,component):
        '''
        adds a component to the tail of a queue
    
        arguments:
            component            component to be added to the
                                   tail of the queue
                                 may not be member of the queue yet
                                 
        the priority will be set to
          the priority of the tail of the queue, if any
          or 0 if queue is empty
        '''
        component.enter(self)

    def add_at_head(self,component):
        '''
        adds a component to the head of a queue
    
        arguments:
            component            component to be added to the
                                   head of the queue
                                 may not be member of the queue yet
                                 
        the priority will be set to 
          the priority of the head of the queue, if any
          or 0 if queue is empty
        '''
        component.enter_to_head(self)

    def add_in_front_of(self,component,poscomponent):
        '''
        adds a component to a queue, just in front of a component
    
        arguments:
            component            component to be added to the queue
                                 may not be member of the queue yet            
            poscomponent         component in front of which component
                                   will be inserted
                                 must be member of the queue
        
        the priority of component will be set to the priority of popcomponent 
        '''
        component.enter_in_front_off(self,poscomponent)

    def add_behind(self,component,poscomponent):
        '''
        adds a component to a queue, just behind a component
    
        arguments:
            component            component to be added to the queue
                                 may not be member of the queue yet            
            popcomponent         component behind which component
                                   will be inserted
                                 must be member of the queue 
        
        the priority of component will be set to the priority of popcomponent
        '''
        component.enter_behind(self,poscomponent) 
        
    def add_sorted(self,component,priority):
        '''
        adds a component to a queue, according to the priority
    
        arguments:
            component            component to be added to the queue
                                 may not be member of the queue yet
            
            priority             used to sort the component in the queue
        '''
        component.enter_sorted(self,priority)

    def remove(self,component):
        '''
        removes component from the queue
    
        arguments:
            component                component to be removed
                                     must be member of the queue
        '''
        component.leave(self)
        
    @property
    def head(self):
        '''
        returns the head component of a queue, if any. None otherwise
        '''
        return self._head.successor.component
    
    @property
    def tail(self):
        '''
        returns the tail component of a queue, if any. None otherwise
        '''
        return self._tail.predecessor.component
        
    @property
    def pop(self):
        '''
        removes the head component and returns it, if any.
        Otherwise return None
        '''
        c=self.head
        if c!=None:
            c.leave(self)
        return c
    
    def successor(self,component):
        ''' 
        arguments:
            component            component whose successor to return
                                 must be member of the queue
         
        returns the successor of component, if any. None otherwise
        '''
        return component.successor(self)                

    def predecessor(self,component):
        ''' 
        arguments:
            component            component whose predecessor to return
                                 must be member of the queue
         
        returns the predecessor of component, if any. None otherwise
        '''
        return component.predecessor(self)   
        
    def contains(self,component):
        '''
        checks whether component is in the queue
        
        arguments:
            component            component to check
            
        True if component is in the queue. False otherwise
        '''
        return component.is_in_queue(self)
        
    def index_of(self,component):
        '''
        get the index of a component in the queue
        
        arguments:
            component            component to be queried
                                 does not need to be in the queue
                                 
        returns the index of component in the queue, where 0 denotes the head,
          if in the queue.
        returns -1 if component is not in the queue
        '''
        return component.index_in_queue(self)
        
    def component_with_index(self,index):
        '''
        returns a component in the queue according to its position
        
        arguments:
            index                position in the queue (0 is head)
            
        returns indexth (0-based) component in the queue if valid index
        return None if index is not valid
        '''
        mx=self._head.successor
        count=0
        while mx!=self._tail:
            count=count+1
            if count==index:
                return mx.component
            mx=mx.successor
        return None 
        
    def component_with_name(self,txt):
        '''
        returns a component in the queue according to its name
        
        arguments:
            txt                name of component to be retrieved
            
        returns the first component in the queue with name txt.
        returns None if not found
        '''
        mx=self._head.successor
        while mx!=self._tail:

            if mx.component._name==txt:
                return mx.component
            mx=mx.successor
        return None 
        
    @property
    def length(self):
        '''
        returns the length of a queue
        '''
        return self._length
        
    @property
    def minimum_length(self):
        '''
        returns the minimum length of a queue, since the last reset_statistics
        '''
        return self._minimum_length
        
    @property
    def maximum_length(self):
        '''
        returns the maximum length of a queue, since the last reset_statistics
        '''
        return self._maximum_length
        
    @property
    def minimum_length_of_stay(self):
        '''
        returns the minimum length of stay of components left the queue since the last reset_statistics
        returns nan if no component has left the queue
        '''
        if self._number_passed==0:
            return nan
        else:
            return self._minimum_length_of_stay
        
    @property
    def maximum_length_of_stay(self):
        '''
        returns the maximum length of stay of components left the queue since the last reset_statistics
        returns nan if no component has left the queue
        '''
        if self._number_passed==0:
            return nan
        else:
            return self._maximum_length_of_stay
                
    @property
    def number_passed(self):
        '''
        returns the number of components that have left the queue 
          since the last reset_statistics
        '''
        return self._number_passed
        
    @property
    def number_passed_direct(self):
        '''
        returns the number of components that have left the queue 
          with a length of stay of zero
          since the last reset_statistics
        '''
        return self._number_passed_direct
        
    @property
    def mean_length_of_stay(self):
        '''
        returns the mean length of stay of components that have left the queue
          since the last reset_statistics
        returns nan if no components have left the queue
        '''
        if self._number_passed==0:
            return nan
        else:
            return self._total_length_of_stay/self._number_passed
    
    @property
    def mean_length(self):
        '''
        returns the mean length of the queue since the last reset_statistics
        '''
        total_time=self._total_length_of_stay
        mx=self._head.successor
        while mx!=self._tail:
            total_time+=(self.env._now-mx.enter_time)
            mx=mx.successor
        duration=self.env._now-self._start_statistics
        if duration==0:
            return self._length
        else:
            return total_time/duration
                            
    def components(self,static=False,removals_possible=True):
        '''
        iterates over all components in queue
        
        arguments:
            static    if False (default),
                         the generator will dynamically return all components
                         in the queue.
                         This allows for components entering or leaving
                         the queue during the usage of the generator
                      if True,
                        the generator makes a snaphot of the queue and 
                        successively returns the components.
                        This may lead to unexpected results if the queue
                        changes during the iteration.
            removals_possible
                      if True (default),
                        it is allowed to remove components from the queue
                        during the iteration.
                      if False, removing components to the queue will lead
                        to unexpected results.
                        Also, only new components should only enter at the
                        tail. Use with great care, and only to improve
                        performance.
                      If static=True, this argument is ignored.
                                  
            usually this will be used in a construction like:
                for c in q.components():
                    ...
        '''
        if static:
            list=[]
            mx=self._head.successor
            while mx!=self._tail:
                list.append(mx.component)
                mx=mx.successor
            for c in list:
                yield c
                    
        else:
            if removals_possible:
                taken={}
                mx=self._head.successor
                while mx!=self._tail:
                    if mx.component in taken:
                        mx=mx.successor
                    else:
                        taken[mx.component]=0
                        msucc=mx.successor
                        yield mx.component
                        if msucc.component is None:
                            mx=self._head.successor
                        else:
                            mx=msucc
            else:
                mx=self._head.successor
                while mx!=self._tail:
                    yield mx.component
                    mx=mx.successor
        
    def union(self,q,name):
        '''
        returns the union of two queues
        
        arguments:
            q            queue to be unioned with self
            name         name of the  new queue
            
        the resulting queue will contain all elements of self and q
        the priority will be set to 0 for all components in the
          resulting  queue
        the order of the resulting queue is not specified
        '''
        save_trace=self.env._trace
        self.env._trace=False
        q1=Queue(name=name,env=self.env)
        components=[]
        mx=self._head.successor
        while mx!=self._tail:
            components.append(mx.component)
            mx=mx.successor
        mx=q._head.successor
        while mx!=q._tail:
            if mx.component not in components:
                components.append(mx.component)
            mx=mx.successor
        for c in components:
            Qmember().insert_in_front_of(q1._tail,c,q1,0)
        self.env._trace=save_trace
        return q1
        
    def intersect(self,q,name):
        '''
        returns the intersect of two queues
        
        arguments:
            q            queue to be intersected with self
            name         name of the  new queue
            
        the resulting queue will contain
          all elements of that are in self and q
        the priority will be set to 0 for all components in the 
          resulting queue
        the order of the resulting queue is not specified
        '''
        save_trace=self.env._trace
        self.env._trace=False
        q1=Queue(name=name,env=self.env)
        components=[]
        mx=q._head.successor
        while mx!=q._tail:
            components.append(mx.component)
            mx=mx.successor
        mx=self._head.successor
        while mx!=self._tail:
            if mx.component in components:
                Qmember().insert_in_front_of(q1._tail,mx.component,q1,0)
            mx=mx.successor
        self.env._trace=save_trace
        return q1

    def difference(self,q,name):
        '''
        returns the difference of two queues
        
        arguments:
            q            queue to be 'substracted' from self
            name         name of the  new queue
            
        the resulting queue will contain 
          all elements of self that are not in q
        the priority will be copied from the original queue
        also, the order will be maintained
        '''
        save_trace=self.env._trace
        self.env._trace=False
        q1=Queue(name=name,env=self.env)
        components=[]
        mx=q._head.successor
        while mx!=q._tail:
            components.append(mx.component)
            mx=mx.successor
            
        mx=self._head.successor
        while mx!=self._tail:
            if mx.component not in components:
                Qmember().insert_in_front_of(
                  q1._tail,mx.component,q1,mx.priority)
            mx=mx.successor
        self.env._trace=save_trace
        return q1

    def copy(self,name):
        '''
        returns a copy of two queues
        
        arguments:
            name         name of the  new queue
            
        the resulting queue will contain all elements of self
        the priority will be copied into the resulting
        '''
        save_trace=self.env._trace
        self.env._trace=False
        q1=Queue(name=name,env=self.env)
        mx=self._head.successor
        while mx!=self._tail:
            Qmember().insert_in_front_of(q1._tail,mx.component,q1,mx.priority)
            mx=mx.successor
        self.env._trace=save_trace
        return q1
      
    def move(self,name):
        '''
        makes a copy of a queue and empties the original
        
        arguments:
            name         name of the  new queue
            
        the resulting queue will contain all elements of self,
          with the proper priority
        self will be emptied
        '''
        q1=self.copy(name)
        self.clear()
        return q1
      
    def clear(self):
        '''
        empties a queue
        
        arguments:
            none
            
        removes all components from a queue
        '''
        mx=self._head.successor
        while mx!=self._tail:
            del mx.component._qmembers[self]
            mx=mx.successor
        self._head.successor=self._tail
        self._tail.predecessor=self._head
        self._length=0
        
    def reset_statistics(self):
        '''
        resets the statistics of a queue
        
        arguments:
            none
        '''        
    
        self._minimum_length_of_stay=inf
        self._maximum_length_of_stay=-inf
        self._minimum_length=self._length
        self._maximum_length=self._length
        self._number_passed=0
        self._number_passed_direct=0
        self._total_length_of_stay=0
        for c in self.components(static=True):
            self._total_length_of_stay-(self.env._now-c.enter_time)
        self._start_statistics=self.env._now
        

def run(*args,**kwargs):
    '''
    run for the default environment
    '''
    default_env.run(*args,**kwargs)
    

def step():
    '''
    step for the default environment
    '''
    default_env.step
    
def peek():
    '''
    peek for the default environment
    '''
    return default_env.peek
    
def _check_fail(c):
    if len(c._requests)!=0:
        c.env.print_trace('','',c._name,'request failed') 
        for r in list(c._requests.keys()):
            c._leave(r._requesters)
        for r in c._pendingclaims:
            r._pendingclaimed_quantity-=c._requests[r]
        c._requests={}
        for r in c._pendingclaims:
            r._claimtry()
        c._pendingclaims=[]
        c._request_failed=True
        
        
class Environment(object): 
    '''
    environment object
    
    arguments:
        trace       defines whether to trace or not
                    if omitted, False
        name        name of the environment.
                    if the name ends with a period (.), 
                      auto serializing will be applied
                    if omitted, the name environment (serialized)

        The trace may be switched on/off later with trace    
        '''
          
    def __init__(self,trace=False,name=None): 
        if name is None:
            name='environment.'
        self._name,self._base_name,self._sequence_number=\
          _reformatname(name,_nameserializeE)
        self._now=0
        self._nameserializeC={}
        self._nameserializeQ={}
        self._nameserializeR={}
        self.env=self 
        self._seq=0
        self._event_list=[]
        self._standbylist=[]
        self._pendingstandbylist=[]
        self._trace=trace
        
        self._main=Component(name='main',env=self)
        self._main._status=current
        self._current_component=self._main
        self.print_trace('%10.3f' % self._now,'main','current')   
        
    def __repr__(self):
        lines=[]
        lines.append('Environment '+hex(id(self)))
        lines.append('  name='+self._name)
        if (animation!=None) and (self==animation.env):
            lines.append('  (animation environment')
        lines.append('  now='+time_to_string(self._now))
        lines.append('  current_component='+self._current_component._name)
        lines.append('  trace='+str(self._trace))      
        return '\n'.join(lines)
        
        
    def reset(self,trace=False):
        '''
        resets the enviroment
        
        arguments:
            trace                   if True, trace is enabled
                                    if False, trace is disabled
                                    
        The trace may be switched on/off later with trace
        '''
        
        newenv=Environment(trace,name=self._name)
        self.__dict__=newenv.__dict__ #keep the original location
        self.env=self
        self.main.__dict__=newenv.main.__dict__ #keep the original location
        if animation!=None:
            if self==animation.env:
                animation.start_animation_time=self._now
                animation.start_animation_clocktime=time.time()
            for ao in animation.animation_objects[:]:
                if not ao.survive_reset:
                    animation.animation_objects.remove(ao)

        return self

    def step(self):
        '''
        executes the next step of the future event list
        
        for advanced use with animation / GUI loops
        '''          
        if len(self.env._pendingstandbylist)>0:
            c=self.env._pendingstandbylist.pop(0)
            if c._status==standby: #skip cancelled components
                c._status=current
                c._scheduled_time=inf
                self.env._current_component=c
                self.print_trace('%10.3f' % self._now,c._name,\
                  'current (standby) @ '+_atprocess(c._process))  
                try:
                    next(c._process)
                    return
                except StopIteration:
                    self.print_trace('%10.3f' % self._now,c._name,'ended')
                    c._status=data 
                    c._scheduled_time=inf
                    c._process=None
                    if animation!=None:
                        for ao in animation.animation_objects[:]:
                            if ao.parent==c:
                                animation.animation_objects.remove(ao)
                    return               
        if len(self.env._standbylist)>0:
            self.env._pendingstandbylist=list(self.env._standbylist)
            self.env._standbylist=[]

        (t,_,c)=heapq.heappop(self._event_list)
        self.env._now=t

        try:
            self.env._current_component=c
            if c._process is None: #denotes end condition
                return
                   
            c._status=current
            self.print_trace('%10.3f' % self._now,c._name,\
              'current'+_atprocess(c._process)) 
            _check_fail(c)
            c._scheduled_time=inf
            next(c._process)
            return
        except StopIteration:
            self.print_trace('%10.3f' % self._now,c._name,'ended')
            c._status=data
            c._scheduled_time=inf
            c._process=None
            if animation!=None:
                for ao in animation.animation_objects[:]:
                    if ao.parent==c:
                        animation.animation_objects.remove(ao)
            return
        
    @property
    def peek(self):
        '''
        returns the time of the next component to become current
        
        if there are no more events, peek will return inf
        
        for advance use with animation / GUI event loops
        '''
        if len(self.env._pendingstandbylist)>0:
            return self.env._now
        else:
            if len(self.env._event_list)==0:
                return inf
            else:
                return self.env._event_list[0][0]
        pass
            

    @property
    def main(self):
        '''
        returns the main component
        '''
        return self._main
        
    @property
    def now(self):
        '''
        returns the current simulation time
        '''   
        return self._now 
            
    @property
    def trace(self,value=None):
        '''
        returns and/or sets the value
        '''
        return self._trace
        
    @trace.setter
    def trace(self,value):
        '''
        returns and/or sets the value
        '''
        self._trace=value
        
    @property
    def current_component(self):
        '''
        returns the current_component
        
        arguments:
            none
        '''
        return self._current_component


    def run(self,duration=None,till=None,animate=False,animation_speed=None):
        '''
        start execution of the simulation

        arguments:
            duration      schedule with a delay of duration
                          if 0, now is used
            till          schedule time
                          if omitted, 0 is assumed
        if neither duration nor till are specified,
          the run will last for an infite time
        only issue this from the main level
        '''


        if animate:        
            if animation is None:
                raise AssertionError('animation is not initialized')
            if animation.env!=self:
                raise AssertionError\
                  ('animation is not initialized for this environment')
            if animation_speed!=None:
                animation.animation_speed=animation_speed
            animation.paused=False

        if till is None:
            if duration is None:
                scheduled_time=inf
            else:
                if duration==inf:
                    scheduled_time=inf
                else:
                    scheduled_time=self.env._now+duration
        else:
            if duration is None:
                scheduled_time=till
            else:
                raise AssertionError('both duration and till specified')
                
        if scheduled_time<self.env._now:
            raise AssertionError(\
              'scheduled time (%0.3f) before now'%scheduled_time)                           
                
        if scheduled_time==inf:
            self.print_trace('','','main','scheduled for        inf') 
        else:
            self.print_trace('','','main',\
              'scheduled for %10.3f'%scheduled_time) 
                        
        self._main._status=scheduled
        self._scheduled_time=scheduled_time
        self._main._push(scheduled_time,False)
        if animate:
            animation.start_animation_time=self._now
            animation.start_animation_clocktime=time.time()

            animation.running=True
            if Pythonista:
                while animation.running:
                    pass
            else:
                animation.root.after(0,self.simulate_and_animate_loop)
                animation.root.mainloop()
            
        else:
            self.simulate_loop()

    def simulate_loop(self):
        while True:
            self.env.step()
            if self.env._current_component==self._main:
                self.print_trace\
                  ('%10.3f' % self._now,self._main._name,'current')                            
                self._scheduled_time=inf
                self._status=current
                return
                
    def simulate_and_animate_loop(self):
        global animation
        animation.running=True
        while animation.running:
            
            if animation.paused:
                t=animation.start_animation_time
            else:
                t=animation.start_animation_time+\
                  ((time.time()-animation.start_animation_clocktime)*\
                  animation.animation_speed)
            animation.t=t
            while self.peek<t:
                self.step()
                if self.env._current_component==self._main:
                    self.print_trace('%10.3f' % self._now,\
                      self._main._name,'current')                            
                    self._scheduled_time=inf
                    self._status=current
                    animation.running=False
                    animation.root.quit()
                    return

            for co in animation.canvas_objects:
                animation.canvas.delete(co)
            animation.canvas_objects=[]
             
            animation.animation_objects.sort\
              (key=lambda obj:(-obj.layer,obj.sequence))
            
            for ao in animation.animation_objects:
                if type(ao) == Component.Animate:
                    im,x,y=ao.pil_image(t)
                    if im!=None:
                        ao.im = ImageTk.PhotoImage(im)
                        r=animation.canvas.create_image(\
                          x,animation.height-y,image=ao.im,anchor=tkinter.SW)                 
                        animation.canvas_objects.append(r)                    
                else:
                    if ao.type=='button':
                        thistext=str_or_function(ao.text)
                        if thistext!=ao.lasttext:
                            ao.lasttext=thistext
                            ao.button.config(text=thistext)
                    elif ao.type=='slider':
                        pass
                    
            animation.canvas.update()
            time.sleep(1/animation.fps)
        
    @property
    def name(self):
        '''
        returns and/or sets the name of an environmnet
        
        arguments:
            txt     name of the queue
                    if txt ends with a period, the name will be serialized
        '''
        return self._name
        
    @name.setter
    def name(self,txt):
        self._name,self._base_name,self._sequence_number=\
          self.env._reformatnameQ(txt)
        
    @property
    def base_name(self):
        '''
        returns the base name of an environment
          (the name used at init or name)
        '''
        return self._base_name        

    @property
    def sequence_number(self):
        '''
        returns the sequence_number of an environment
          (the sequence number at init or name)

        normally this will be the integer value of a serialized name,
        but also non serialized names (without a dot at the end)
          will be numbered)
        '''
        return self._sequence_number        


    def print_trace(self,s1='',s2='',s3='',s4=''):
        if self._trace:
             if not self._current_component._suppress_trace:
                 print(pad(s1,10)+' '+pad(s2,20)+' '+pad(s3,35)+' '+s4)    
        
    def _reformatnameC(self,name):
        return _reformatname(name,self._nameserializeC)
        
    def _reformatnameQ(self,name):
        return _reformatname(name,self._nameserializeQ)

    def _reformatnameR(self,name):
        return _reformatname(name,self._nameserializeR)        

class Component(object): 
    '''
    component object
    
    arguments:
        name              name of the component.
                          if the name ends with a period (.), 
                            auto serializing will be applied
                          if omitted, the name will be derived from the class 
                            it is defined in lowercased)
        at                schedule time
                          if omitted, now is used
        delay             schedule with a delay
                          if omitted, no delay
        urgent            if False (default), the component will be scheduled
                            behind all other components scheduled
                            for the same time
                          if True, the component will be scheduled 
                            in front of all components scheduled
                            for the same time
        auto_start        if there is a process generator defined in the
                             component class, this will be activated 
                             automatically, unless overridden with auto_start
                          if there is no process generator, no activation 
                            takes place, anyway
        env               environment where the component is defined
                          if omitted, default_env will be used
                            
    usually, a component will be defined as a subclass of Component
    '''
    
    def __init__(self,name=None,at=None,delay=None,urgent=False,\
      auto_start=True,suppress_trace=False,env=None): 
        if env is None:
            self.env=default_env
        else:
            self.env=env
        if name is None:
            name=str(type(self)).split('.')[-1].split("'")[0].lower()+'.'
        self._name,self._base_name,\
          self._sequence_number = self.env._reformatnameC(name)
        self._qmembers={}
        self._process=None
        self._status=data
        self._requests={}
        self._pendingclaims=[]
        self._claims={}
        self._scheduled_time=inf
        self._request_failed=False
        self._creation_time=self.env._now
        self._suppress_trace=suppress_trace
        hasprocess=True
        try:
            process=self.process()
        except AttributeError:
            hasprocess=False
        if hasprocess and auto_start:
            self.activate(process=process,at=at,delay=delay,urgent=urgent)
        
    def __repr__(self):
        lines=[]
        lines.append('Component '+hex(id(self)))
        lines.append('  name= '+self._name)
        lines.append('  class='+str(type(self)).split('.')[-1].split("'")[0])
        lines.append('  suppress_trace='+str(self._suppress_trace))
        lines.append('  status='+self._status)
        lines.append('  creation_time='+time_to_string(self._creation_time))
        lines.append('  scheduled_time='+time_to_string(self._scheduled_time))
        if len(self._qmembers)>0:
            lines.append('  member of queue(s):')
            for q in sorted(self._qmembers,key=lambda obj:obj._name.lower()):
                lines.append('    '+pad(q._name,20)+' enter_time='+\
                  time_to_string(self._qmembers[q].enter_time)+\
                  ' priority='+str(self._qmembers[q].priority))
        if len(self._requests)>0:
            if self._greedy:
                lines.append('  greedy requesting resource(s):')
            else:
                lines.append('  requesting resource(s):')
                
            for r in sorted(list(self._requests),\
              key=lambda obj:obj._name.lower()):
                if r in self._pendingclaims:
                    lines.append('    '+pad(r._name,20)+' quantity='+\
                      str(self._requests[r])+' provisionally claimed')
                else:
                    lines.append('    '+pad(r._name,20)+' quantity='+\
                      str(self._requests[r]))
        if len(self._claims)>0:
            lines.append('  claiming resource(s):')
                
            for r in sorted(list(self._claims),key=\
              lambda obj:obj._name.lower()):
                lines.append('    '+pad(r._name,20)+\
                  ' quantity='+str(self._claims[r]))
        return '\n'.join(lines)
                
    def _push(self,t,urgent):
        self.env._seq+=1
        if urgent:
            seq=-self.env._seq
        else:
            seq=self.env._seq
        heapq.heappush(self.env._event_list,(t,seq,self))
    
    def _remove(self):
        for i in range(len(self.env._event_list)):
            if self.env._event_list[i][2]==self:
                self.env._event_list[i]=self.env._event_list[0]
                heapq.heapify(self.env._event_list)
                return
        raise AssertionError('remove error')
     
    def _reschedule(self,scheduled_time,urgent,caller):
        if scheduled_time<self.env._now:
            raise AssertionError(\
              'scheduled time (%0.3f) before now'%scheduled_time)                           
        if self._scheduled_time!=inf:
            self._remove() 
        self._scheduled_time=scheduled_time                       
        if scheduled_time==inf:
            self._status=passive
            self.env.print_trace('','',caller+' '+self._name,'(passivate)')
        else:                     
            self._push(scheduled_time,urgent)
            self._status=scheduled
            self.env.print_trace('','',self._name+' '+caller,\
              ('scheduled for %10.3f'%scheduled_time)+\
              _urgenttxt(urgent)+_atprocess(self._process))        
           
    def reschedule(self,process=None,at=None,delay=None,urgent=False):
        '''
        reschedule component

        arguments:
            process       process to be started
                          if omitted, process will not be changed
            at            schedule time
                          if omitted, now is used
                          if inf, this results in a passivate
            delay         schedule with a delay
                          if omitted, no delay
            urgent        if False (default), the component will be scheduled
                            behind all other components scheduled
                            for the same time
                          if True, the component will be scheduled 
                            in front of all components scheduled
                            for the same time
        if to be applied for the current component, use yield reschedule.
        '''
  
        if at is None:
            if delay is None:
                scheduled_time=self.env._now
            else:
                if delay==inf:
                    scheduled_time=inf
                else:
                    scheduled_time=self.env._now+delay
        else:
            if delay is None:                
                scheduled_time=at
            else:
                raise AssertionError('both at and delay specified') 
        if process!=None:
            self._process=process
        self._reschedule(scheduled_time,urgent,'reschedule')
                      
    def activate(self,process=None,at=None,delay=None,urgent=False):
        '''
        activate component

        arguments:
            process       process to be started
                          if omitted, the process called process() will be used
                          note that the function *must* be a generator,
                            i.e. contains at least one yield.
            at            schedule time
                          if omitted, now is used
                          if inf, this results in a passivate
            delay         schedule with a delay
                          if omitted, no delay
            urgent        if False (default), the component will be scheduled
                            behind all other components scheduled
                            for the same time
                          if True, the component will be scheduled 
                            in front of all components scheduled
                            for the same time
        if to be applied for the current component, use yield activate.
        '''
        if process is None:
            try:
                self._process=self.process()
            except AttributeError:
                raise AssertionError('default '+self._name+
                '.process() not found')
        else:
            self._process=process
        if at is None:
            if delay is None:
                scheduled_time=self.env._now
            else:
                if delay==inf:
                    scheduled_time=inf
                else:
                    scheduled_time=self.env._now+delay
        else:
            if delay is None:                
                scheduled_time=at
            else:
                raise AssertionError('both at and delay specified') 
                
        if scheduled_time==inf:
            raise AssertionError('inf not allowed')
        self._request_failed=False
          # ensures that an activate of a cancelled component resets
          # the failed state
        self._reschedule(scheduled_time,urgent,'activate')
                    
    def reactivate(self,at=None,delay=None,urgent=False):
        '''
        reactivate component

        arguments:
            at            schedule time
                          if omitted, now is used
                          if inf, this results in a passivate
            delay         schedule with a delay
                          if omitted, no delay
            urgent        if False (default), the component will be scheduled
                            behind all other components scheduled
                            for the same time
                          if True, the component will be scheduled 
                            in front of all components scheduled
                            for the same time
          
        if to be applied for the current component, use yield activate.
        '''
        self._checknotcurrent()
        self._checkispassive()                 

        if at is None:
            if delay is None:
                scheduled_time=self.env._now
            else:
                if delay==inf:
                    scheduled_time=inf
                else:
                    scheduled_time=self.env._now+delay
        else:
            if delay is None:                
                scheduled_time=at
            else:
                raise AssertionError('both at and delay specified') 
                
        self._reschedule(scheduled_time,urgent,'reactivate')
                        
    def hold(self,duration=None,till=None,urgent=False):
        '''
        hold the current component

        arguments:
            duration      schedule with a delay of duration
                          if 0, now is used
            till          schedule time
                          if omitted, no delay
            urgent        if False (default), the component will be scheduled
                            behind all other components scheduled
                            for the same time
                          if True, the component will be scheduled 
                            in front of all components scheduled
                            for the same time
        *always* use as yield self.hold(...)
        '''

        self._checkcurrent()       
        if till is None:
            if duration is None:
                scheduled_time=self.env._now
            else:
                if duration==inf:
                    scheduled_time=inf
                else:
                    scheduled_time=self.env._now+duration
        else:
            if duration is None:
                scheduled_time=till
            else:
                raise AssertionError('both duration and till specified')
                
        self._reschedule(scheduled_time,urgent,'hold')
        
    def passivate(self,reason=''):
        '''
        passivate the current component

        arguments:
            none

        *always* use as self.yield passivate()
        '''
        self._checkcurrent()          
        self.env.print_trace('','','passivate')
        self._scheduled_time=inf
        self._passive_reason=reason
        self._status=passive
                        
    def cancel(self):
        '''
        cancel component (makes the component data)

        arguments:
            none
          
        if to be applied for the current component, use yield cancel()
        '''
        self.env.print_trace('','','cancel '+self._name)
           
        _check_fail(self)
        self._process=None
        if self._scheduled_time!=inf:
            self._remove()
        self._scheduled_time=inf
        self._status=data
      
    def standby(self):
        '''
        puts the current container in standby mode
        
        arguments:
            none
        
        *always* use as yield self.standby()        
        '''
        if self!=self.env._current_component:
            raise AssertionError(self._name+' is not current')            
        self.env.print_trace('','','standby')
        self._scheduled_time=self.env._now
        self.env._standbylist.append(self)
        self._status=standby
         
    def stop_run(self):
        '''
        stops the simulation and gives control to the main program, immediate

        arguments:
            none
        always use yield self.stop_run()
        '''
        scheduled_time=self.env._now
        self.env.print_trace('','','run_stop ',\
          'scheduled for=%10.3f'%scheduled_time)

        if self.env._main._scheduled_time!=inf: # just to be sure
            self.env._main._remove()
        self.env._main._scheduled_time=scheduled_time
        self.env._main._push(scheduled_time,urgent=True)
        self.env._main._status=scheduled

    def request(self,*args,priority=None,greedy=False,fail_at=None):
        '''
        request from a resource or resources
        
        arguments:
            *args             a sequence of requested resources
                              each resource can be optionally followed by a
                              quantity and a priority 
                              if the quantity is not specified, 1 is assumed
                              if the priority is not specified, this request
                              for the resources be added to the tail of
                              the requesters queue 
                              alternatively, the request for a resource may
                              be specified as a list or tuple containing
                              the resource name, the quantity and the 
                              priority
            greedy            if False (default), the request will be honoured
                              at once when all requested quantities of the
                              resources are available
                              if True, the components puts a pending claim
                              already when sufficient capacity is available.
                              When the requests cannot be honoured finally,
                              all pending requests will be released.
            fail_at           if the request is not honoured before fail_at,
                              the request will be cancelled and the
                              parameter request_failed will be set.
                              if not specified, the request will not time out. 
                              
        it is not allowed to claim a resource more than once
        the rquested quantity may exceed the current capacity of a resource
        the parameter request_failed will be reset by calling request
        
        *always* use as yield self.request(...)
        '''
        if fail_at is None:
            scheduled_time=inf
        else:
            scheduled_time=fail_at

        self._checkcurrent()
        self._greedy=greedy

        self._request_failed=False
        i=0
        while i<len(args):
            q=1
            priority=None
            argsi=args[i]
            if type(argsi)==Resource:
                r=argsi
                if i+1<len(args):
                    if type(args[i+1]) not in (Resource,list,tuple):
                        i+=1
                        q=args[i]
                if i+1<len(args):
                    if type(args[i+1]) not in (Resource,list,tuple):
                        i+=1
                        priority=args[i]
                    
            else:
                r=argsi[0]
                if len(argsi)>=2:
                    q=argsi[1]
                    if len(argsi)>=3:
                        priority=argsi[2]
                        
            if r in self._requests:
                raise AssertionError(resource._name+' requested twice')
            if q<=0:
                raise AssertionError('quantity '+str(q)+' <=0')
            self._requests[r]=q
            if self._greedy:
                addstring=' greedy'
            else:
                addstring=''
            if priority is None:
                self._enter(r._requesters)
            else:
                addstring=addstring+' priority='+str(priority)
                self._enter_sorted(r._requesters,priority)
            self.env.print_trace('','',self._name,\
              'request for '+str(q)+' from '+r._name+addstring)

            i+=1
            
        for r in list(self._requests):
            r._claimtry()
            
        if len(self._requests)!=0:
            self._push(scheduled_time,False)
        
    def _release(self,r,q):
        if not r in self._claims:
            raise AssertionError(self._name+\
              ' not claiming from resource '+r._name)
        if q is None:
            q=self._claims[r]
        if q>self._claims[r]:
            q=self.claimers[r]        
        r._claimed_quantity-=q
        self._claims[r]-=q
        if self._claims[r]<1e-8:
            self.leave(r._claimers)
            if r._claimers._length==0:
                r._claimed_quantity=0 #to avoid rounding problems
            del self._claims[r]
        self.env.print_trace('','',self._name,\
          'release '+str(q)+' from '+r._name)
        r._claimtry()    
            
    def release(self,*args):
        '''
        releases a quantity from a resource or resources
        arguments:
            *args             a sequence of requested resources to be released
                              each resource can be optionally followed by a
                              quantity
                              if the quantity is not specified, the current
                              alternatively, the release for a resource may
                              be specified as a list or tuple containing
                              the resource name and a quantity
        '''
        if len(args)==0:
            for r in list(self._claims.keys()):
                self._release(r,None)                
                
        else:
            i=0
            while i<len(args):
                q=None
                argsi=args[i]
                if type(argsi)==Resource:
                    r=argsi
            
                    if i+1<len(args):
                        if type(args[i+1]) not in (Resource,list,tuple):
                            i+=1
                            q=args[i]
                else:
                    r=argsi[0]
                    if len(argsi)>=2:
                        q=argsi[1]
                self._release(r,q)       
                i=i+1
        
            
    def claimed_quantity(self,resource):
        '''
        returns the claimed quantity from a resource
        
        arguments:
            resource     resource to be queried
        
        if the resource is not claimed, 0 will be returned
        '''
        if resource in self._resources:
            return self._resources[resource]
        else:
            return 0
            
    @property
    def claimed_resources(self):
        '''
        returns a list of claimed resources
        '''
        l=[]
        for r in self._resources:
            l.append(r)
        return l

    @property
    def request_failed(self):
        '''
        returns whether the latest request has failed
        '''
        return self._request_failed
        
    @property
    def name(self,txt=None):
        '''
        gets and/or sets the name of a component
        
        arguments:
            txt      name of the component
                     if txt ends with a period, the name will be serialized
                     if omitted, the name will not be changed
        '''
        return self._name
        
    @name.setter
    def name(self,txt):
        self._name,self._base_name,\
          self._sequence_number=self.env._reformatnameC(txt)
        
    @property
    def base_name(self):
        '''
        returns the base name of a component (the name used at init or name)
        '''
        return self._base_name        

    @property
    def sequence_number(self):
        '''
        returns the sequence_number of a component
          (the sequence number at init or name)

        normally this will be the integer value of a serialized name,
        but also non serialized names (without a dot at the end)
          will be numbered 
        '''
        return self._sequence_number
        
        
    @property
    def suppress_trace(self):
        return self._suppress_trace
        
    @suppress_trace.setter
    def suppress_trace(self,value):
        self._suppress_trace=value
        
    @property
    def is_passive(self):
        '''
        return True if status is passive, False otherwise
        '''
        return self.status==passive
        
    @property
    def is_current(self):
        '''
        return True if status is current, False otherwise
        '''
        return self.status==current
        
    @property
    def is_scheduled(self):
        '''
        return True if status is scheduled, False otherwise
        '''
        return self.status==scheduled
        
    @property
    def is_standby(self):
        '''
        return True if status is standby, False otherwise
        '''
        return self.status==standby   
        
    @property
    def is_data(self):
        '''
        return True if status is data, False otherwise
        '''
        return self.status==data   
                        
    @property
    def main(self):
        '''
        returns the main component
        '''
        return self.env.main
        
    @property
    def now(self):
        '''
        returns the current simulation time
        '''   
        return self.env.now 
            
    @property
    def current_component(self):
        '''
        returns the current component
        '''   
        return self.env.current_component


    @property
    def trace(self,value=None):
        '''
        returns and/or sets the value
        '''
        return self.env._trace
        
    @trace.setter
    def trace(self,value):
        '''
        returns and/or sets the value
        '''
        self.env._trace=value
        
    @property
    def current_component(self):
        '''
        returns the current component
        '''
        return self.env.current_component

    
    def is_in_queue(self,q):
        '''
        check to see whether component is in a queue
        
        argments:
            q                       queue to be checked against
            
        returns True if the component is in q, False otherwise.
        '''
        return self._member(q)!=None
        
    def index_in_queue(self,q):
        '''
        get indez of component in a queue
        
        argments:
            q                       queue to be used
            
        Returns the index of component in q, if component belongs to q
        Returns -1 if component does not belong to q
        '''
        m1=self._member(q)
        if m1 is None:
            return -1
        else:
            mx=q._head.successor
            index=0
            while mx!=m1:
                mx=mx.successor
                index+=1
            return index    
        

    def _enter(self,q):
        savetrace=self.env._trace
        self.env._trace=False
        self.enter(q)
        self.env._trace=savetrace

    def enter(self,q):
        '''
        enters a queue at the tail
        
        arguments:
            q                      queue to enter
            
        the priority will be set to
          the priority of the tail of the queue, if any
          or 0 if queue is empty
        '''
        self._checknotinqueue(q)
        priority=q._tail.predecessor.priority
        Qmember().insert_in_front_of(q._tail,self,q,priority)

    def enter_at_head(self,q):
        '''
        enters a queue at the head
        
        arguments:
            q                      queue to enter
            
        the priority will be set to
          the priority of the head of the queue, if any
          or 0 if queue is empty
        '''
        self._checknotinqueue(q)
        priority=q._head.successor.priority
        Qmember().insert_in_front_of(q._head.successor,self,q,priority)
                   
    def enter_in_front_of(self,q,poscomponent):
        '''
        enters a queue in front of a component
        
        arguments:
            q                      queue to enter
            poscomponent           component to entered in front of
                                   must be member of q
            
        the priority will be set to the priority of poscomponent
        '''
        self._checknotinqueue(q)
        m2=poscomponent._checkinqueue(q)
        priority=m2.priority
        Qmember().insert_in_front_of(m2,self,q,priority)

    def enter_behind(self,q,poscomponent):
        '''
        enters a queue behind a component
        
        arguments:
            q                      queue to enter
            poscomponent           component to entered behind
                                   must be member of q
            
        the priority will be set to the priority of poscomponent
        '''
        self._checknotinqueue(q)
        m1=poscomponent._checkinqueue(q)
        priority=m1.priority
        Qmember().insert_in_front_of(m1.successor,self,q,priority)
        
    def enter_sorted(self,q,priority):
        '''
        enters a queue, according ti the priority
        
        arguments:
            q                      queue to enter
            priority               used to sort the component in the queue
        '''

        self._checknotinqueue(q)
        m2=q._head.successor
        while (m2!=q._tail) and (m2.priority<=priority):
            m2=m2.successor
        Qmember().insert_in_front_of(m2,self,q,priority)
        
    def _enter_sorted(self,q,priority):
        savetrace=self.env._trace
        self.env._trace=False
        self.enter_sorted(q,priority)
        self.env._trace=savetrace        
          
    def _leave(self,q):
        savetrace=self.env._trace
        self.env._trace=False
        self.leave(q)
        self.env._trace=savetrace
        
    def leave(self,q):
        '''
        leave queue
        
        argumnents:
            q                       queue to leave
        
        statistics are updated accordingly
        '''

        mx=self._checkinqueue(q)
        m1=mx.predecessor
        m2=mx.successor
        m1.successor=m2
        m2.predecessor=m1
        mx.component=None
          # signal for components method that memeber is not in the queue
        q._number_passed+=1
        length_of_stay=self.env._now-mx.enter_time       
        if length_of_stay==0:
            q._number_passed_direct+=1
        q._total_length_of_stay+=length_of_stay
        q._minimum_length_of_stay=min(q._minimum_length_of_stay,length_of_stay)
        q._maximum_length_of_stay=max(q._maximum_length_of_stay,length_of_stay)
        q._length-=1
        q._minimum_length=min(q._minimum_length,q._length)
        del self._qmembers[q]
        self.env.print_trace('','',self._name, 'leave '+q._name)                 
        
    def get_priority(self,q):
        '''
        gets the priority of a component in a queue
        
        arguments:
            q                       queue where the component belongs to
        '''
        mx=self._checkinqueue(q)
        return mx.priority


    def set_priority(self,q,priority):
        '''
        sets the priority of a component in a queue
        
        arguments:
            q                       queue where the component belongs to
            priority                used to resort the component in a queue

        the order of the queue may be changed
        '''
        mx=self._checkinqueue(q)
        if priority!=mx.priority:
           self.leave(q)
           self.enter_sorted(q,priority)
           if q._resource!=None:
               q._resource._claimtry()
        
    def successor(self,q):
        '''
        successor of component in a queue
        
        arguments:
            q                       queue where conponent belongs to
        returns the successor of the component in the queue if component is not at the tail.
        returns None if component is at the tail
        ''' 
        mx=self._checkinqueue(q)
        return mx.successor.component

    def predecessor(self,q):
        '''
        predecessor of component in a queue
        
        arguments:
            q                       queue where conponent belongs to
        returns the precessor of the component in the queue if component is at not the head
        returns None if component is at the head
        '''
        mx=self._checkinqueue(q)
        return mx.predecessor.component
        
    def enter_time(self,q):
        '''
        time the component entered the queue
        
        arguments:
            q                       queue where component belongs to
        returns the time the component entered the queue
        '''
        mx=self._checkinqueue(q)
        return mx.enter_time
        
    @property
    def creation_time(self):
        '''
        returns the time the component was created
        
        arguments:
            none
        returns the time the component was created
        '''
        
        return self._creation_time
        
    @property
    def scheduled_time(self):
        '''
        returns the time the component is scheduled for
        
        arguments:
            none
        returns the time the component scheduled for, if it is scheduled
        returns inf otherwise
        '''
        return self._scheduled_time
    
    @property
    def current_component(self):
        '''
        returns the current_component
        
        arguments:
            none
        returns the current component
        '''
        return self.env._current_component

    @property
    def status(self):
        '''
        returns the status of a  component
        
        arguments:
            none
        returns the status of a component
        possible values are
            data
            passive
            scheduled
            current
            standby
        '''
        
        return self._status
        
    @property
    def passive_reason(self):
        '''
        returns the passive_reason of a component
         
        arguments:
            none
        returns the passive_reason (as given with the passivate call, if passive
        returns None if not passive
        '''
        if self._status==passive:
            return self._passive_reason
        else:
            return None

    class Animate(object):
        '''
        defines an animation object
        
        arguments:
            layer         lower layer values are on top of higher layer values (default 0)
            parent        component where this animation object belongs to (default None)
                          if given, the animation ofject will be removed automatically upon termination of
                          the parent component
            keep          if False, animation object is hidden after t1, shown otherwise
            t0            time of start of the polygon animation
            x0            x-coordinate of the origin (default 0) at time t0
            y0            y-coordinate of the origin (default 0) at time t0
            offsetx0      offsets the x-coordinate of the object (default 0) at time t0
            offsety0      offsets the y-coordinate of the object (default 0) at time t0

            circle0       the circle at time t0 (radius,)
            line0         the line(s) at time t0 (xa,ya,xb,yb,xc,yc, ...)
            polygon0      the polygon at time t0 (xa,ya,xb,yb,xc,yc, ...) the last point will be auto connected to the start
            rectangle0    the rectangle at time t0 (xlowerleft,ylowerlef,xupperright,yupperright)
            image         the image to be displayed. This may be either a filename or a PIL image
            text          the text to be displayed

            font          font to be used for texts. Either a string or a list/tuple of fontnames. If not found, uses calibri or arial
            linewidth0    linewidth of the contour at time t0 (default 0 = no contour)
            fillcolor0    color of interior/text at time t0 (default black)
            linecolor0    color of the contour at time t0 (default black)
            angle0        angle of the polygon at time t0 (in degrees) (default 0)
            fontsize0     fontsize of text at time t0 (default: 20)
            width0        width of the image to be displayed (default: no scaling)

            x1            x-coordinate of the origin (default x0) at time t0
            y1            y-coordinate of the origin (default y0) at time t0
            offsetx1      offsets the x-coordinate of the object (default offsetx0) at time t1
            offsety1      offsets the y-coordinate of the object (default offsety0) at time t1
            circle1       the circle at time t1 (radius,) (default circle0)
            line1         the line(s) at time t1 (xa,ya,xb,yb,xc,yc, ...) (default line0)
            polygon1      the polygon at time t1 (xa,ya,xb,yb,xc,yc, ...) (default polygon01)
            rectangle1    the rectangle at time t1 (xlowerleft,ylowerleft,xupperright,yupperright) (default rectangle0)

            linewidth1    linewidth of the contour at time t1 (default linewidth0)
            fillcolor1    color of interior/text at time t1 (default fillcolor0)
            linecolor1    color of the contour at time t1 (default linecolor0)
            angle1        angle of the polygon at time t1 (in degrees) (default angle0)
            fontsize1     fontsize of text at time t1 (default: fontsize0)
            width1        width of the image to be displayed (default: width0)
        
        colors may be specified as a valid colorname, a hexname, or a tuple (R,G,B) or (R,G,B,A)
        colornames may contain an additional alpha, like red#7f
        hexnames may be either 3 of 4 bytes long (RGB or RGBA)
        both colornames and hexnames may be given as a tuple with an additional alpha between 0 and 255,
          e.g. ('red',127) or ('#ff00ff',128)
        '''

        def pil_image(self,t):
            
            if ((t>=self.t0) and (t<=self.t1)) or self.keep:
                x=interpolate(t,self.t0,self.t1,self.x0,self.x1)
                y=interpolate(t,self.t0,self.t1,self.y0,self.y1)
                offsetx=interpolate(t,self.t0,self.t1,self.offsetx0,self.offsetx1)
                offsety=interpolate(t,self.t0,self.t1,self.offsety0,self.offsety1)
                angle=interpolate(t,self.t0,self.t1,self.angle0,self.angle1)
                                            
                if (self.type=='polygon') or (self.type=='rectangle') or (self.type=='line'):
                    linewidth=interpolate(t,self.t0,self.t1,self.linewidth0,self.linewidth1)*animation.scale
                    linecolor=interpolate(t,self.t0,self.t1,self.linecolor0,self.linecolor1)
                    fillcolor=interpolate(t,self.t0,self.t1,self.fillcolor0,self.fillcolor1)
            
                    cosa=math.cos(angle*math.pi/180)
                    sina=math.sin(angle*math.pi/180)                    

                    if self.type=='rectangle': 
                        p0=[
                         self.rectangle0[0],self.rectangle0[1],
                         self.rectangle0[2],self.rectangle0[1],
                         self.rectangle0[2],self.rectangle0[3],
                         self.rectangle0[0],self.rectangle0[3],
                         self.rectangle0[0],self.rectangle0[1]]

                        p1=[
                         self.rectangle1[0],self.rectangle1[1],
                         self.rectangle1[2],self.rectangle1[1],
                         self.rectangle1[2],self.rectangle1[3],
                         self.rectangle1[0],self.rectangle1[3],
                         self.rectangle1[0],self.rectangle1[1]]

                    elif self.type=='line':
                        p0=self.line0
                        p1=self.line1
                        fillcolor=(0,0,0,0)

                    else:
                        p0=self.polygon0
                        p1=self.polygon1
            
                    if self.screen_coordinates:
                        qx=x
                        qy=y
                    else:
                        qx=(x-animation.x0)*animation.scale
                        qy=(y-animation.y0)*animation.scale

                    r=[]
                    minrx=inf
                    minry=inf
                    maxrx=-inf
                    maxry=-inf
                    for i in range(0,len(p0),2):
                        px=interpolate(t,self.t0,self.t1,p0[i],p1[i])+offsetx
                        py=interpolate(t,self.t0,self.t1,p0[i+1],p1[i+1])+offsety
                        rx=px*cosa-py*sina
                        ry=px*sina+py*cosa
                        if not self.screen_coordinates:
                            rx=rx*animation.scale
                            ry=ry*animation.scale
                        minrx=min(minrx,rx)
                        maxrx=max(maxrx,rx)
                        minry=min(minry,ry)
                        maxry=max(maxry,ry)
                        r.append(rx)
                        r.append(ry)
                    if self.type=='polygon':
                        if (r[0]!=r[len(r)-2]) or (r[1]!=r[len(r)-1]): # connect with start point
                            r.append(r[0])
                            r.append(r[1])
                            
                                                
            
                    rscaled=[]
                    for i in range(0,len(r),2):
                        rscaled.append(r[i]-minrx+linewidth)
                        rscaled.append(maxry-r[i+1]+linewidth)
                    rscaled=tuple(rscaled) #to make it hashable
            
                    if (rscaled,minrx,maxrx,minry,maxry,fillcolor,linecolor,linewidth) in self.image_cache:
                        im1=self.image_cache[(rscaled,minrx,maxrx,minry,maxry,fillcolor,linecolor,linewidth)]
                    else:
                        im1=Image.new('RGBA',(int(maxrx-minrx+2*linewidth),int(maxry-minry+2*linewidth)),(0,0,0,0))
                        draw=ImageDraw.Draw(im1)
                        if fillcolor[3]!=0:
                            draw.polygon(rscaled,fill=fillcolor)
                        if (linewidth>0) and (linecolor[3]!=0):
                            draw.line(rscaled,fill=linecolor,width=int(linewidth))
                           
                        self.image_cache[(rscaled,minrx,maxrx,minry,maxry,fillcolor,
                            linecolor,linewidth)]=im1
                    zx=qx+minrx-linewidth
                    zy=qy+minry-linewidth
                    return (im1,zx,zy)
                    
                elif self.type=='circle':
                    linewidth=interpolate(t,self.t0,self.t1,self.linewidth0,self.linewidth1)*animation.scale
                    fillcolor=interpolate(t,self.t0,self.t1,self.fillcolor0,self.fillcolor1)
                    linecolor=interpolate(t,self.t0,self.t1,self.linecolor0,self.linecolor1)
                    radius=interpolate(t,self.t0,self.t1,self.circle0[0],self.circle1[0])
                    

                    if self.screen_coordinates:
                        qx=x
                        qy=y
                    else:
                        qx=(x-animation.x0)*animation.scale
                        qy=(y-animation.y0)*animation.scale
                        linewidth*=animation.scale
                        radius*=animation.scale


                    if (radius,linewidth,linecolor,fillcolor) in self.image_cache:
                        im1=self.image_cache[(radius,linewidth,linecolor,fillcolor)]
                    else:
                        nsteps=int(math.sqrt(radius)*6)
                        tangle=2*math.pi/nsteps
                        sint=math.sin(tangle)
                        cost=math.cos(tangle)
                        p=[]
                        x=radius
                        y=0
                        
                        
                        for i in range(nsteps+1):
                            x,y=(x*cost-y*sint,x*sint+y*cost)
                            p.append(x+radius+linewidth)
                            p.append(y+radius+linewidth)
                            

                        im1=Image.new('RGBA',(int(radius*2+2*linewidth),int(radius*2+2*linewidth)),(0,0,0,0))
                        draw=ImageDraw.Draw(im1)
                        if fillcolor[3]!=0:
                            draw.polygon(p,fill=fillcolor)
                        if (linewidth>0) and (linecolor[3]!=0):
                            draw.line(p,fill=linecolor,width=int(linewidth))
                        self.image_cache[(radius,linewidth,linecolor,fillcolor)]=im1                        
                    dx=offsetx
                    dy=offsety
                    cosa=math.cos(angle*math.pi/180)
                    sina=math.sin(angle*math.pi/180)  
                    ex=dx*cosa-dy*sina
                    ey=dx*sina+dy*cosa
                    return(im1,qx+ex-radius-linewidth-1,qy+ey-radius-linewidth-1)
            
                elif self.type=='image':
                    width=interpolate(t,self.t0,self.t1,self.width0,self.width1)
                    height=width*self.image.size[1]/self.image.size[0]
                    angle=interpolate(t,self.t0,self.t1,self.angle0,self.angle1)                        
                    if self.screen_coordinates:
                        qx=x
                        qy=y
                    else:
                        qx=(x-animation.x0)*animation.scale
                        qy=(y-animation.y0)*animation.scale
                        offsetx=offsetx*animation.scale
                        offsety=offsety*animation.scale
                    
                    if (width,height,angle) in self.image_cache:
                        imr,imwidth,imheight,imrwidth,imrheight=self.image_cache[(width,height,angle)]
                    else:
                        if not self.screen_coordinates:
                            width*=animation.scale
                            height*=animation.scale
                        im1 = self.image.resize((int(width),int(height)), Image.ANTIALIAS)
                        imwidth,imheight=im1.size
                        
                        imr = im1.rotate(angle,expand=1)
                        imrwidth,imrheight=imr.size
                        self.image_cache[(width,height,angle)]=(imr,imwidth,imheight,imrwidth,imrheight)
                        
                    anchor_to_dis={'ne':(-0.5,-0.5),'n':(0,-0.5),'nw':(0.5,-0.5),'e':(-0.5,0),'center':(0,0),'w':(0.5,0),'se':(0.5,0.5),'s':(0,0.5),'sw':(0.5,0.5)}
                    dx,dy=anchor_to_dis[self.anchor.lower()]
                    dx=dx*imwidth+offsetx
                    dy=dy*imheight+offsety
                    cosa=math.cos(angle*math.pi/180)
                    sina=math.sin(angle*math.pi/180)  
                    ex=dx*cosa-dy*sina
                    ey=dx*sina+dy*cosa
                    return (imr,qx+ex-imrwidth/2,qy+ey-imrheight/2)
            
                elif self.type=='text':
                    fillcolor=interpolate(t,self.t0,self.t1,self.fillcolor0,self.fillcolor1)                 
                    fontsize=interpolate(t,self.t0,self.t1,self.fontsize0,self.fontsize1)
                    angle=interpolate(t,self.t0,self.t1,self.angle0,self.angle1)                        
                    text=str_or_function(self.text)
                    if self.screen_coordinates:
                        qx=x
                        qy=y
                    else:
                        qx=(x-animation.x0)*animation.scale
                        qy=(y-animation.y0)*animation.scale
                        fontsize=fontsize*animation.scale
                        offsetx=offsetx*animation.scale
                        offsety=offsety*animation.scale
                    
                    if (text,self.font,fontsize,angle,fillcolor) in self.image_cache:
                        imr,imwidth,imheight,imrwidth,imrheight=self.image_cache[(text,self.font,fontsize,angle,fillcolor)]
                    else:
                        font=getfont(self.font,fontsize)
                            
                        width,height=font.getsize(text)
                        im=Image.new('RGBA',(int(width),int(height)),(0,0,0,0))
                        imwidth,imheight=im.size
                        draw=ImageDraw.Draw(im)
                        draw.text(xy=(0,0),text=text,font=font,fill=fillcolor)
                        
                        imr = im.rotate(angle,expand=1)
                        imrwidth,imrheight=imr.size
                        self.image_cache[(text,self.font,fontsize,angle)]=(imr,imwidth,imheight,imrwidth,imrheight)
                    
                    anchor_to_dis={'ne':(-0.5,-0.5),'n':(0,-0.5),'nw':(0.5,-0.5),'e':(-0.5,0),'center':(0,0),'w':(0.5,0),'se':(-0.5,0.5),'s':(0,0.5),'sw':(0.5,0.5)}
                    dx,dy=anchor_to_dis[self.anchor.lower()]
                    dx=dx*imwidth+offsetx
                    dy=dy*imheight+offsety
                    cosa=math.cos(angle*math.pi/180)
                    sina=math.sin(angle*math.pi/180)  
                    ex=dx*cosa-dy*sina
                    ey=dx*sina+dy*cosa
            
                    return(imr,qx+ex-imrwidth/2,qy+ey-imrheight/2)
            return (None,None,None)
    
        def load_image(self,image):
            if type(image)==str:
                im = Image.open(image)
                im = im.convert('RGBA')
                return im
            else:
                return image

        def remove_background(self,im):
            pixels=im.load()
            background=pixels[0,0]
            imagewidth,imageheight=im.size
            for y in range(imageheight):
                for x in range(imagewidth):
                    if abs(pixels[x, y][0]-background[0])<10:
                        if abs(pixels[x, y][1]-background[1])<10:
                            if abs(pixels[x, y][2]-background[2])<10:
                                pixels[x, y] = (255, 255, 255, 0)  
                        
            
        def settype(self,circle,line,polygon,rectangle,image,text):
            n=0
            t=''
            if circle!=None:
                t='circle'
                n+=1
            if line!=None:
                t='line'
                n+=1
            if polygon!=None:
                t='polygon'
                n+=1
            if rectangle!=None:
                t='rectangle'
                n+=1
            if image!=None:
                t='image'
                n+=1
            if text!=None:
                t='text'
                n+=1
            if n>=2:
                raise AssertionError('more than one object given')
            return t                
                
        def __init__(self,parent=None,layer=0,keep=True,screen_coordinates=False,
                t0=None,x0=0,y0=0,offsetx0=0,offsety0=0,
                circle0=None,line0=None,polygon0=None,rectangle0=None,image=None,text=None,
                font='',anchor='center',
                linewidth0=1,fillcolor0='black',linecolor0='black',angle0=0,fontsize0=20,width0=None,
                t1=None,x1=None,y1=None,offsetx1=None,offsety1=None,
                circle1=None,line1=None,polygon1=None,rectangle1=None,
                linewidth1=None,fillcolor1=None,linecolor1=None,angle1=None,fontsize1=None,width1=None):
                        
            self.type=self.settype(circle0,line0,polygon0,rectangle0,image,text)
            if self.type=='':
                raise AssertionError('no object specified')
            type1=self.settype(circle1,line1,polygon1,rectangle1,None,None)
            if (type1!='') and (type1!=self.type):
                raise AssertionError('incompatible types: '+self.type+' and '+ type1)
                
            self.layer=layer
            self.parent=parent
            self.keep=keep
            self.screen_coordinates=screen_coordinates
            self.survive_reset=False
            animation.sequence+=1
            self.sequence=animation.sequence

            self.circle0=circle0
            self.line0=line0
            self.polygon0=polygon0
            self.rectangle0=rectangle0            
            self.text=text
            
            if image is None:
                self.width0=0 #justto be able to intepolate
            else:
                self.image=self.load_image(image)
                self.width0=self.image.size[0] if width0 is None else width0
 
            self.image_cache={}
                
            self.font=font
            self.anchor=anchor
            
            self.x0=x0
            self.y0=y0
            self.offsetx0=offsetx0
            self.offsety0=offsety0

            self.fillcolor0=colorspec_to_tuple(fillcolor0)
            self.linecolor0=colorspec_to_tuple(linecolor0)
            self.linewidth0=linewidth0
            self.angle0=angle0
            self.fontsize0=fontsize0

            self.t0=animation.env._now if t0 is None else t0
    
            self.circle1=self.circle0 if circle1 is None else circle1
            self.line1=self.line0 if line1 is None else line1
            self.polygon1=self.polygon0 if polygon1 is None else polygon1
            self.rectangle1=self.rectangle0 if rectangle1 is None else rectangle1

            self.x1=self.x0 if x1 is None else x1
            self.y1=self.y0 if y1 is None else y1
            self.offsetx1=self.offsetx0 if offsetx1 is None else offsetx1
            self.offsety1=self.offsety0 if offsety1 is None else offsety1
            self.fillcolor1=self.fillcolor0 if fillcolor1 is None else colorspec_to_tuple(fillcolor1)
            self.linecolor1=self.linecolor0 if linecolor1 is None else colorspec_to_tuple(linecolor1)
            self.linewidth1=self.linewidth0 if linewidth1 is None else linewidth1
            self.angle1=self.angle0 if angle1 is None else angle1
            self.fontsize1=self.fontsize0 if fontsize1 is None else fontsize1
            self.width1=self.width0 if width1 is None else width1
            
            self.t1=inf if t1 is None else t1
    
            animation.animation_objects.append(self)
    
        def update(self,layer=None,keep=None,
                t0=None,x0=None,y0=None,offsetx0=None,offsety0=None,
                circle0=None,line0=None,polygon0=None,rectangle0=None,image=None,text=None,font=None,anchor=None,
                linewidth0=None,fillcolor0=None,linecolor0=None,angle0=None,fontsize0=None,width0=None,
                t1=None,x1=None,y1=None,offsetx1=None,offsety1=None,
                circle1=None,line1=None,polygon1=None,rectangle1=None,
                linewidth1=None,fillcolor1=None,linecolor1=None,angle1=None,fontsize1=None,width1=None):
            '''
            updates an animation object
        
            arguments:
                layer         lower layer values are on top of higher layer values (default 0)
                keep          if False, animation object is hidden after t1, shown otherwise
                t0            time of start of the polygon animation
                x0            x-coordinate of the origin at time t0 (default *)
                y0            y-coordinate of the origin at time t0 (default *)
                polygon0      the polygon at time t0 (xa,ya,xb,yb,xc,yc, ...) (default *)
                linewidth0    linewidth of the contour at time t0 (default *)
                fillcolor0    color of interior at time t0 (default *)
                linecolor0    color of the contour at time t0 (default *)
                angle0        angle of the polygon at time t0 (in degrees) (*)
                t1            time of end of the polygon animation
                x1            x-coordinate of the origin at time t1 (default x0)
                y1            y-coordinate of the origin at time t1 (default y0)
                polygon1      the polygon at time t1 (xa,ya,xb,yb,xc,yc, ...) (default polygon0)
                linewidth1    linewidth of the contour at time t1 (default linewidth0)
                fillcolor1    color of interior at time t1 (default fillcolor0)
                linecolor1    color of the contour at time t1 (default linecolor0)
                angle1        angle of the polygon at time t1 (in degrees) (default angle0)
            
            default * means that the current value (at time now) is used
            ''' 

            type0=self.settype(circle0,line0,polygon0,rectangle0,image,text)
            if (type0!='') and (type0!=self.type):
                raise AssertionError('incorrect type '+type0+' (should be '+self.type)
            type1=self.settype(circle1,line1,polygon1,rectangle1,None,None)
            if (type1!='') and (type1!=self.type):
                raise AssertionError('incompatible types: '+self.type+' and '+ type1)

            if layer!=None:
                self.layer=layer
            if keep!=None:
                self.keep=keep
            self.circle0=self.circle() if circle0 is None else circle0
            self.line0=self.line() if line0 is None else line0
            self.polygon0=self.polygon() if polygon0 is None else polygon0
            self.rectangle0=self.rectangle() if rectangle0 is None else rectangle0
            if text!=None: self.text=text
            self.width0=self.width() if width0 is None else width0
            if image!=None:
                self.image=self.load_image(image)
                self.width0==self.image.size[0] if width0 is None else width0
                self.image_cache={} #because the cache might refer to another image

            if font!=None: self.font=font
            if anchor!=None: self.anchor=anchor
                
            self.x0=self.x() if x0 is None else x0
            self.y0=self.y() if y0 is None else y0
            self.offsetx0=self.offsetx() if offsetx0 is None else offsetx0
            self.offsety0=self.offsety() if offsety0 is None else offsety0

            self.fillcolor0=self.fillcolor() if fillcolor0 is None else colorspec_to_tuple(fillcolor0)
            self.linecolor0=self.linecolor() if linecolor0 is None else colorspec_to_tuple(linecolor0)
            self.linewidth0=self.linewidth() if linewidth0 is None else linewidth0
            self.angle0=self.angle() if angle0 is None else angle0
            self.fontsize0=self.fontsize() if fontsize0 is None else fontsize0
            self.t0=animation.env._now if t0 is None else t0
    
            self.circle1=self.circle0 if circle1 is None else circle1
            self.line1=self.line0 if line1 is None else line1
            self.polygon1=self.polygon0 if polygon1 is None else polygon1
            self.rectangle1=self.rectangle0 if rectangle1 is None else rectangle1

            self.x1=self.x0 if x1 is None else x1
            self.y1=self.y0 if y1 is None else y1
            self.offsetx1=self.offsetx0 if offsetx1 is None else offsetx1
            self.offsety1=self.offsety0 if offsety1 is None else offsety1
            self.fillcolor1=self.fillcolor0 if fillcolor1 is None else colorspec_to_tuple(fillcolor1)
            self.linecolor1=self.linecolor0 if linecolor1 is None else colorspec_to_tuple(linecolor1)
            self.linewidth1=self.linewidth0 if linewidth1 is None else linewidth1
            self.angle1=self.angle0 if angle1 is None else angle1
            self.fontsize1=self.fontsize0 if fontsize1 is None else fontsize1
            self.width1=self.width0 if width1 is None else width1

            self.t1=inf if t1 is None else t1
            if self not in animation.animation_objects:
                animation.animation_objects.append(self)
    
        def remove(self):
            '''
            removes the animation object
            
            the animation object is removed from the animation queue, so effectively ending this animation
            note that it might be still updated if required
            '''
            if self in animation.animation_objects:
                animation.animation_objects.remove(self)
                
        def x(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.x0,self.x1)

        def y(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.y0,self.y1)

        def offsetx(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.offsetx0,self.offsetx1)

        def offsety(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.offsety0,self.offsety1)

        def angle(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.angle0,self.angle1)

        def linewidth(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.linewidth0,self.linewidth1)

        def linecolor(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.linecolor0,self.linecolor1)

        def fillcolor(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.fillcolor0,self.fillcolor1)

        def circle(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.circle0,self.circle1)

        def line(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.line0,self.line1)

        def polygon(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.polygon0,self.polygon1)

        def rectangle(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.rectangle0,self.rectangle1)

        def width(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.width0,self.width1)

        def fontsize(self,t=None):
            return interpolate((animation.env._now if t is None else t),self.t0,self.t1,self.fontsize0,self.fontsize1)



    class AnimateButton(object):
        '''
        defines a button
        
        arguments:
            layer         lower layer values are on top of higher layer values (default 0)
            x             x-coordinate of centre of button in screen coordinates
            y             y-coordinate of centre of button in screen coordinates
            width         width of button in screen coordinates (default 80)
            height        height of button in screen coordinates (default 30)
            linewidth     width of contour in screen coordinates (default 0=no contour)
            fillcolor     color of the interior (default 40%gray)  
            linecolor     color of contour (default black)
            color         color of the text (default white)
            text          text of the button (default null string)
                          if text is an argumentless function, this will be called each time the
                          button is shown/updated
            font          font of the text (default Helvetica)
            fontsize      fontsize of the text (default 15)
            action        function executed when the button is pressed (default None)
                          the function should have no arguments
        '''
        def __init__(self,layer=0,x=0,y=0,width=80,height=30,
                     linewidth=0,fillcolor='40%gray',
                     linecolor='black',color='white',text='',font='',fontsize=15,action=None):
            
            self.type='button'
            self.parent=None
            self.layer=layer
            self.t0=-inf
            self.t1=inf
            self.x0=0
            self.y0=0
            self.x1=0
            self.y1=0
            self.survive_reset=True
            animation.sequence+=1
            self.sequence=animation.sequence
            self.x=x-width/2
            self.y=y-height/2
            self.width=width
            self.height=height
            self.fillcolor=colorspec_to_tuple(fillcolor)
            self.linecolor=colorspec_to_tuple(linecolor)
            self.color=colorspec_to_tuple(color)
            self.linewidth=linewidth
            self.font=font
            self.fontsize=fontsize
            self.text=text
            self.lasttext='*'
            self.action=action
            
            if not Pythonista:
                self.button = tkinter.Button(animation.root, text = self.lasttext, command = action, anchor = tkinter.CENTER)
                self.button.configure(width = int(2.2*width/fontsize), foreground=colorspec_to_hex(self.color,False),background =colorspec_to_hex(self.fillcolor,False), relief = tkinter.FLAT)
                self.button_window = animation.canvas.create_window(self.x+self.width, animation.height-self.y-self.height,anchor=tkinter.NE,
                    window=self.button)            
                
            animation.animation_objects.append(self)
    
    class AnimateSlider(object):
        '''
        defines a slider
        
        arguments:
            layer         lower layer values are on top of higher layer values (default 0)
            x             x-coordinate of centre of slider in screen coordinates
            y             y-coordinate of centre of slider in screen coordinates
            vmin          minimum value (default 0)
            vmax          maximum value (default 10)
            v             initial value (default vmin)
            resolution    step size of value (default 1)
            width         width of slider in screen coordinates (default 100)
            height        height of slider in screen coordinates (default 20)
            linewidth     width of contour in screen coordinates (default 0=no contour)
            fillcolor     color of the interior (default 40%gray)  
            linecolor     color of contour (default black)
            labelcolor    color of the label (default black)
            label         label if the slider (default null string)
                          if label is an argumentless function, this function will be used to display
                          label, otherwise the label plus the current value of the slider will be shown 
            font          font of the text (default Helvetica)
            fontsize      fontsize of the text (default 12)
            action        function executed when the slider value is changed (default None)
                          the function should have no arguments
                          if None, no action
          
            The current value of the slider is in the v attibute of the slider
        '''
        def __init__(self,layer=0,x=0,y=0,width=100,height=20,
                     vmin=0,vmax=10,v=None,resolution=1,
                     linecolor='black',labelcolor='black',label='',
                     font='',fontsize=12,action=None):
            
            n=round((vmax-vmin)/resolution)+1
            self.vmin=vmin
            self.vmax=vmin+(n-1)*resolution
            self._v=vmin if v is None else v
            self.xdelta=width/n
            self.resolution=resolution
            
            self.type='slider'
            self.layer=layer
            self.parent=None
            self.t0=-inf
            self.t1=inf
            self.x0=0
            self.y0=0
            self.x1=0
            self.y1=0
            self.survive_reset=True
            animation.sequence+=1
            self.sequence=animation.sequence
            self.x=x-width/2
            self.y=y-height/2
            self.width=width
            self.height=height
            self.linecolor=colorspec_to_tuple(linecolor)
            self.labelcolor=colorspec_to_tuple(labelcolor)
            self.font=font
            self.fontsize=fontsize
            self.label=label
            self.action=action
    
            if Pythonista:
                self.y=self.y-height*1.5
            else:
                self.slider=tkinter.Scale(animation.root, from_=self.vmin, to=self.vmax,orient=tkinter.HORIZONTAL,label=label,resolution=resolution)
                self.slider.window = animation.canvas.create_window(self.x, animation.height-self.y, anchor=tkinter.NW, window=self.slider)
                self.slider.config(font=(font,int(fontsize*0.8)),background=colorspec_to_hex(animation.background_color,False),
                                   highlightbackground=colorspec_to_hex(animation.background_color,False))
                self.slider.set(self._v)
    
            animation.animation_objects.append(self)
        
        
        @property
        def v(self,value=None):
            '''
            returns and/or sets the value
            '''
            if Pythonista:
                return self._v
            else:
                return self.slider.get()
        
        @v.setter
        def v(self,value):
            '''
            returns and/or sets the value
            '''
            if Pythonista:
                self._v=value
            else:
                self.slider.set(value)

    
    def _member(self,q):
        try:
            return self._qmembers[q]
        except:
            return None
        
    def _checknotinqueue(self,q):
        mx=self._member(q)
        if mx is None:
            pass
        else:
            raise AssertionError(self._name+' is already member of '+q._name)
        
    def _checkinqueue(self,q):
        mx=self._member(q)
        if mx is None:
            raise AssertionError(self._name+' is not member of '+q._name)
        else:
            return mx
            
    def _checkcurrent(self):
        if self.env._current_component==self:
            pass
        else:
            raise AssertionError(self._name+' is not current')
            
    def _checknotcurrent(self):
        if not self.env._current_component==self:
            pass
        else:
            raise AssertionError(self._name+' is current')
                        
    def _checkispassive(self):
        if self._status==passive:
            pass
        else:
            raise AssertionError(self._name+' is not passive')
        
    
class Animation(object):
    '''
    Initializes the animation
    
    arguments:
        width            width of the animation in screen coordinates (default 1024)
        height           height of the animation in screen coordinates (default 768)
        x0               user x-coordinate of the lower left corner (default 0)
        y0               user y_coordinate of the lower left corner (default 0)
        x1               user x-coordinate of the upper right corner (default x0+1024)
        env              environment to animate (default default_env)
        background_color color of the background (default 90%gray)
        fps              number of frames per second
        modelname        name of model to be shown in upper left corner, along this text 'a salabim model'
        use_toplevel     if salabim animation is used in parallel with other modules using tkinter,
                         it might be necessary to initialize the root with tkinter.TopLevel(). In that
                         case, set this parameter to True.
                         if False (default), the root will be initialized with tkinter.Tk()
        
    Animation may be called only once.
    
    For Pythonista, the default width and height are according to the device orientation
    '''

    def __init__(self,width=None,height=None,x0=0,y0=0,x1=None,y1=None,env=None,
        background_color='90%gray',fps=30,modelname=''):
        global animation
        assert animation is None
        if Pythonista:
            dwidth,dheight=ui.get_screen_size()
        else:
            dwidth,dheight=(1024,768)
        animation=self
        self.env=default_env if env is None else env
        self.background_color=colorspec_to_tuple(background_color)
        animation.fps=fps
        if width is None:
            if height is None:
                self.width=dwidth
                self.height=dheight
            else:
                self.height=height
                self.width=height*dwidth/dheight
        else:
            if height is None:
                self.width=width
                self.height=width*dheight/dwidth
            else:
                self.width=width
                self.height=height
        self.x0=x0
        self.y0=y0
        if x1 is None:
            self.x1=self.x0+self.width
        else:
            self.x1=x1
        self.y1=self.y0+(self.x1-self.x0)*self.height/self.width                

        self.scale=self.width/(self.x1-self.x0)
        
        self.animation_objects=[]
        self.animation_speed=1
        self.running=False
        self.sequence=0
        self.font_cache={}
        
        if Pythonista:
            scene.run(MyScene(), frame_interval=60/animation.fps, show_fps=False)
        else:         
            self.canvas_objects=[]
            
            self.root = tkinter.Toplevel()
            self.canvas = tkinter.Canvas(self.root, width=self.width,height = self.height)
            self.canvas.configure(background=colorspec_to_hex(self.background_color,False))
            self.canvas.pack()
            
        if modelname!='':
            h1=main.Animate(text=modelname,
                x0=8,y0=animation.height-60,
                anchor='w',fontsize0=30,fillcolor0='black',screen_coordinates=True )
            h1.survive_reset=True
            h2=main.Animate(text='a salabim model',
                x0=8,y0=animation.height-78,
                anchor='w',fontsize0=16,fillcolor0='red',screen_coordinates=True )            
            h2.survive_reset=True

        self.env._main.AnimateButton(x=48,y=animation.height-21,text='Quit',action=self.animquit)
        self.env._main.AnimateButton(x=48+1*90,y=animation.height-21,text='Anim/2',action=self.animhalf) 
        self.env._main.AnimateButton(x=48+2*90,y=animation.height-21,text='Anim*2',action=self.animdouble)
        self.env._main.AnimateButton(x=48+3*90,y=animation.height-21,text=pausetext,action=self.animpause)
        self.env._main.AnimateButton(x=48+4*90,y=animation.height-21,text=tracetext,action=self.animtrace)                                                                                  
            
        t1=self.env._main.Animate(x0=animation.width,y0=self.height-5,fillcolor0='black',text=clocktext,
            fontsize0=15,anchor='ne',screen_coordinates=True)

        t1.survive_reset=True

    def exit(self):
        self.root.destroy()

    def quit(self):
        self.running=False

    def animhalf(self):
        if animation.paused:
            animation.paused=False
        else:
            animation.animation_speed=animation.animation_speed/2    
            animation.start_animation_time=animation.t
            animation.start_animation_clocktime=time.time()      

    def animdouble(self):
        if animation.paused:
            animation.paused=False
        else:
            animation.animation_speed=animation.animation_speed*2  
            animation.start_animation_time=animation.t
            animation.start_animation_clocktime=time.time()
    
    def animpause(self):
        animation.paused=not animation.paused
        animation.start_animation_time=animation.t
        animation.start_animation_clocktime=time.time()
         
    def animquit(self):
        if Pythonista:
            animation.scene.view.close()
        else:
            animation.root.destroy()
        
    def animtrace(self):
        animation.env._trace=not animation.env._trace
        
class _Distribution():
        
    @property
    def mean(self):
        '''
        returns the mean of a distribution
        
        '''
        return self._mean
        
class Exponential(_Distribution):
    '''
    exponential distribution
    
    Exponential(mean,seed)
    
    arguments:
        mean                mean of the distribtion
                            must be >0
        randomstream        randomstream
                            if omitted, random will be used
                            if used as random.Random(12299) it assign a new stream with the specified seed
    '''
    def __init__(self,mean,randomstream=None):
        if mean<=0:
            raise AsserionError('mean<=0')
        self._mean=mean
        if randomstream is None:
            self.randomstream=random
        else:
            assert type(ramdomstream)==random.Random
            self.randomstream=randomstream
            
    def __repr__(self):
        lines=[]
        lines.append('Exponential distribution '+hex(id(self)))
        lines.append('  mean='+str(self.mean))
        lines.append('  randomstream='+hex(id(self.randomstream)))
        return '\n'.join(lines)
        
    @property
    def sample(self):
        return self.randomstream.expovariate(1/(self._mean))


class Normal(_Distribution):
    '''
    normal distribution
    
    Normal(mean,standard_deviation,randomstream)
    
    arguments:
        mean                mean of the distribution
        standard_deviation  standard deviation of the distribution
                            must be >=0
        randomstream        randomstream
                            if omitted, random will be used
                            if used as random.Random(12299) it assign a new stream with the specified seed
    '''
    def __init__(self,mean,standard_deviation,randomstream=None):
        if standard_deviation<0:
            raise AsserionError('standard_deviation<0')
        self._mean=mean
        self._standard_deviation=standard_deviation
        if randomstream is None:
            self.randomstream=random
        else:
            assert type(ramdomstream)==random.Random
            self.randomstream=randomstream

    def __repr__(self):
        lines=[]
        lines.append('Normal distribution '+hex(id(self)))
        lines.append('  mean='+str(self.mean))
        lines.append('  standard_deviation='+str(self.standard_deviation))
        lines.append('  randomstream='+hex(id(self.randomstream)))
        return '\n'.join(lines)

    @property
    def sample(self):
        return self.randomstream.normalvariate(self._mean,self._standard_deviation)

class Uniform(_Distribution):
    '''
    uniform distribution
    
    Uniform(lowerbound,upperboud,seed)
    
    arguments:
        lowerbound          lowerbound of the distribution
        upperbound          upperbound of the distribution
        randomstream        randomstream
                            if omitted, random will be used
                            if used as random.Random(12299) it assign a new stream with the specified seed

    upperbound must be >= lowerbound
    '''
    def __init__(self,lowerbound,upperbound,randomstream=None):
        if lowerbound>upperbound:
            raise AssertionError('lowerbound>upperbound')
        self._lowerbound=lowerbound
        self._upperbound=upperbound
        if randomstream is None:
            self.randomstream=random
        else:
            assert type(ramdomstream)==random.Random
            self.randomstream=randomstream
        self._mean=(lowerbound+upperbound)/2
        
    def __repr__(self):
        lines=[]
        lines.append('Uniform distribution '+hex(id(self)))
        lines.append('  lowerbound='+str(self._lowerbound))
        lines.append('  upperbound='+str(self._upperbound))
        lines.append('  randomstream='+hex(id(self.randomstream)))
        return '\n'.join(lines)
        

    @property
    def sample(self):
        return self.randomstream.uniform(self._lowerbound,self._upperbound)
        
class Triangular(_Distribution):
    '''
    triangular distribution
    
    Triangular(low,high,mode,seed)
    
    arguments:
        low                 lowerbound of the distribution
        upp                 upperbound of the distribution
        mode                mode of the distribution
        randomstream        randomstream
                            if omitted, random will be used
                            if used as random.Random(12299) it assign a new stream with the specified seed
    requirement: low <= mode <= upp
    '''
    def __init__(self,low,high,mode,randomstream=None):
        if low>high:
            raise AssertionError('low>high')
        if low>mode:
            raise AssertionError('low>mode')
        if high<mode:
            raise AssertionError('high<mode')
        self._low=low
        self._high=high
        self._mode=mode
        if randomstream is None:
            self.randomstream=random
        else:
            assert type(ramdomstream)==random.Random
            self.randomstream=randomstream
        self._mean=(low+mode+high)/3

    def __repr__(self):
        lines=[]
        lines.append('Triangular distribution '+hex(id(self)))
        lines.append('  low='+str(self._low))
        lines.append('  high='+str(self._high))
        lines.append('  mode='+str(self._mode))
        lines.append('  randomstream='+hex(id(self.randomstream)))
        return '\n'.join(lines)

    @property
    def sample(self):
        return self.randomstream.triangular(self._low,self._high,self._mode)
    
class Constant(_Distribution):
    '''
    constant distribution
    
    Constant(value,randomstream)
    
    arguments:
        value               value to be returned in sample
        randomstream        randomstream
                            if omitted, random will be used
                            if used as random.Random(12299) it assign a new stream with the specified seed
    '''
    def __init__(self,value,randomstream=None):
        self._value=value
        if randomstream is None:
            self.randomstream=random
        else:
            assert type(randomstream)==random.Random
            self.randomstream=randomstream
        self._mean=value
        
    def __repr__(self):
        lines=[]
        lines.append('Constant distribution '+hex(id(self)))
        lines.append('  value='+str(self._value))
        lines.append('  randomstream='+hex(id(self.randomstream)))
        return '\n'.join(lines)
        

    @property
    def sample(self):
        return(self._value)
        
class Cdf(_Distribution):
    '''
    Cumulative distribution function
    
    Cdf(spec,seed)
    
    arguments:
        spec                list with x-values and corresponduing cumulative density
                            (x1,c1,x2,c2, ...xn,cn)
        randomstream        randomstream
                            if omitted, random will be used
                            if used as random.Random(12299) it assign a new stream with the specified seed
    requirements:
        x1<=X2<= ...<=xn
        c1<=c2<=cn
        c1=0
        cn>0
        all cumulative densities are auto scaled according to cm,
        so no need to set cn to 1 or 100.
    '''
    def __init__(self,spec,randomstream=None):
        self._x=[]
        self._cum=[]
        if randomstream is None:
            self.randomstream=random
        else:
            assert type(randomstream)==random.Random
            self.randomstream=randomstream
            
        lastcum=0
        lastx=-inf
        spec=list(spec)
        if len(spec)==0:
            raise AssertionError('no arguments specified')
        if spec[1]!=0:
            raise AssertionError('first cumulative value should be 0')
        while len(spec)>0:
            x=spec.pop(0)
            if len(spec)==0:
                raise AssertionError('uneven number of parameters specified')
            if x<lastx:
                raise AssertionError('x value %s is smaller than previous value %s'%(x,lastx))
            cum=spec.pop(0)
            if cum<lastcum:
                raise AssertionError('cumulative value %s is smaller than previous value %s'%(cum,lastcum))
            self._x.append(x)
            self._cum.append(cum)
            lastx=x
            lastcum=cum
        if lastcum==0:
            raise AssertionError('last cumulative value should be >0')
        for i in range (len(self._cum)):
            self._cum[i]=self._cum[i]/lastcum
        self._mean=0
        for i in range(len(self._cum)-1):
            self._mean+=((self._x[i]+self._x[i+1])/2)*(self._cum[i+1]-self._cum[i])

    def __repr__(self):
        lines=[]
        lines.append('Cdf distribution '+hex(id(self)))
        lines.append('  randomstream='+hex(id(self.randomstream)))
        return '\n'.join(lines)

            
    @property
    def sample(self):
        r=self.randomstream.random()
        for i in range (len(self._cum)):
            if r<self._cum[i]:
                return interpolate(r,self._cum[i-1],self._cum[i],self._x[i-1],self._x[i])
        return self._x[i]        
                
class Pdf(_Distribution):
    '''
    Probility distribution function
    
    Pdf(list,seed)
    
    arguments:
        spec                list with x-values and corresponding probability
                            (x1,p1,x2,p2, ...xn,pn)
        randomstream        randomstream
                            if omitted, random will be used
                            if used as random.Random(12299) it assign a new stream with the specified seed
    requirements:
        p1+p2=...+pn>0
        all densities are auto scaled according to the sum of p1 to pn,
        so no need to have p1 to pn add up to 1 or 100.
    '''
    def __init__(self,spec,randomstream=None):
        self._x=[0] # just a place holder
        self._cum=[0] 
        if randomstream is None:
            self.randomstream=random
        else:
            assert type(ramdomstream)==random.Random                
            self.randomstream=randomstream

        sump=0
        sumxp=0
        lastx=-inf
        spec=list(spec)
        if len(spec)==0:
            raise AssertionError('no arguments specified')
        while len(spec)>0:
            x=spec.pop(0)
            if len(spec)==0:
                raise AssertionError('uneven number of parameters specified')
            p=spec.pop(0)
            sump+=p
            if type(x) in (list,tuple):
                if len(x)==2:
                    xm=(x[0]+x[1])/2
                    x=(min(x[0],x[1]),max(x[0],x[1])) 
                else:
                    raise AssertionError('error in tuple ',x)
            else:
                xm=x
            sumxp+=(p*xm)
            self._x.append(x)
            self._cum.append(sump)
        if sump==0:
            raise AssertionError('at least one probability should be >0')
        for i in range (len(self._cum)):
            self._cum[i]=self._cum[i]/sump
        self._mean=sumxp/sump

    def __repr__(self):
        lines=[]
        lines.append('Pdf distribution '+hex(id(self)))
        lines.append('  randomstream='+hex(id(self.randomstream)))
        return '\n'.join(lines)

    @property
    def sample(self):
        r=self.randomstream.random()
        for i in range (len(self._cum)):
            if r<=self._cum[i]:
                x=self._x[i]
                if type(x) in (list,tuple):
                    x=interpolate(r,self._cum[i-1],self._cum[i],self._x[i][0],self._x[i][1])
                    if x<self._x[i][0]:
                        x=self._x[i][0]
                    if x>self._x[i][1]:
                        x=self._x[i][1]
                    return x
                else:
                    return self._x[i]
        return self._x[i]  # just for safety  

class Distribution(_Distribution):
    '''
    Generate a distribution from a string
    
    Distribution(spec,randomstream)
    
    arguments:
        spec                string containing a valid salabim distribution
        randomstream        randomstream
                            if omitted, random will be used
                            if used as random.Random(12299) it assign a new stream with the specified seed
                            note that the rendomstream in the string is ignored
    requirements:
        spec must evakuate to a proper salabim distribution (including proper casing).
    '''

    def __init__(self,spec,randomstream=None):
        d=eval(spec)
        if randomstream is None:
            self.randomstream=random
        else:
            assert type(ramdomstream)==random.Random
            self.randomstream=randomstream
        self._distribution=d
        self._mean=d._mean

    def __repr__(self):
        return self._distribution.__repr__()
        
    @property
    def sample(self):
        self._distribution.randomstream=self.randomstream
        return self._distribution.sample        

class Resource(object):
    def __init__(self,name=None,capacity=1,strict_order=False,anonymous=False,env=None):
        '''
        
        '''
        
        if (env is None):
            self.env=default_env
        else:
            self.env=env
        if name is None:
            name='resource.'            
        self._capacity=capacity
        self._name,self._base_name,self._sequence_number = self.env._reformatnameR(name)
        self._requesters=Queue(name='requesters:'+name,env=self.env)
        self._requesters._resource=self
        self._claimers=Queue(name='claimers:'+name,env=self.env)
        self._pendingclaimed_quantity=0
        self._claimed_quantity=0
        self._anonymous=anonymous
        self._strict_order=strict_order

    def __repr__(self):
        lines=[]
        lines.append('Resource '+hex(id(self)))
        lines.append('  name='+self._name)
        lines.append('  capacity='+str(self._capacity))
        if self._requesters.length==0:
            lines.append('  no requests')
        else:
            lines.append('  requesting component(s):')
            for c in self._requesters.components():
                if self in c._pendingclaims:
                    lines.append('    '+pad(c._name,20)+' quantity='+str(c._requests[self])+' provisionally claimed')
                else:
                    lines.append('    '+pad(c._name,20)+' quantity='+str(c._requests[self]))
        
        lines.append('  claimed_quantity='+str(self._claimed_quantity))
        if self._claimed_quantity>=0:
            if self._anonymous:
                lines.append('  not claimed by any components, because the resource is anonymous')
            else:
                lines.append('  claimed by:')
                for c in self._claimers.components():
                    lines.append('    '+pad(c._name,20)+' quantity='+str(c._claims[self]))
                 
        return '\n'.join(lines)

    def _claimtry(self):
        mx=self._requesters._head.successor
        while mx!=self._requesters._tail:
            c=mx.component
            mx=mx.successor
            if c._greedy:
                if self not in c._pendingclaims:
                    if c._requests[self]<=self._capacity-self._claimed_quantity-self._pendingclaimed_quantity+1e-8:
                        c._pendingclaims.append(self)
                        self._pendingclaimed_quantity+=c._requests[self] 
            claimed=True
            for r in c._requests:
                if r not in c._pendingclaims:
                    if c._requests[r]>r._capacity-r._claimed_quantity-r._pendingclaimed_quantity+1e-8:
                        claimed=False
                        break
            if claimed:
                for r in list(c._requests):

                    r._claimed_quantity+=c._requests[r]
                    if r in c._pendingclaims:
                        r._pendingclaimed_quantity-=c._requests[r]
                        
                    if not r._anonymous:
                        if r in c._claims:
                            c._claims[r]+=c._requests[r]
                        else:
                            c._claims[r]=c._requests[r]
                        c._enter(r._claimers)
                    c._leave(r._requesters)
                c._requests={}   
                c._pendingclaims=[]
                c._reschedule(self.env._now,False,'request honoured')                  
            else:
                if self._strict_order:
                    return
                    
    def release(self,quantity=None):
        '''
        releases all claims or a specified quantity
        
        arguments:
            quantity          quantity to be released
                              if not specified, the resource will be emptied 
                              completely
                              
        quantity may not be specified for a non-anomymous resoure
        '''
        if self._anonymous:
            if quantity is None:
                q=self._claimed_quantity
            else:
                q=quantity
            self._claimed_quantity-=q
            if self._claimed_quantity<1e-8:
                self._claimed_quantity=0
            self._claimtry
            
        else:
            if quantity!=None:
                raise AssertionError('no quantity allowed for non-anonymous resource')
                
            for c in list(self._claimers.components()):
                c.release(self)
                
    @property
    def requesters(self):
        '''
        returns the queue containing all components not yet honoured requests.
        '''
        return self._requesters
        
    @property
    def claimers(self):
        '''
        returns the name of all components claiming from the resource.
        will be an empty queue for anonymous resource
        '''
        return self._claimers

    @property
    def capacity(self,cap=None):
        '''
        gets or sets the capacity of a resource
        '''
        return self._capacity

    @capacity.setter
    def capacity(self,cap):
        self._capacity=cap
        self._claimtry()
        
    @property
    def claimed_quantity(self):
        '''
        returns the claimed quantity
        '''
        return self._claimed_quantity
            
    @property
    def strict_order(self):
        '''
        gets of sets the strict_order property of a resource
        '''
        return self._strict_order
        
    @strict_order.setter
    def strict_order(self,strict_order):
        self._strict_order=strict_order
        self._claimtry()

    @property
    def name(self):
        '''
        gets and/or sets the name of a resource
        
        arguments:
            txt                 name of the resource
                                if txt ends with a period, the name will be serialized
                                if omitted, the name will not be changed
        '''
        return self._name

    @name.setter
    def name(self,txt):
        self._name,self._base_name,self._sequence_number=self.env._reformatnameR(txt)
        
    @property
    def base_name(self):
        '''
        returns the base name of a resource (the name used at init or name)
        '''
        return self._base_name        

    @property
    def sequence_number(self):
        '''
        returns the sequence_number of a resource (the sequence number at init or name)

        normally this will be the integer value of a serialized name,
        but also non serialized names (without a dot at the end will be numbered)
        '''
        return self._sequence_number  

def colornames():
    return {  
        'aliceblue':            '#F0F8FF',
        'antiquewhite':         '#FAEBD7',
        'aqua':                 '#00FFFF',
        'aquamarine':           '#7FFFD4',
        'azure':                '#F0FFFF',
        'beige':                '#F5F5DC',
        'bisque':               '#FFE4C4',
        'black':                '#000000',
        'blanchedalmond':       '#FFEBCD',
        'blue':                 '#0000FF',
        'blueviolet':           '#8A2BE2',
        'brown':                '#A52A2A',
        'burlywood':            '#DEB887',
        'cadetblue':            '#5F9EA0',
        'chartreuse':           '#7FFF00',
        'chocolate':            '#D2691E',
        'coral':                '#FF7F50',
        'cornflowerblue':       '#6495ED',
        'cornsilk':             '#FFF8DC',
        'crimson':              '#DC143C',
        'cyan':                 '#00FFFF',
        'darkblue':             '#00008B',
        'darkcyan':             '#008B8B',
        'darkgoldenrod':        '#B8860B',
        'darkgray':             '#A9A9A9',
        'darkgreen':            '#006400',
        'darkkhaki':            '#BDB76B',
        'darkmagenta':          '#8B008B',
        'darkolivegreen':       '#556B2F',
        'darkorange':           '#FF8C00',
        'darkorchid':           '#9932CC',
        'darkred':              '#8B0000',
        'darksalmon':           '#E9967A',
        'darkseagreen':         '#8FBC8F',
        'darkslateblue':        '#483D8B',
        'darkslategray':        '#2F4F4F',
        'darkturquoise':        '#00CED1',
        'darkviolet':           '#9400D3',
        'deeppink':             '#FF1493',
        'deepskyblue':          '#00BFFF',
        'dimgray':              '#696969',
        'dodgerblue':           '#1E90FF',
        'firebrick':            '#B22222',
        'floralwhite':          '#FFFAF0',
        'forestgreen':          '#228B22',
        'fuchsia':              '#FF00FF',
        'gainsboro':            '#DCDCDC',
        'ghostwhite':           '#F8F8FF',
        'gold':                 '#FFD700',
        'goldenrod':            '#DAA520',
        'gray':                 '#808080',
        'green':                '#008000',
        'greenyellow':          '#ADFF2F',
        'honeydew':             '#F0FFF0',
        'hotpink':              '#FF69B4',
        'indianred':            '#CD5C5C',
        'indigo':               '#4B0082',
        'ivory':                '#FFFFF0',
        'khaki':                '#F0E68C',
        'lavender':             '#E6E6FA',
        'lavenderblush':        '#FFF0F5',
        'lawngreen':            '#7CFC00',
        'lemonchiffon':         '#FFFACD',
        'lightblue':            '#ADD8E6',
        'lightcoral':           '#F08080',
        'lightcyan':            '#E0FFFF',
        'lightgoldenrodyellow': '#FAFAD2',
        'lightgreen':           '#90EE90',
        'lightgray':            '#D3D3D3',
        'lightpink':            '#FFB6C1',
        'lightsalmon':          '#FFA07A',
        'lightseagreen':        '#20B2AA',
        'lightskyblue':         '#87CEFA',
        'lightslategray':       '#778899',
        'lightsteelblue':       '#B0C4DE',
        'lightyellow':          '#FFFFE0',
        'lime':                 '#00FF00',
        'limegreen':            '#32CD32',
        'linen':                '#FAF0E6',
        'magenta':              '#FF00FF',
        'maroon':               '#800000',
        'mediumaquamarine':     '#66CDAA',
        'mediumblue':           '#0000CD',
        'mediumorchid':         '#BA55D3',
        'mediumpurple':         '#9370DB',
        'mediumseagreen':       '#3CB371',
        'mediumslateblue':      '#7B68EE',
        'mediumspringgreen':    '#00FA9A',
        'mediumturquoise':      '#48D1CC',
        'mediumvioletred':      '#C71585',
        'midnightblue':         '#191970',
        'mintcream':            '#F5FFFA',
        'mistyrose':            '#FFE4E1',
        'moccasin':             '#FFE4B5',
        'navajowhite':          '#FFDEAD',
        'navy':                 '#000080',
        'oldlace':              '#FDF5E6',
        'olive':                '#808000',
        'olivedrab':            '#6B8E23',
        'orange':               '#FFA500',
        'orangered':            '#FF4500',
        'orchid':               '#DA70D6',
        'palegoldenrod':        '#EEE8AA',
        'palegreen':            '#98FB98',
        'paleturquoise':        '#AFEEEE',
        'palevioletred':        '#DB7093',
        'papayawhip':           '#FFEFD5',
        'peachpuff':            '#FFDAB9',
        'peru':                 '#CD853F',
        'pink':                 '#FFC0CB',
        'plum':                 '#DDA0DD',
        'powderblue':           '#B0E0E6',
        'purple':               '#800080',
        'red':                  '#FF0000',
        'rosybrown':            '#BC8F8F',
        'royalblue':            '#4169E1',
        'saddlebrown':          '#8B4513',
        'salmon':               '#FA8072',
        'sandybrown':           '#FAA460',
        'seagreen':             '#2E8B57',
        'seashell':             '#FFF5EE',
        'sienna':               '#A0522D',
        'silver':               '#C0C0C0',
        'skyblue':              '#87CEEB',
        'slateblue':            '#6A5ACD',
        'slategray':            '#708090',
        'snow':                 '#FFFAFA',
        'springgreen':          '#00FF7F',
        'steelblue':            '#4682B4',
        'tan':                  '#D2B48C',
        'teal':                 '#008080',
        'thistle':              '#D8BFD8',
        'tomato':               '#FF6347',
        'turquoise':            '#40E0D0',
        'violet':               '#EE82EE',
        'wheat':                '#F5DEB3',
        'white':                '#FFFFFF',
        'whitesmoke':           '#F5F5F5',
        'yellow':               '#FFFF00',
        'yellowgreen':          '#9ACD32',
        '10%gray':              '#191919',
        '20%gray':              '#333333',
        '30%gray':              '#464646',
        '40%gray':              '#666666',
        '50%gray':              '#7F7F7F',
        '60%gray':              '#999999',
        '70%gray':              '#B2B2B2',
        '80%gray':              '#CCCCCC',
        '90%gray':              '#E6E6E6',
        'transparent':          '#00000000',
        'none':                 '#00000000',
        '':                     '#00000000'
        }

def colorspec_to_tuple(colorspec):
    if type(colorspec) in (tuple,list):
        if len(colorspec)==2:
            c=colorspec_to_tuple(colorspec[0])
            return (c[0],c[1],c[2],colorspec[1])
        elif len(colorspec)==3:
            return (colorspec[0],colorspec[1],colorspec[2],255)
        elif len(colorspec)==4:
            return colorspec
    else:
        if (colorspec!='') and (colorspec[0])=='#':
            if len(colorspec)==7:
                return (int(colorspec[1:3],16),int(colorspec[3:5],16),int(colorspec[5:7],16))
            elif len(colorspec)==9:
                return (int(colorspec[1:3],16),int(colorspec[3:5],16),int(colorspec[5:7],16),int(colorspec[7:9],16))
        else:
            s=colorspec.split('#')
            if len(s)==2:
                alpha=s[1]
                colorspec=s[0]
            else:
                alpha='FF'
            colorhex=colornames()[colorspec.replace(' ','').lower()]
            if len(colorhex)==7:
                colorhex=colorhex+alpha
            return colorspec_to_tuple(colorhex)
    raise AssertionError('wrong spec for color')

def hex_to_rgb(v):
    if v=='':
        return(0,0,0,0)
    if v[0] == '#':
        v = v[1:]
    if len(v)==6:
        return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16)
    if len(v)==8:
        return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16), int(v[6:8], 16)
    raise AssertionError('Incorrect value'+str(v))

def colorspec_to_hex(colorspec,withalpha=True):
    v=colorspec_to_tuple(colorspec)
    if withalpha:
        return '#%02x%02x%02x%02x' % (int(v[0]),int(v[1]),int(v[2]),int(v[3]))
    else:
        return '#%02x%02x%02x' % (int(v[0]),int(v[1]),int(v[2]))

def getfont(fontname,fontsize): # fontsize in screen_coordinates!
    if type(fontname)==list:
        fonts=tuple(fontname)
    elif type(fontname)==str:
        fonts=(fontname,)
    else:
        fonts=fontname

    if (fonts,fontsize) in animation.font_cache:
        font=animation.font_cache[(fonts,fontsize)]
    else:
        for ifont in fonts+('calibri', 'Calibri'):
            try:
                font=ImageFont.truetype(font=ifont,size=int(fontsize))
                break
            except:
                pass
        animation.font_cache[(fonts,fontsize)]=font
    return font
        
def getwidth(text,font='',fontsize=20,screen_coordinates=False):
    if not screen_coordinates:
        fontsize=fontsize*animation.scale
    f=getfont(font,fontsize)
    thiswidth,thisheight=f.getsize(text)
    if screen_coordinates:
        return thiswidth
    else:
        return thiswidth/animation.scale
    return 

def getfontsize_to_fit(text,width,font='',screen_coordinates=False):
    if not screen_coordinates:
        width=width*animation.scale

    lastwidth=0    
    for fontsize in range(1,300):
        f=getfont(font,fontsize)
        thiswidth,thisheight=f.getsize(text)
        if thiswidth>width:
            break
        lastwidth=thiswidth
    print('--width,lastwidth',width,lastwidth)
    fontsize=interpolate(width,lastwidth,thiswidth,fontsize-1,fontsize)
    if screen_coordinates:
         return fontsize
    else:
         return fontsize/animation.scale

def _i(p,v0,v1):
    if v0==v1:
        return v0 # avoid rounding problems
    return (1-p)*v0+p*v1

def interpolate(t,t0,t1,v0,v1):
    if (v0 is None) or (v1 is None):
        return None
    if t<=t0:
        return v0
    if t>=t1:
        return v1
    if t1==inf:
        return v0
    p=(0.0+t-t0)/(t1-t0)
    if type(v0) in (list,tuple):
        l=[]
        for x0,x1 in zip(v0,v1):
            l.append(_i(p,x0,x1))
        return tuple(l)
    else:
        return _i(p,v0,v1)

def str_or_function(t):
    if callable(t):
        return t()
    else:
        return str(t)
        
def clocktext():
    if (animation.paused) and (int(time.time()*2)%2==0):
        return ' '
    else:
        return '%6.3f %10.3f'% (animation.animation_speed,animation.t)    

def pausetext():
    if animation.paused:
        return 'Resume'  
    else:
        return 'Pause'  
        
def tracetext():
    if animation.env._trace:
        return 'Trace off'
    else:
        return 'Trace on'
            
        
def _reformatname(name,_nameserialize):
    L=20
    if name in _nameserialize:
        next=_nameserialize[name]+1
    else: 
        next=1
    _nameserialize[name]=next        
    if (len(name)!=0) and (name[len(name)-1]=='.'):
        nextstring='%d'%next
        if len(name)+len(nextstring)>L:
            name=name[0:L-len(nextstring)]
        return name+(L-len(name)-len(nextstring))*'.'+nextstring,name,next
    else:
        return name,name,next    

def pad(txt,n):
    return txt.ljust(n)[:n]
    
def rpad(txt,n):
    return txt.rjust(n)[:n]

def time_to_string(t):
    if t==inf:
        s='inf'
    else:
        s='%10.3f'%t
    return rpad(s,10)
    
def _urgenttxt(urgent):
    if urgent:
        return ' urgent'
    else:
        return '' 
        
def _atprocess(process):
    if process.__name__=='process':
        return ''
    else:
        return (' @ '+process.__name__)

def trace(value=None):
    if value!=None:
        default_env._trace=value
    return default_env._trace
    
def now():
    '''
    returns now for the default environment
    '''
    return default_env._now
    
def current_component():
    '''
    returns the current component for the default environment
    '''
    return default_env.current_component
    
def print_trace(*args,**kwargs):
    default_env.trace.print_trace(*args,**kwargs)


def pythonistacolor(c):
    return (c[0]/255,c[1]/255,c[2]/255,c[3]/255)
        

    
'''
initialization of globals
'''
animation=None
_nameserializeE={}
default_env=Environment(trace=False,name='default environment')
main=default_env._main
random=random.Random(-1)

if __name__ == '__main__':
    try:
        import salabim_test
        salabim_test.test1()
    except:
        pass






