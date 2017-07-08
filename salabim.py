'''
salabim  discrete event simulation module

The MIT License (MIT)

Copyright (c) 2017 Ruud van der Ham, Upward Systems

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

www.salabim.org
'''

from __future__ import print_function # compatibility with Python 2.x
from __future__ import division # compatibility with Python 2.x

import platform
Pythonista=(platform.system()=='Darwin')


import heapq
import random
import time
import math
import copy
import collections

try:
    import numpy
    import cv2
    numpy_and_cv2_installed=True
except:
    numpy_and_cv2_installed=False

try:
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
    pil_installed=True
except:
    pil_installed=False

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
    inf=float('inf')
    nan=float('nan')

__version__='1.1.1'

data='data'
current='current'
standby='standby'
passive='passive'
scheduled='scheduled'

class SalabimException(Exception):
    def __init__(self,value):
        self.value=value
        
    def __str__(self):
        return self.value

if Pythonista:
        
    class MyScene(scene.Scene):
        ''' internal class for Pythonista animation '''
        def __init__(self,*args,**kwargs):
            scene.Scene.__init__(self,*args,**kwargs)
            An.scene=self

        def setup(self):
            pass
        
        def touch_ended(self,touch):
            for uio in An.env.ui_objects:            
                if uio.type=='button':
                    if touch.location in \
                      scene.Rect(uio.x-2,uio.y-2,uio.width+2,uio.height+2):
                        uio.action()
                if uio.type=='slider':
                    if touch.location in\
                      scene.Rect(uio.x-2,uio.y-2,uio.width+4,uio.height+4):
                        xsel=touch.location[0]-uio.x
                        uio._v=uio.vmin+round(-0.5+xsel/uio.xdelta)*uio.resolution
                        if uio.action!=None:
                            uio.action(uio._v)                        
                                  
        def draw(self):   
            
            if An.env!=None:
                scene.background(pythonistacolor(colorspec_to_tuple(An.background_color)))
                if An.paused:
                    An.t = An.start_animation_time
                else:
                    An.t = \
                      An.start_animation_time+\
                      ((time.time()-\
                      An.start_animation_clocktime)*An.env.speed)                

                while An.env.peek<An.t:
                    An.env.step()
                    if An.env._current_component==An.env._main:
                        An.env.print_trace(\
                          '%10.3f' % An.env._now,\
                          An.env._main._name,'current')                            
                        An.env._main._scheduled_time=inf
                        An.env._main._status=current
                        An.env.an_quit()
                        return

                if not An.paused:
                    An.frametimes.append(time.time())
                    
                An.env.an_objects.sort\
                  (key=lambda obj:(-obj.layer(An.t),obj.sequence))
                touchvalues=self.touches.values()
                
                capture_image=Image.new('RGB',
                  (An.width,An.height),colorspec_to_tuple(An.background_color))
                                
                for ao in An.env.an_objects:
                    ao.make_pil_image(An.t)
                    if ao._image_visible:
                        capture_image.paste(ao._image,
                          (int(ao._image_x),
                          int(An.height-ao._image_y-ao._image.size[1])),
                          ao._image)
                              
                ims=scene.load_pil_image(capture_image)
                scene.image(ims,0,0,*capture_image.size)                
                   
                for uio in An.env.ui_objects:
                                                                          
                    if uio.type=='button':
                        linewidth=uio.linewidth
                            
                        scene.push_matrix()
                        scene.fill(pythonistacolor(uio.fillcolor))
                        scene.stroke(pythonistacolor(uio.linecolor))
                        scene.stroke_weight(linewidth)
                        scene.rect(uio.x,uio.y,uio.width,uio.height)
                        scene.tint(uio.color)
                        scene.translate(uio.x+uio.width/2,uio.y+uio.height/2)
                        scene.text(uio.text(),uio.font,uio.fontsize,alignment=5)
                        scene.tint(1,1,1,1)
                          #required for proper loading of images 
                        scene.pop_matrix()
                    elif uio.type=='slider':
                        scene.push_matrix()
                        scene.tint(pythonistacolor(uio.labelcolor))   
                        v=uio.vmin
                        x=uio.x+uio.xdelta/2
                        y=uio.y
                        mindist=inf
                        v=uio.vmin
                        while v<=uio.vmax:
                            if abs(v-uio.v)<mindist:
                                mindist=abs(v-uio._v)
                                vsel=v
                            v+=uio.resolution
                        thisv=uio._v
                        for touch in touchvalues:
                            if touch.location in\
                              scene.Rect(uio.x,uio.y,uio.width,uio.height):
                                xsel=touch.location[0]-uio.x
                                vsel=round(-0.5+xsel/uio.xdelta)*uio.resolution
                                thisv=vsel
                        scene.stroke(pythonistacolor(uio.linecolor))
                        v=uio.vmin
                        xfirst=-1
                        while v<=uio.vmax:
                            if xfirst==-1:
                                xfirst=x
                            if v==vsel:
                                scene.stroke_weight(3)
                            else:
                                scene.stroke_weight(1)
                            scene.line(x,y,x,y+uio.height)
                            v+=uio.resolution
                            x+=uio.xdelta
                                
                                
                        scene.push_matrix()
                        scene.translate(xfirst,uio.y+uio.height+2)
                        scene.text(uio.label,uio.font,uio.fontsize,alignment=9)     
                        scene.pop_matrix()
                        scene.translate(uio.x+uio.width,y+uio.height+2)    
                        scene.text(str(thisv)+' ',\
                          uio.font,uio.fontsize,alignment=7)                 
                        scene.tint(1,1,1,1)
                          #required for proper loading of images later                                
                        scene.pop_matrix() 
                                                                               
class Qmember():
    ''' internal class '''
    
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
        for iter in q._iter_touched:
            q._iter_touched[iter]=True
        q._maximum_length=max(q._maximum_length,q._length)
        c._qmembers[q]=self
        q.env.print_trace('','',c._name,'enter '+q._name)        

class Queue(object):
    '''
    queue object
    
    Parameters
    ----------
    name : str
        name of the queue |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if omitted, the name queue (serialized)
    env : Environment
        environment where the queue is defined |n|
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
          _reformatname(name,self.env._nameserializeQueue)
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
        self._iter_sequence=0
        self._iter_touched={}
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
        
        Parameters
        ----------
        txt : str
            name of the queue |n|
            if txt ends with a period, the name will be serialized
        '''
        return self._name
        
    @name.setter
    def name(self,txt):
        self._name,self._base_name,self._sequence_number=\
          _reformatname(txt,self.env._nameserializeQueue)
        
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
    
        Parameters
        ----------
        component : Component
            component to be added to the tail of the queue |n|
            may not be member of the queue yet
                                 
        the priority will be set to
        the priority of the tail of the queue, if any
        or 0 if queue is empty
        '''
        component.enter(self)

    def add_at_head(self,component):
        '''
        adds a component to the head of a queue
    
        Parameters
        ----------
        
        component : Component
            component to be added to the head of the queue |n|
            may not be member of the queue yet
                                 
        the priority will be set to 
        the priority of the head of the queue, if any
        or 0 if queue is empty
        '''
        component.enter_to_head(self)

    def add_in_front_of(self,component,poscomponent):
        '''
        adds a component to a queue, just in front of a component
    
        Parameters
        ----------
        component : Component
            component to be added to the queue |n|
            may not be member of the queue yet
                        
        poscomponent : Component
            component in front of which component will be inserted |n|
            must be member of the queue
        
        the priority of component will be set to the priority of poscomponent 
        '''
        component.enter_in_front_off(self,poscomponent)

    def add_behind(self,component,poscomponent):
        '''
        adds a component to a queue, just behind a component
    
        Parameters
        ----------
        component : Component
            component to be added to the queue |n|
            may not be member of the queue yet
                        
        poscomponent : Component
            component behind which component will be inserted |n|
            must be member of the queue
        
        the priority of component will be set to the priority of poscomponent 
        '''
        component.enter_behind(self,poscomponent) 
        
    def add_sorted(self,component,priority):
        '''
        adds a component to a queue, according to the priority
    
        Parameters
        ----------
        component : Component
            component to be added to the queue |n|
            may not be member of the queue yet
                        
        priority : float
            priority of the component|n|
            
        component will be placed just after the last component with
        a priority <= priority
        '''
        component.enter_sorted(self,priority)

    def remove(self,component):
        '''
        removes component from the queue
    
        Parameters
        ----------
        component : Component
           component to be removed |n|
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
        removes the head component and returns it, if any. |n|
        Otherwise return None
        '''
        c=self.head
        if c!=None:
            c.leave(self)
        return c
    
    def successor(self,component):
        ''' 
        successor in queue
        
        Parameters
        ----------
        component : Component
            component whose successor to return |n|
            must be member of the queue
         
        returns the successor of component, if any. None otherwise
        '''
        return component.successor(self)                

    def predecessor(self,component):
        ''' 
        predecessor in queue
        
        Parameters
        ----------
        component : Component
            component whose predecessor to return |n|
            must be member of the queue
         
        returns the predcessor of component, if any. None otherwise
        '''
        return component.predecessor(self)   
        
    def __contains__ (self,component):
        return component._member(self)!=None
        
    def __getitem__(self,key):
        if isinstance( key, slice) :
            #Get the start, stop, and step from the slice
            startval,endval,incval=key.indices(self._length)
            if incval>0:
                l=[]
                targetval=startval
                mx=self._head.successor
                count=0
                while mx!=self._tail:
                    if targetval>=endval:
                        break
                    if targetval==count:
                        l.append(mx.component)
                        targetval += incval
                    count += 1
                    mx=mx.successor
            else:
                l=[]
                targetval=startval
                mx=self._tail.predecessor
                count=self._length-1
                while mx!=self._head:
                    if targetval<=endval:
                        break
                    if targetval==count:
                        l.append(mx.component)
                        targetval += incval #incval is negative here!
                    count -= 1
                    mx=mx.predecessor                    
                                
            return list(l)
            
        elif isinstance( key, int ) :
            if key < 0 : #Handle negative indices
                key += self._length
            if key < 0 or key >= self._length:
                return None
            mx=self._head.successor
            count=0
            while mx!=self._tail:
                if count==key:
                    return mx.component
                count=count+1
                mx=mx.successor

            return None #just for safety
                        
        else:
            raise TypeError('Invalid argument type.')        
        
    def __len__(self):
        return self._length
        
    def __reversed__(self):
        self._iter_sequence += 1
        iter_sequence = self._iter_sequence
        self._iter_touched[iter_sequence] = False
        iter_list = []
        mx = self._tail.predecessor
        while mx != self._head:
            iter_list.append(mx)
            mx = mx.predecessor
        iter_index = 0
        while len(iter_list)>iter_index:
            if self._iter_touched[iter_sequence]:
                iter_list=iter_list[:iter_index] #place all taken qmembers on the list
                mx = self._tail.predecessor
                while mx != self._head:
                    if mx not in iter_list:
                        iter_list.append(mx)
                    mx = mx.precessor
                self._iter_touched[iter_sequence]=False
            else:
                c = iter_list[iter_index].component
                if c is not None: # skip deleted components
                    yield c
                iter_index += 1
                                        
        del self._iter_touched[iter_sequence]

                
    def index_of(self,component):
        '''
        get the index of a component in the queue
        
        Parameters
        ----------
        component : Component
            component to be queried |n|
            does not need to be in the queue
                                 
        returns the index of component in the queue, where 0 denotes the head,
        if in the queue. |n|
        returns -1 if component is not in the queue
        '''
        return component.index_in_queue(self)
        
    def component_with_name(self,txt):
        '''
        returns a component in the queue according to its name
        
        Parameters
        ----------
        txt : str
            name of component to be retrieved
            
        returns the first component in the queue with name txt. |n|
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
        
        it is advised to use the builtin len function.
        '''
        return self._length
        
    @property
    def minimum_length(self):
        '''
        returns the minimum length of a queue
        since the last reset_statistics
        '''
        return self._minimum_length
        
    @property
    def maximum_length(self):
        '''
        returns the maximum length of a queue
        since the last reset_statistics
        '''
        return self._maximum_length
        
    @property
    def minimum_length_of_stay(self):
        '''
        returns the minimum length of stay of components left the queue
        since the last reset_statistics. |n|
        returns nan if no component has left the queue
        '''
        if self._number_passed==0:
            return nan
        else:
            return self._minimum_length_of_stay
        
    @property
    def maximum_length_of_stay(self):
        '''
        returns the maximum length of stay of components left the queue
        since the last reset_statistics. |n|
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
        with a zero length of stay
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
        returns the mean length of the queue
        since the last reset_statistics
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
                         
    def __iter__(self):
        self._iter_sequence += 1
        iter_sequence = self._iter_sequence
        self._iter_touched[iter_sequence] = False
        iter_list = []
        mx = self._head.successor
        while mx != self._tail:
            iter_list.append(mx)
            mx = mx.successor
        iter_index = 0
        while len(iter_list)>iter_index:
            if self._iter_touched[iter_sequence]:
                iter_list=iter_list[:iter_index] #place all taken qmembers on the list
                mx = self._head.successor
                while mx != self._tail:
                    if mx not in iter_list:
                        iter_list.append(mx)
                    mx = mx.successor
                self._iter_touched[iter_sequence]=False
            else:
                c = iter_list[iter_index].component
                if c is not None: # skip deleted components
                    yield c
                iter_index += 1
                                        
        del self._iter_touched[iter_sequence]
    
                            
    def union(self,q,name):
        '''
        returns the union of two queues
        
        Parameters
        ----------
        q : Queue
            queue to be unioned with self
                
        name :str
            name of the  new queue
            
        the resulting queue will contain all elements of self and q |n|
        the priority will be set to 0 for all components in the
        resulting  queue |n|
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
        
        Parameters
        ----------
        q : Queue
            queue to be intersected with self
                
        name :str
            name of the  new queue
            
        the resulting queue will contain all elements that
        are in self and q |n|
        the priority will be set to 0 for all components in the
        resulting  queue |n|
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
        
        Parameters
        ----------
        q : Queue
            queue to be 'subtracted' from self
                
        name :str
            name of the  new queue
            
        the resulting queue will contain all elements of self that are not
        in q |n|
        the priority will be copied from the original queue.
        Also, the order will be maintained.
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
        
        Parameters
        ----------
        name : str
            name of the new queue
                 
        the resulting queue will contain all elements of self |n|
        The priority will be copied from original queue.
        Also, the order will be maintained.
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
        
        Parameters
        ----------
        name : str
            name of the new queue

        the resulting queue will contain all elements of self,
          with the proper priority |n|
        self will be emptied
        '''
        q1=self.copy(name)
        self.clear()
        return q1
      
    def clear(self):
        '''
        empties a queue
            
        removes all components from a queue
        '''
        mx=self._head.successor
        while mx!=self._tail:
            c=mx.component
            mx=mx.successor
            c._leave(self)
        
    def reset_statistics(self):
        '''
        resets the statistics of a queue
        '''        
    
        self._minimum_length_of_stay=inf
        self._maximum_length_of_stay=-inf
        self._minimum_length=self._length
        self._maximum_length=self._length
        self._number_passed=0
        self._number_passed_direct=0
        self._total_length_of_stay=0
        mx=self._head.successor
        while mx!=self._tail:
            c=mx.component
            self._total_length_of_stay-(self.env._now-c.enter_time)
            mx=mx.successor
        self._start_statistics=self.env._now
        

def run(*args,**kwargs):
    '''
    run for the default environment
    '''

    default_env.run(*args,**kwargs)
    
def animation_parameters(*args,**kwargs):
    '''
    animation_parameters for the default environment
    '''

    default_env.animation_parameters(*args,**kwargs)
    
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
        
def finish():
    raise SalabimException('Stopped by user')    
    if Pythonista:
        if An.scene!=None:
            An.scene.view.close()
              
class Environment(object): 
    '''
    environment object
    
    Parameters
    ----------
    trace : bool
        defines whether to trace or not |n|
        if omitted, False
        
    name : str
        name of the environment |n|.
        if the name ends with a period (.), 
        auto serializing will be applied |n|
        if omitted, the name ``environment`` (serialized)

    The trace may be switched on/off later with trace     
    '''
        
    _name_serialize={}
          
    def __init__(self,trace=False,name=None): 
        if name is None:
            name='environment.'
        self._name,self._base_name,self._sequence_number=\
          _reformatname(name,Environment._name_serialize)
        self.env=self 
        self._nameserializeComponent={} # just to allow main to be created; will be reset later
        self._now=0 #just to allow main to be created; will be reset later    
        self._main=Component(name='main',env=self)
        self._main._status=current
        self._current_component=self._main
        self.ui_objects=[]
        self.reset(trace)
        self.print_trace('%10.3f' % self._now,'main','current')   

                               
    def serialize(self):
        self.serial+=1
        return self.serial


    def __repr__(self):
        lines=[]
        lines.append('Environment '+hex(id(self)))
        lines.append('  name='+self._name+(' (animation environment)' if self==An.env else ''))
        lines.append('  now='+time_to_string(self._now))
        lines.append('  current_component='+self._current_component._name)
        lines.append('  trace='+str(self._trace))      
        return '\n'.join(lines)
        
        
    def reset(self,trace=False):
        '''
        resets the enviroment
        
        Parameters
        ----------
        trace : bool
            defines whether to trace or not |n|
            if omitted, False
                                                
        The trace may be switched on/off later with trace
        '''
        self._main._checkcurrent()
        self._trace=trace
        self._now=0
        self._nameserializeQueue={}
        self._nameserializeComponent={}
        self._nameserializeResource={}
        self._seq=0
        self._event_list=[]
        self._standbylist=[]
        self._pendingstandbylist=[]
        
        if An.env==self:
            for uio in self.ui_objects[:]:
               uio.remove()

        self.an_objects=[]
        self.ui_objects=[]
        self.serial=0
        self.speed=1
        self.animate=False
        if Pythonista:
            self.width,self.height=ui.get_screen_size()
            self.width=int(self.width)
            self.height=int(self.height)
        else:
            self.width=1024
            self.height=768
        self.x0=0
        self.y0=0
        self.x1=self.width
        self.background_color='white'
        self.fps=30
        self.modelname=''
        self.use_toplevel=False
        self.show_fps=True
        self.show_speed=True
        self.show_time=True
        self.video=''

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
        gets or sets trace
        '''
        return self._trace
        
    @trace.setter
    def trace(self,value):
        self._trace=value
        
    @property
    def current_component(self):
        '''
        returns the current_component
        '''
        return self._current_component
        
    def animation_parameters(self,
      animate=None,speed=None,width=None,height=None,
      x0=None,y0=0,x1=None,background_color=None,
      fps=None,modelname=None,use_toplevel=None,
      show_fps=None,show_speed=None,show_time=None,
      video=None):

        '''
        set animation parameters

        Parameters:
        -----------
        animate : bool
            animate indicator |n|
            if omitted, True, i.e. animation |n|
            Installation of PIL is required for animation.
            
        speed : float
            speed |n|
            specifies how much faster or slower than real time the animation will run. 
            e.g. if 2, 2 simulation time units will be displayed per second.
            
        background_color : colorspec
            color of the background |n|
            if omitted, no change
                        
        width : int
            width of the animation in screen coordinates (default 1024)
            
        height : int
            height of the animation in screen coordinates (default 768)
            
        x0 : float
            user x-coordinate of the lower left corner (default 0)
            
        y0 : float
            user y_coordinate of the lower left corner (default 0)
            
        x1 : float
            user x-coordinate of the upper right corner (default 1024)
        
        fps : float
            number of frames per second
            
        modelname : str
            name of model to be shown in upper left corner,
            along with text 'a salabim model'
            
        use_toplevel : bool
            if salabim animation is used in parallel with
            other modules using tkinter, it might be necessary to 
            initialize the root with tkinter.TopLevel().
            In that case, set this parameter to True. |n|
            if False (default), the root will be initialized with tkinter.Tk()
    
        show_fps : bool
            if True, show the number of frames per second (default)|n|
            if False, do not show the number of frames per second

        show_speed: bool
            if True, show the animation speed (default)|n|
            if False, do not show the animation speed

        show_time: bool
            if True, show the time (default)|n|
            if False, do not show the time
            
        video : str
            if video is not omitted, a mp4 format video with the name video 
            will be created. |n|
            The video has to have a .mp4 etension |n|
            This requires installation of numpy and opencv (cv2).
                          
        The y-coordinate of the upper right corner is determined automatically
        in such a way that the x and scaling are the same. |n|

        Note that changing the parameters x0, x1, y0, width, height, background_color, modelname,
        use_toplevelmand video, animate has no effect on the current animation.
        So to avoid confusion, do not use change these parameters when an animation is running. |n|
        On the other hand, changing speed, show_fps, show_time, show_speed and fps can be useful in
        a running animation.
        '''
        
        if speed!=None:
            self.speed=speed
            if An.env==self:
                An.set_start_animation()
                        
        if show_fps!=None:
            self.show_fps=show_fps
        if show_speed!=None:
            self.show_speed=show_speed
        if show_time!=None:
            self.show_time=show_time
                                                                      
        if animate==None:
            self.animate=True
        else:
            self.animate=animate
        if width!=None:
            self.width=width
        if height!=None:
            self.height=height
        if x0!=None:
            self.x0=x0
        if x1!=None:
            self.x1=x1
        if y0!=None:
            self.y0=y0
        if background_color!=None:
            self.background_color=background_color
        if fps!=None:
            self.fps=fps
        if modelname!=None:
            self.modelname=modelname
        if use_toplevel!=None:
            self.use_toplevel=use_toplevel
        if video!=None:
            self.video=video

    def run(self,duration=None,till=None):
        '''
        start execution of the simulation

        Parameters:
        -----------
        duration : float
            schedule with a delay of duration |n|
            if 0, now is used
            
        till : float
            schedule time |n|
            if omitted, 0 is assumed
          
        only issue run from the main level
        '''

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

        if self.animate:
            if not pil_installed:
                raise AssertionError('PIL is required for animation')

            An.font_cache={}
            An.t=self.env._now # for the call to set_start_animation
            An.set_start_animation()
            An.stopped=False
            An.running=True
            An.paused=False
            An.background_color=self.background_color
            An.width=self.width
            An.height=self.height
            An.x0=self.x0
            An.x1=self.x1
            An.y0=self.y0
            An.scale=An.width/(An.x1-An.x0)            
            An.env=self
                         
            if Pythonista:
                if An.scene==None:
                    scene.run\
                      (MyScene(), frame_interval=60/self.fps,
                      show_fps=False)
                    # this also assigns an_scene
            else:         
                if self.use_toplevel:
                    An.root = tkinter.Toplevel()
                else:
                    An.root = tkinter.Tk()
                An.canvas = \
                  tkinter.Canvas(An.root, width=An.width,height = An.height)
                An.canvas.configure\
                  (background=colorspec_to_hex(self.background_color,False))
                An.canvas.pack()
                An.canvas_objects=[]

            for uio in self.ui_objects:
                if not Pythonista:
                    uio.install()

            An.system_an_objects=[]
            An.system_ui_objects=[]
            if self.modelname!='':
                ao=Animate(text=self.modelname,
                    x0=8,y0=self.height-60,
                    anchor='w',fontsize0=30,textcolor0='black',
                    screen_coordinates=True,env=self )
                An.system_an_objects.append(ao)
                ao=Animate(text='a salabim model',
                    x0=8,y0=self.height-78,
                    anchor='w',fontsize0=16,textcolor0='red',screen_coordinates=True,env=self)
                An.system_an_objects.append(ao)                    
    
            uio=AnimateButton\
              (x=48,y=self.height-21,text='Stop',\
               action=self.env.an_stop,env=self)
            An.system_ui_objects.append(uio)
            uio=AnimateButton\
              (x=48+1*90,y=self.height-21,text='Anim/2',\
              action=self.env.an_half,env=self) 
            An.system_ui_objects.append(uio)
            uio=AnimateButton\
              (x=48+2*90,y=self.height-21,text='Anim*2',\
              action=self.env.an_double,env=self)
            An.system_ui_objects.append(uio)
            uio=AnimateButton\
              (x=48+3*90,y=self.height-21,text='',\
              action=self.env.an_pause,env=self)
            An.system_ui_objects.append(uio)
            uio.text=lambda :pausetext()
            uio=AnimateButton\
              (x=48+4*90,y=self.height-21,text='',\
              action=self.env.an_trace,env=self)                                                                                  
            An.system_ui_objects.append(uio)
            uio.text=tracetext
            ao=Animate\
              (x0=An.width,y0=An.height-5,fillcolor0='black',\
                text='',fontsize0=15,font='DejaVuSansMono',anchor='ne',\
                screen_coordinates=True,env=self)
            An.system_an_objects.append(ao)                    
            ao.text=clocktext
            if self.video=='':
                An.dovideo=False
            else:
                An.dovideo=True
                if not numpy_and_cv2_installed:
                    raise AssertionError('numpy and cv2 required for video production')
                                
            if An.dovideo:
                An.video_sequence=0
                fourcc = cv2.VideoWriter_fourcc(*'MP4V')
                An.out = cv2.VideoWriter(self.video,fourcc, self.fps, (An.width,An.height)) 

            if Pythonista:
                while An.running:
                    pass
            else:
                An.root.after(0,self.simulate_and_animate_loop)
                An.root.mainloop()
                if An.dovideo:
                    An.out.release()
            if An.stopped:
                finish()
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
        An.running=True
        
        while An.running:
            tick_start=time.time()
            if An.dovideo:
                An.t=An.start_animation_time+An.video_sequence*self.speed/self.fps
            else:
                if An.paused:
                    An.t=An.start_animation_time
                else:
                    An.t=An.start_animation_time+\
                      ((time.time()-An.start_animation_clocktime)*\
                      self.speed)

            while self.peek<An.t:
                self.step()
                if self._current_component==self._main:
                    self.print_trace('%10.3f' % self._now,\
                      self._main._name,'current')                            
                    self._scheduled_time=inf
                    self._status=current
                    An.running=False
                    self.an_quit()
                    return
            if not An.running:
                break
            
            if An.dovideo:
                capture_image=Image.new('RGB',(An.width,An.height),colorspec_to_tuple(An.background_color))
                
            if not An.paused:
                An.frametimes.append(time.time())

            self.an_objects.sort\
              (key=lambda obj:(-obj.layer(An.t),obj.sequence))
              
            canvas_objects_iter=iter(An.canvas_objects[:])
            co=next(canvas_objects_iter,None)
            
            for ao in self.an_objects:

                ao.make_pil_image(An.t)
                if ao._image_visible:
                    if co==None:
                        ao.im = ImageTk.PhotoImage(ao._image)
                        co1=An.canvas.create_image(
                          ao._image_x,self.height-ao._image_y,image=ao.im,anchor=tkinter.SW)
                        An.canvas_objects.append(co1)
                        ao.canvas_object=co1

                    else:
                        if ao.canvas_object==co:
                            if ao._image_ident!=ao._image_ident_prev:
                                ao.im = ImageTk.PhotoImage(ao._image)
                                An.canvas.itemconfig(ao.canvas_object,image=ao.im)    
                                          
                            if (ao._image_x!=ao._image_x_prev) or (ao._image_y!=ao._image_y_prev):
                                An.canvas.coords(ao.canvas_object,(ao._image_x,self.height-ao._image_y))                                            

                        else:
                            ao.im = ImageTk.PhotoImage(ao._image)
                            ao.canvas_object=co
                            An.canvas.itemconfig(ao.canvas_object,image=ao.im)    
                            An.canvas.coords(ao.canvas_object,(ao._image_x,An.height-ao._image_y))
                    co=next(canvas_objects_iter,None)
                    
                    if An.dovideo:
                        capture_image.paste(ao._image,
                          (int(ao._image_x),
                          int(An.height-ao._image_y-ao._image.size[1])),
                          ao._image)
                else:
                    ao.canvas_object=None
                                                    
            for co in canvas_objects_iter:
                An.canvas.delete(co)
                An.canvas_objects.remove(co)
                    
            for uio in self.ui_objects:
                if not uio.installed:
                    uio.install()
 
            for uio in self.ui_objects:
                if uio.type=='button':
                    thistext=uio.text()
                    if thistext!=uio.lasttext:
                        uio.lasttext=thistext
                        uio.button.config(text=thistext)       

            if An.dovideo:
                open_cv_image = numpy.array(capture_image) 
                   # Convert RGB to BGR 
                open_cv_image = open_cv_image[:, :, ::-1].copy() 
                open_cv_image=cv2.cvtColor(numpy.array(capture_image), cv2.COLOR_RGB2BGR)
                An.out.write(open_cv_image)
                An.video_sequence += 1
                
            An.canvas.update()
            if not An.dovideo:
                tick_duration=time.time()-tick_start  
                if tick_duration<1/self.fps:
                    time.sleep((1/self.fps)-tick_duration)

    def an_quit(self):
        An.running=False

        for ao in An.system_an_objects:
            ao.remove()
        for uio in An.system_ui_objects:
            uio.remove()

        for uio in self.ui_objects:
            if uio.type=='slider':
                uio._v=uio.v
            uio.installed=False
                
        if not Pythonista:
            An.root.destroy()
        An.env=None

    def an_half(self):
        if An.paused:
            An.paused=False
        else:
            self.speed /=2
            An.set_start_animation() 

    def an_double(self):
        if An.paused:
            An.paused=False
        else:
            self.speed *=2
            An.set_start_animation()            
    
    def an_pause(self):
        An.paused=not An.paused
        An.set_start_animation()        
         
    def an_stop(self):
        self.an_quit()
        An.stopped=True
                
    def an_trace(self):
        self._trace=not self._trace  

        
    @property
    def name(self):
        '''
        returns and/or sets the name of an environmnet
        
        Parameters
        ----------
        txt : str
            gets/sets name of the environment |n|
            if txt ends with a period, the name will be serialized
        '''
        return self._name
        
    @name.setter
    def name(self,txt):
        self._name,self._base_name,self._sequence_number=\
          _reformatname(txt,Environment._nameserialize)
        
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
class An():
    env=None
    scene=None
    
    def set_start_animation():
        An.frametimes=collections.deque(maxlen=30)
        An.start_animation_time=An.t
        An.start_animation_clocktime=time.time()

class Animate(object):
    '''
    defines an animation object
    
    Parameters
    ----------
    parent : Component
        component where this animation object belongs to (default None) |n|
        if given, the animation ofject will be removed
        automatically upon termination of the parent
    
    layer : int
         layer value |n|
         lower layer values are on top of higher layer values (default 0)

    keep : bool
        keep |n|
        if False, animation object is hidden after t1, shown otherwise
        (default True)
            
    screen_coordinates : bool
        use screen_coordinates |n|
        normally, the scale parameters are use for positioning and scaling
        objects. |n|
        if True, screen_coordinates will be used instead.
    
    t0 : float
        time of start of the animation (default: now)
    
    x0 : float
        x-coordinate of the origin (default 0) at time t0
    
    y0 : float
        y-coordinate of the origin (default 0) at time t0
    
    offsetx0 : float
        offsets the x-coordinate of the object (default 0) at time t0
    
    offsety0 : float
        offsets the y-coordinate of the object (default 0) at time t0
    
    circle0 : tuple
         the circle at time t0 specified as a tuple (radius,)
    
    line0 : tuple
        the line(s) at time t0 (xa,ya,xb,yb,xc,yc, ...)
            
    polygon0 : tuple
        the polygon at time t0 (xa,ya,xb,yb,xc,yc, ...) |n|
        the last point will be auto connected to the start
    
    rectangle0 : tuple
        the rectangle at time t0 |n| 
        (xlowerleft,ylowerlef,xupperright,yupperright)
    
    image : str or PIL image
        the image to be displayed |n|
        This may be either a filename or a PIL image
    
    text : str
        the text to be displayed
    
    font : str or list/tuple
        font to be used for texts |n|
        Either a string or a list/tuple of fontnames.
        If not found, uses calibri or arial
            
    anchor : str
        anchor position |n|
        specifies where to put images or texts relative to the anchor
        point |n|
        possible values are (default: center): |n|
        ``nw    n    ne`` |n|
        ``w   center  e`` |n|
        ``sw    s    se``  
    
    linewidth0 : float
        linewidth of the contour at time t0 (default 0 = no contour)
            
    fillcolor0 : colorspec
        color of interior at time t0 (default black)
            
    linecolor0 : colorspec
        color of the contour at time t0 (default black)
        
    textcolor0 : colorspec
        color of the text at time 0 (default black)
            
    angle0 : float
        angle of the polygon at time t0 (in degrees) (default 0)
            
    fontsize0 : float
        fontsize of text at time t0 (default: 20)
            
    width0 : float
       width of the image to be displayed at time t0 (default: no scaling)
    
    t1 : float
        time of end of the animation (default: inf) |n|
        if keep=True, the animation will continue (frozen) after t1
    
    x1 : float
        x-coordinate of the origin (default x0) at time t1
    
    y1 : float
        y-coordinate of the origin (default y0) at time t1
    
    offsetx1 : float
        offsets the x-coordinate of the object (default offsetx0) at time t1
    
    offsety1 : float
        offsets the y-coordinate of the object (default offsety0) at time t1
    
    circl10 : tuple
         the circle at time t1 specified as a tuple (radius,)
    
    line1 : tuple
        the line(s) at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: line0) |n|
        should have the same length as line0
            
    polygon1 : tuple
        the polygon at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: polygon0) |n|
        should have the same length as polygon0
    
    rectangle1 : tuple
        the rectangle at time t1 (default: rectangle0) |n| 
        (xlowerleft,ylowerlef,xupperright,yupperright)
    
    linewidth1 : float
        linewidth of the contour at time t1 (default linewidth0)
            
    fillcolor1 : colorspec
        color of interior at time t1 (default fillcolor0)
            
    linecolor1 : colorspec
        color of the contour at time t1 (default linecolor0)
            
    textcolor1 : colorspec
        color of text at time t1 (default textcolor0)
            
    angle1 : float
        angle of the polygon at time t1 (in degrees) (default angle0)
            
    fontsize1 : float
        fontsize of text at time t1 (default: fontsize0)
            
    width1 : float
       width of the image to be displayed at time t1 (default: width0) |n|
       
       
        
    note that one (and only one) of the following parameters is required:
         - circle0
         - image
         - line0
         - polygon0
         - rectangle0
         - text
        
    colors may be specified as a
        - valid colorname
        - hexname
        - tuple (R,G,B) or (R,G,B,A)
    colornames may contain an additional alpha, like ``red#7f``
    hexnames may be either 3 of 4 bytes long (RGB or RGBA)
    both colornames and hexnames may be given as a tuple with an
    additional alpha between 0 and 255,
    e.g. ``('red',127)`` or ``('#ff00ff',128)``        
        
    Permitted parameters
    
    ======================  ========= ========= ========= ========= ========= =========
    parameter               circle    image     line      polygon   rectangle text     
    ======================  ========= ========= ========= ========= ========= =========
    parent                  -         -         -         -         -         -              
    layer                   -         -         -         -         -         -              
    keep                    -         -         -         -         -         -              
    scree_coordinates       -         -         -         -         -         -
    t0,t1                   -         -         -         -         -         -              
    x0,x1                   -         -         -         -         -         -              
    y0,y1                   -         -         -         -         -         -              
    offsetx0,offsetx1       -         -         -         -         -         -              
    offsety0,offsety1       -         -         -         -         -         -              
    circle0,circle1         -
    image                             -
    line0,line1                                 -
    polygon0,polygon1                                     -
    rectangle0,rectangle1                                           -
    text                                                                      -
    font
    anchor                            -                                       -    
    linewidth0,linewidth1    -                  -         -         -                
    fillcolor0,fillcolor1    -                            -         -
    linecolor0,linecolor1    -                  -         -         -
    textcolor0,textcolor1.                                                    -
    angle0,angle1                     -         -         -         -         -
    font                                                                      -
    fontsize0,fontsize1                                                       -
    width0,width1                     -                                   
    ======================  ========= ========= ========= ========= ========= ========= 
    '''

    def make_pil_image(self,t):
        
        visible=self.visible(t)

        if (t>=self.t0) and ((t<=self.t1) or self.keep) and visible:
            self._image_visible=True
            self._image_x_prev=self._image_x
            self._image_y_prev=self._image_y
            self._image_ident_prev=self._image_ident  
                      
            x=self.x(t)
            y=self.y(t)
            offsetx=self.offsetx(t)
            offsety=self.offsety(t)
            angle=self.angle(t)
                                  
            if (self.type=='polygon') or (self.type=='rectangle') or (self.type=='line'):
                linewidth=self.linewidth(t)*An.scale
                linecolor=colorspec_to_tuple(self.linecolor(t))
                fillcolor=colorspec_to_tuple(self.fillcolor(t))
                                        
                cosa=math.cos(angle*math.pi/180)
                sina=math.sin(angle*math.pi/180)                    

                if self.type=='rectangle': 
                    rectangle=self.rectangle(t)
                    p=[
                     rectangle[0],rectangle[1],
                     rectangle[2],rectangle[1],
                     rectangle[2],rectangle[3],
                     rectangle[0],rectangle[3],
                     rectangle[0],rectangle[1]]


                elif self.type=='line':
                    p=self.line(t)
                    fillcolor=(0,0,0,0)

                else:
                    p=self.polygon(t)
        
                if self.screen_coordinates:
                    qx=x
                    qy=y
                else:
                    qx=(x-An.x0)*An.scale
                    qy=(y-An.y0)*An.scale

                r=[]
                minrx=inf
                minry=inf
                maxrx=-inf
                maxry=-inf
                for i in range(0,len(p),2):
                    px=p[i]
                    py=p[i+1]
                    rx=px*cosa-py*sina
                    ry=px*sina+py*cosa
                    if not self.screen_coordinates:
                        rx=rx*An.scale
                        ry=ry*An.scale
                    minrx=min(minrx,rx)
                    maxrx=max(maxrx,rx)
                    minry=min(minry,ry)
                    maxry=max(maxry,ry)
                    r.append(rx)
                    r.append(ry)
                if self.type=='polygon':
                    if (r[0]!=r[len(r)-2]) or (r[1]!=r[len(r)-1]):
                        r.append(r[0])
                        r.append(r[1])
                      
                rscaled=[]
                for i in range(0,len(r),2):
                    rscaled.append(r[i]-minrx+linewidth)
                    rscaled.append(maxry-r[i+1]+linewidth)
                rscaled=tuple(rscaled) #to make it hashable
        
                self._image_ident=(rscaled,minrx,maxrx,minry,maxry,
                  fillcolor,linecolor,linewidth)
                if self._image_ident!=self._image_ident_prev:
                    self._image=Image.new\
                      ('RGBA',(int(maxrx-minrx+2*linewidth),\
                      int(maxry-minry+2*linewidth)),(0,0,0,0))
                    draw=ImageDraw.Draw(self._image)
                    if fillcolor[3]!=0:
                        draw.polygon(rscaled,fill=fillcolor)
                    if (linewidth>0) and (linecolor[3]!=0):
                        draw.line\
                          (rscaled,fill=linecolor,width=int(linewidth))
       
                self._image_x=qx+minrx-linewidth+(offsetx*cosa-offsety*sina)
                self._image_y=qy+minry-linewidth+(offsetx*sina+offsety*cosa)
                
            elif self.type=='circle':
                linewidth=self.linewidth(t)*An.scale
                fillcolor=colorspec_to_tuple(self.fillcolor(t))
                linecolor=colorspec_to_tuple(self.linecolor(t))
                circle=self.circle(t)
                radius=circle[0]                

                if self.screen_coordinates:
                    qx=x
                    qy=y
                else:
                    qx=(x-An.x0)*An.scale
                    qy=(y-An.y0)*An.scale
                    linewidth*=An.scale
                    radius*=An.scale

                self._image_ident=(radius,linewidth,linecolor,fillcolor)
                if self._image_ident!=self._image_ident_prev:
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
                        

                    self._image=Image.new\
                      ('RGBA',(int(radius*2+2*linewidth),\
                      int(radius*2+2*linewidth)),(0,0,0,0))
                    draw=ImageDraw.Draw(self._image)
                    if fillcolor[3]!=0:
                        draw.polygon(p,fill=fillcolor)
                    if (linewidth>0) and (linecolor[3]!=0):
                        draw.line(p,fill=linecolor,width=int(linewidth))

                dx=offsetx
                dy=offsety
                cosa=math.cos(angle*math.pi/180)
                sina=math.sin(angle*math.pi/180)  
                ex=dx*cosa-dy*sina
                ey=dx*sina+dy*cosa
                self._image_x=qx+ex-radius-linewidth-1
                self._image_y=qy+ey-radius-linewidth-1
        
            elif self.type=='image':
                image,image_serial=self.image(t)
                width=self.width(t)
                height=width*image.size[1]/image.size[0]
                angle=self.angle(t)

                anchor=self.anchor(t)
                if self.screen_coordinates:
                    qx=x
                    qy=y
                else:
                    qx=(x-An.x0)*An.scale
                    qy=(y-An.y0)*An.scale
                    offsetx=offsetx*An.scale
                    offsety=offsety*An.scale
                
                self._image_ident=(image_serial,width,height,angle)
                if self._image_ident!=self._image_ident_prev:
                    if not self.screen_coordinates:
                        width*=An.scale
                        height*=An.scale
                    im1 = image.resize\
                      ((int(width),int(height)), Image.ANTIALIAS)
                    self.imwidth,self.imheight=im1.size
                    
                    self._image = im1.rotate(angle,expand=1)
                    
                anchor_to_dis={
                  'ne':(-0.5,-0.5),
                  'n':(0,-0.5),
                  'nw':(0.5,-0.5),
                  'e':(-0.5,0),
                  'center':(0,0),
                  'w':(0.5,0),\
                  'se':(-0.5,0.5),
                  's':(0,0.5),
                  'sw':(0.5,0.5)}
                dx,dy=anchor_to_dis[anchor.lower()]
                dx=dx*self.imwidth+offsetx
                dy=dy*self.imheight+offsety
                cosa=math.cos(angle*math.pi/180)
                sina=math.sin(angle*math.pi/180)  
                ex=dx*cosa-dy*sina
                ey=dx*sina+dy*cosa
                imrwidth,imrheight=self._image.size

                self._image_x=qx+ex-imrwidth/2
                self._image_y=qy+ey-imrheight/2

            elif self.type=='text':
                textcolor=colorspec_to_tuple(self.textcolor(t))                 
                fontsize=self.fontsize(t)
                angle=self.angle(t)                        
                anchor=self.anchor(t)

                text=self.text(t)
                if self.screen_coordinates:
                    qx=x
                    qy=y
                else:
                    qx=(x-An.x0)*An.scale
                    qy=(y-An.y0)*An.scale
                    fontsize=fontsize*An.scale
                    offsetx=offsetx*An.scale
                    offsety=offsety*An.scale
                
                self._image_ident= (text,self.font,fontsize,angle,textcolor)
                if self._image_ident!=self._image_ident_prev:
                    font=getfont(self.font,fontsize)
                        
                    width,height=font.getsize(text)
                    im=Image.new('RGBA',(int(width),int(height)),(0,0,0,0))
                    imwidth,imheight=im.size
                    draw=ImageDraw.Draw(im)
                    draw.text(xy=(0,0),text=text,font=font,fill=textcolor)
                    #this code is to correct a bug in the rendering of text,
                    #leaving a kind of shadow around the text
                    textcolor3=textcolor[0:3]
                    if textcolor3!=(0,0,0): #black is ok
                        for y in range(imheight):
                            for x in range(imwidth):
                                c=im.getpixel((x,y))
                                if not c[0:3] in (textcolor3,(0,0,0)):
                                    im.putpixel((x,y),(*textcolor3,c[3]))  
                    #end of code to correct bug     
          
                    self.imwidth,self.imheight=im.size
                    
                    self._image = im.rotate(angle,expand=1)
                                    
                anchor_to_dis={
                  'ne':(-0.5,-0.5),
                  'n':(0,-0.5),
                  'nw':(0.5,-0.5),
                  'e':(-0.5,0),
                  'center':(0,0),
                  'w':(0.5,0),\
                  'se':(-0.5,0.5),
                  's':(0,0.5),
                  'sw':(0.5,0.5)}

                dx,dy=anchor_to_dis[anchor.lower()]
                dx=dx*self.imwidth+offsetx
                dy=dy*self.imheight+offsety
                cosa=math.cos(angle*math.pi/180)
                sina=math.sin(angle*math.pi/180)  
                ex=dx*cosa-dy*sina
                ey=dx*sina+dy*cosa
                imrwidth,imrheight=self._image.size        
                self._image_x=qx+ex-imrwidth/2
                self._image_y=qy+ey-imrheight/2
            else:
                self._image_visible=False #should never occur
                
        else:
            self._image_visible=False

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
            
    def __init__(self,parent=None,layer=0,keep=True,visible=True,
            screen_coordinates=False,
            t0=None,x0=0,y0=0,offsetx0=0,offsety0=0,
            circle0=None,line0=None,polygon0=None,rectangle0=None,
            image=None,text=None,
            font='',anchor='center',
            linewidth0=1,fillcolor0='black',linecolor0='black',textcolor0='black',
            angle0=0,fontsize0=20,width0=None,
            t1=None,x1=None,y1=None,offsetx1=None,offsety1=None,
            circle1=None,line1=None,polygon1=None,rectangle1=None,
            linewidth1=None,fillcolor1=None,linecolor1=None,textcolor1=None,
            angle1=None,fontsize1=None,width1=None,env=None):
                    
        self.env=default_env if env==None else env
        self._image_ident=None # denotes no image yet
        self._image=None
        self._image_x=0
        self._image_y=0
        self.canvas_object=None
        
        self.type=self.settype(circle0,line0,polygon0,rectangle0,image,text)
        if self.type=='':
            raise AssertionError('no object specified')
        type1=self.settype(circle1,line1,polygon1,rectangle1,None,None)
        if (type1!='') and (type1!=self.type):
            raise AssertionError('incompatible types: '+self.type+' and '+ type1)
            
        self.layer0=layer
        self.parent=parent
        self.keep=keep
        self.visible0=visible
        self.screen_coordinates=screen_coordinates
        self.sequence=self.env.serialize()

        self.circle0=circle0
        self.line0=line0
        self.polygon0=polygon0
        self.rectangle0=rectangle0            
        self.text0=text
        
        if image is None:
            self.width0=0 #just to be able to interpolate
        else:
            self.image0=spec_to_image(image)
            self.image_serial0=self.env.serialize()
            self.width0=self.image0.size[0] if width0 is None else width0
 
        self.font=font
        self.anchor0=anchor
        
        self.x0=x0
        self.y0=y0
        self.offsetx0=offsetx0
        self.offsety0=offsety0

        self.fillcolor0=fillcolor0
        self.linecolor0=linecolor0
        self.textcolor0=textcolor0        
        self.linewidth0=linewidth0
        self.angle0=angle0
        self.fontsize0=fontsize0

        self.t0=self.env._now if t0 is None else t0

        self.circle1=self.circle0 if circle1 is None else circle1
        self.line1=self.line0 if line1 is None else line1
        self.polygon1=self.polygon0 if polygon1 is None else polygon1
        self.rectangle1=self.rectangle0 if rectangle1 is None else rectangle1

        self.x1=self.x0 if x1 is None else x1
        self.y1=self.y0 if y1 is None else y1
        self.offsetx1=self.offsetx0 if offsetx1 is None else offsetx1
        self.offsety1=self.offsety0 if offsety1 is None else offsety1
        self.fillcolor1=\
          self.fillcolor0 if fillcolor1 is None else fillcolor1
        self.linecolor1=\
          self.linecolor0 if linecolor1 is None else linecolor1
        self.textcolor1=\
          self.textcolor0 if textcolor1 is None else textcolor1
        self.linewidth1=\
          self.linewidth0 if linewidth1 is None else linewidth1
        self.angle1=self.angle0 if angle1 is None else angle1
        self.fontsize1=\
          self.fontsize0 if fontsize1 is None else fontsize1
        self.width1=self.width0 if width1 is None else width1
        
        self.t1=inf if t1 is None else t1

        self.env.an_objects.append(self)

    def update(self,layer=None,keep=None,visible=None,
            t0=None,x0=None,y0=None,offsetx0=None,offsety0=None,
            circle0=None,line0=None,polygon0=None,rectangle0=None,
            image=None,text=None,font=None,anchor=None,
            linewidth0=None,fillcolor0=None,linecolor0=None,textcolor0=None,
            angle0=None,fontsize0=None,width0=None,
            t1=None,x1=None,y1=None,offsetx1=None,offsety1=None,
            circle1=None,line1=None,polygon1=None,rectangle1=None,
            linewidth1=None,fillcolor1=None,linecolor1=None,textcolor1=None,
            angle1=None,fontsize1=None,width1=None):
        '''
        updates an animation object
    
        Parameters
        ----------
        layer : int
            layer value |n|
            lower layer values are on top of higher layer values (default *)

        keep : bool
            keep |n|
            if False, animation object is hidden after t1, shown otherwise
            (default *)
                
        t0 : float
            time of start of the animation (default: now)
    
        x0 : float
            x-coordinate of the origin (default *) at time t0
    
        y0 : float
            y-coordinate of the origin (default *) at time t0
    
        offsetx0 : float
            offsets the x-coordinate of the object (default *) at time t0
    
        offsety0 : float
            offsets the y-coordinate of the object (default *) at time t0
    
        circle0 : tuple
            the circle at time t0 specified as a tuple (radius,) (default *)
    
        line0 : tuple
            the line(s) at time t0 (xa,ya,xb,yb,xc,yc, ...) (default *)
            
        polygon0 : tuple
            the polygon at time t0 (xa,ya,xb,yb,xc,yc, ...) |n|
            the last point will be auto connected to the start (default *)
    
        rectangle0 : tuple
            the rectangle at time t0 |n| 
            (xlowerleft,ylowerlef,xupperright,yupperright) (default *)
    
        image : str or PIL image
            the image to be displayed |n|
            This may be either a filename or a PIL image (default *)
    
        text : str
            the text to be displayed (default *)
    
        font : str or list/tuple
            font to be used for texts |n|
            Either a string or a list/tuple of fontnames. (default *)
            If not found, uses calibri or arial
            
        anchor : str
            anchor position |n|
            specifies where to put images or texts relative to the anchor
            point (default *) |n|
            possible values are (default: center): |n|
            ``nw    n    ne`` |n|
            ``w   center  e`` |n|
            ``sw    s    se``  
    
        linewidth0 : float
            linewidth of the contour at time t0 (default *)
            
        fillcolor0 : colorspec
            color of interior/text at time t0 (default *)
            
        linecolor0 : colorspec
            color of the contour at time t0 (default *)
            
        angle0 : float
            angle of the polygon at time t0 (in degrees) (default *)
            
        fontsize0 : float
            fontsize of text at time t0 (default *)
            
        width0 : float
            width of the image to be displayed at time t0 (default *)
        
        t1 : float
            time of end of the animation (default: inf) |n|
            if keep=True, the animation will continue (frozen) after t1
        
        x1 : float
            x-coordinate of the origin (default x0) at time t1
        
        y1 : float
            y-coordinate of the origin (default y0) at time t1
        
        offsetx1 : float
            offsets the x-coordinate of the object (default offsetx0) at time t1
        
        offsety1 : float
            offsets the y-coordinate of the object (default offsety0) at time t1
        
        circle1: tuple
             the circle at time t1 specified as a tuple (radius,)
        
        line1 : tuple
            the line(s) at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: line0) |n|
            should have the same length as line0
                
        polygon1 : tuple
            the polygon at time t1 (xa,ya,xb,yb,xc,yc, ...) (default: polygon0) |n|
            should have the same length as polygon0
        
        rectangle1 : tuple
            the rectangle at time t1 (default: rectangle0) |n| 
            (xlowerleft,ylowerlef,xupperright,yupperright)
        
        linewidth1 : float
            linewidth of the contour at time t1 (default linewidth0)
                
        fillcolor1 : colorspec
            color of interior/text at time t1 (default fillcolor0)
                
        linecolor1 : colorspec
            color of the contour at time t1 (default linecolor0)
                
        angle1 : float
            angle of the polygon at time t1 (in degrees) (default angle0)
                
        fontsize1 : float
            fontsize of text at time t1 (default: fontsize0)
                
        width1 : float
           width of the image to be displayed at time t1 (default: width0) |n|
           
            
        note that the type of the animation cannot be changed with this method.    
           
        default * means that the current value (at time now) is used
        ''' 

        t=self.An.env._now
        type0=self.settype(circle0,line0,polygon0,rectangle0,image,text)
        if (type0!='') and (type0!=self.type):
            raise AssertionError\
              ('incorrect type '+type0+' (should be '+self.type)
        type1=self.settype(circle1,line1,polygon1,rectangle1,None,None)
        if (type1!='') and (type1!=self.type):
            raise AssertionError\
              ('incompatible types: '+self.type+' and '+ type1)

        if layer!=None:
            self.layer0=layer
        if keep!=None:
            self.keep=keep
        if visible!=None:
            self.visible0=visible
        self.circle0=self.circle() if circle0 is None else circle0
        self.line0=self.line() if line0 is None else line0
        self.polygon0=self.polygon() if polygon0 is None else polygon0
        self.rectangle0=\
          self.rectangle() if rectangle0 is None else rectangle0
        if text!=None: self.text0=text
        self.width0=self.width() if width0 is None else width0
        if image!=None:
            self.image0=spec_to_image(image)
            self.image_serial0=self.env.serialize()
            self.width0=self.image0.size[0] if width0 is None else width0

        if font!=None: self.font=font
        if anchor!=None: self.anchor0=anchor
            
        self.x0=self.x(t) if x0 is None else x0
        self.y0=self.y(t) if y0 is None else y0
        self.offsetx0=self.offsetx(t) if offsetx0 is None else offsetx0
        self.offsety0=self.offsety(t) if offsety0 is None else offsety0

        self.fillcolor0=\
          self.fillcolor(t) if fillcolor0 is None else fillcolor0
        self.linecolor0=self.linecolor(t) if linecolor0 is None else linecolor0
        self.linewidth0=self.linewidth(t) if linewidth0 is None else\
          linewidth0
        self.textcolor0=\
          self.textcolor(t) if textcolor0 is None else textcolor0
        self.angle0=self.angle(t) if angle0 is None else angle0
        self.fontsize0=self.fontsize(t) if fontsize0 is None else fontsize0
        self.t0=self.An.env._now if t0 is None else t0

        self.circle1=self.circle0 if circle1 is None else circle1
        self.line1=self.line0 if line1 is None else line1
        self.polygon1=self.polygon0 if polygon1 is None else polygon1
        self.rectangle1=\
          self.rectangle0 if rectangle1 is None else rectangle1

        self.x1=self.x0 if x1 is None else x1
        self.y1=self.y0 if y1 is None else y1
        self.offsetx1=self.offsetx0 if offsetx1 is None else offsetx1
        self.offsety1=self.offsety0 if offsety1 is None else offsety1
        self.fillcolor1=\
          self.fillcolor0 if fillcolor1 is None else fillcolor1
        self.linecolor1=\
          self.linecolor0 if linecolor1 is None else linecolor1
        self.textcolor1=\
          self.textcolor0 if textcolor1 is None else textcolor1
        self.linewidth1=\
          self.linewidth0 if linewidth1 is None else linewidth1
        self.angle1=self.angle0 if angle1 is None else angle1
        self.fontsize1=\
          self.fontsize0 if fontsize1 is None else fontsize1
        self.width1=self.width0 if width1 is None else width1

        self.t1=inf if t1 is None else t1
        if self not in self.env.an_objects:
            self.env.an_objects.append(self)

    def remove(self):
        '''
        removes the animation object
        
        the animation object is removed from the animation queue,
        so effectively ending this animation
        
        note that it might be still updated, if required
        '''
        if self in self.env.an_objects:
            self.env.an_objects.remove(self)
            
    def x(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.x0,self.x1)

    def y(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.y0,self.y1)

    def offsetx(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.offsetx0,self.offsetx1)

    def offsety(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.offsety0,self.offsety1)

    def angle(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.angle0,self.angle1)

    def linewidth(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.linewidth0,self.linewidth1)

    def linecolor(self,t=None):
        return colorinterpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.linecolor0,self.linecolor1)

    def fillcolor(self,t=None):
        return colorinterpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.fillcolor0,self.fillcolor1)

    def circle(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.circle0,self.circle1)
          
    def textcolor(self,t=None):
        return colorinterpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.textcolor0,self.textcolor1)
          
    def line(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.line0,self.line1)

    def polygon(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.polygon0,self.polygon1)

    def rectangle(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.rectangle0,self.rectangle1)

    def width(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.width0,self.width1)

    def fontsize(self,t=None):
        return interpolate((self.An.env._now if t is None else t),\
          self.t0,self.t1,self.fontsize0,self.fontsize1)
    
    def text(self,t=None):
        return self.text0
        
    def anchor(self,t=None):
        return self.anchor0
        
    def layer(self,t=None):
        return self.layer0

    def visible(self,t=None):
        return self.visible0
        
    def image(self,t=None):
        '''
        returns image and a serial number at time t
        use the function spec_to_image to change the image here
        if there's a change in the image, a new serial numbder should be returned
        if there'n no change, do not update the serial number
        '''
        return self.image0,self.image_serial0

class AnimateButton(object):
    '''
    defines a button
    
    Parameters:
    -----------
    x : int
        x-coordinate of centre of the button in screen coordinates (default 0)
        
    y : int
        y-coordinate of centre of the button in screen coordinates (default 0)
        
    width : int
        width of button in screen coordinates (default 80)
        
    height : int
        height of button in screen coordinates (default 30)
        
    linewidth : int
        width of contour in screen coordinates (default 0=no contour)
        
    fillcolor : colorspec
        color of the interior (default 40%gray)  
        
    linecolor : colorspec
        color of contour (default black)
        
    color : colorspec
        color of the text (default white)
    
    text : str or function
        text of the button (default null string) |n|
        if text is an argumentless function, this will be called each time;
        the button is shown/updated
        
    font : str
        font of the text (default Helvetica)
        
    fontsize : int
        fontsize of the text (default 15)
        
    action :  function 
        action to take when button is pressed |n|
        executed when the button is pressed (default None)
        the function should have no arguments |n|
        
    On CPython platforms, the tkinter functionality is used, 
    on Pythonista, this is emulated by salabim
    '''
    def __init__(self,x=0,y=0,width=80,height=30,
                 linewidth=0,fillcolor='40%gray',
                 linecolor='black',color='white',text='',font='',
                 fontsize=15,action=None,env=None):
        
        self.env=default_env if env==None else env
        self.type='button'
        self.parent=None
        self.t0=-inf
        self.t1=inf
        self.x0=0
        self.y0=0
        self.x1=0
        self.y1=0
        self.sequence=self.env.serialize()
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
        self.text0=text
        self.lasttext='*'
        self.action=action
        
        self.env.ui_objects.append(self)
        self.installed=False

    def text(self):
        return self.text0
        
    def install(self):
        self.button = tkinter.Button\
          (An.root, text = self.lasttext, command = self.action,
          anchor = tkinter.CENTER)
        self.button.configure\
          (width = int(2.2*self.width/self.fontsize),\
          foreground=colorspec_to_hex(self.color,False),background =colorspec_to_hex(self.fillcolor,False), relief = tkinter.FLAT)
        self.button_window = An.canvas.create_window\
          (self.x+self.width, An.height-self.y-self.height,\
          anchor=tkinter.NE,window=self.button)            
        self.installed=True
    

    def remove(self):
        '''
        removes the button object
        
        the ui object is removed from the ui queue,
        so effectively ending this ui
        '''
        if self in self.env.ui_objects:
            self.env.ui_objects.remove(self)
        if not Pythonista:
            self.button.destroy()

class AnimateSlider(object):
    '''
    defines a slider
    
    Parameters:
    -----------
    x : int
        x-coordinate of centre of the slider in screen coordinates (default 0)
        
    y : int
        y-coordinate of centre of the slider in screen coordinates (default 0)
        
    vmin : float
        minimum value of the slider (default 0)
        
    vmax : float
        maximum value of the slider (default 0)
        
    v : float
        initial value of the slider (default 0) |n|
        should be between vmin and vmax
        
    resolution : float
        step size of value (default 1)
        
    width : float
        width of slider in screen coordinates (default 100)
        
    height : float
        height of slider in screen coordinates (default 20)
        
    linewidth : float
        width of contour in screen coordinate (default 0 = no contour)
        
    fillcolor : colorspec
        color of the interior (default 40%gray)  
        
    linecolor : colorspec
        color of contour (default black)
        
    labelcolor : colorspec
        color of the label (default black)
        
    label : str
        label if the slider (default null string) |n|
        if label is an argumentless function, this function
        will be used to display as label, otherwise the
        label plus the current value of the slider will be shown 
        
    font : str
         font of the text (default Helvetica)
         
    fontsize : int
         fontsize of the text (default 12)
         
    action ; function
         function executed when the slider value is changed (default None) |n|
         the function should one arguments, being the new value |n|
         if None (default), no action
      
    The current value of the slider is the v attibute of the slider. |n|
    On CPython platforms, the tkinter functionality is used, 
    on Pythonista, this is emulated by salabim
    '''
    def __init__(self,layer=0,x=0,y=0,width=100,height=20,
                 vmin=0,vmax=10,v=None,resolution=1,
                 linecolor='black',labelcolor='black',label='',
                 font='',fontsize=12,action=None,env=None):
        
        self.env=default_env if env==None else env
        n=round((vmax-vmin)/resolution)+1
        self.vmin=vmin
        self.vmax=vmin+(n-1)*resolution
        self._v=vmin if v is None else v
        self.xdelta=width/n
        self.resolution=resolution
        
        self.type='slider'
        self.parent=None
        self.t0=-inf
        self.t1=inf
        self.x0=0
        self.y0=0
        self.x1=0
        self.y1=0
        self.sequence=self.env.serialize()
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
        self.installed=False

        if Pythonista:
            self.y=self.y-height*1.5

        self.env.ui_objects.append(self)
    
    @property
    def v(self,value=None):
        '''
        returns and/or sets the value
        '''
        if Pythonista:
            return self._v
        else:
            if An.env == self.env:
                return self.slider.get()
            else:
                return self._v
    
    @v.setter
    def v(self,value):
        if Pythonista:
            self._v=value
        else:
            if self.An.env == self.env:
                self.slider.set(value)
            else:
                self._v=value
                
    def install(self):    
        self.slider=tkinter.Scale\
          (An.root, from_=self.vmin, to=self.vmax,\
          orient=tkinter.HORIZONTAL,label=self.label,resolution=self.resolution,command=self.action)
        self.slider.window = An.canvas.create_window\
          (self.x, An.height-self.y, anchor=tkinter.NW,\
          window=self.slider)
        self.slider.config\
          (font=(self.font,int(self.fontsize*0.8)),\
          background=\
          colorspec_to_hex(An.background_color,False),\
          highlightbackground=\
          colorspec_to_hex(An.background_color,False))
        self.slider.set(self._v)
        self.installed=True
        
    def remove(self):
        '''
        removes the slider object
        
        the ui object is removed from the ui queue,
        so effectively ending this ui
        '''
        if self in self.env.ui_objects:
            self.env.ui_objects.remove(self)
        if not Pythonista:
            self.slider.destroy()
            
class Component(object): 
    '''Component object
    
    A salabim component is used as a data component (primarily for queueing
    or as a component with a process) |n|
    Usually, a component will be defined as a subclass of Component.
    
    Parameters:
    -----------
    name : str
        name of the component. |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if omitted, the name will be derived from the class 
        it is defined in (lowercased)
        
    at : float
        schedule time |n|
        if omitted, now is used
        
    delay : float
        schedule with a delay |n|
        if omitted, no delay
        
    urgent : boolean 
        urgency indicator |n|
        if False (default), the component will be scheduled
        behind all other components scheduled
        for the same time |n|
        if True, the component will be scheduled 
        in front of all components scheduled
        for the same time
        
    mode : str preferred
        mode |n|
        will be used in trace and can be used in animations|n|
        if nothing specified, the mode will be None.|n|
        also mode_time will be set to now.
        
    auto_start : bool
        auto start indicator |n|
        if there is a generator call process defined in the
        component class, this will be activated 
        automatically, unless overridden with auto_start |n|
        if there is no generator called process, no activation 
        takes place, anyway
        
    env : Environment
        environment where the component is defined |n|
        if omitted, default_env will be used
    '''
    
    def __init__(self,name=None,at=None,delay=None,urgent=False,\
      auto_start=True,suppress_trace=False,mode=None,env=None): 
        if env is None:
            self.env=default_env
        else:
            self.env=env
        if name is None:
            name=str(type(self)).split('.')[-1].split("'")[0].lower()+'.'
        self._name,self._base_name,\
          self._sequence_number = _reformatname(name,self.env._nameserializeComponent)
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
        self.mode=mode #this also sets self._mode_time
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
        lines.append('  '+_modetxt(self._mode))
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
            self.env.print_trace('','',caller+' '+self._name,'(passivate)'+_modetxt(self._mode))
        else:                     
            self._push(scheduled_time,urgent)
            self._status=scheduled
            self.env.print_trace('','',self._name+' '+caller,\
              ('scheduled for %10.3f'%scheduled_time)+\
              _urgenttxt(urgent)+_atprocess(self._process)+' '+_modetxt(self._mode))       
           
    def reschedule(self,process=None,at=None,delay=None,urgent=False,mode='*'):
        '''
        reschedule component

        Parameters:
        -----------
        process : generator function
           process to be started. |n|
           if omitted, process will not be changed |n|
           note that the function *must* be a generator,
           i.e. contains at least one yield.
                     
        at : float
           schedule time |n|
           if omitted, now is used |n|
           if inf, this results in a passivate
           
        delay : float
           schedule with a delay |n|
           if omitted, no delay
           
        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time |n|
            if True, the component will be scheduled 
            in front of all components scheduled
            for the same time
                            
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations|n|
            if nothing specified, the mode will be unchanged.|n|
            also mode_time will be set to now, if mode is set.
            
        if to be applied for the current component, use yield reschedule.
        
        '''
        if mode!='*':
            self.mode=mode
  
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
                      
    def activate(self,process=None,at=None,delay=None,urgent=False,mode='*'):
        '''
        activate component

        Parameters:
        -----------
        process : generator function
           process to be started. |n|
           if omitted, the function called process will be used |n|
           note that the function *must* be a generator,
           i.e. contains at least one yield.
                     
        at : float
           schedule time |n|
           if omitted, now is used |n|
           if inf, an error will be raised
           
        delay : float
           schedule with a delay |n|
           if omitted, no delay
           
        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time |n|
            if True, the component will be scheduled 
            in front of all components scheduled
            for the same time
            
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations|n|
            if nothing specified, the mode will be unchanged.|n|
            also mode_time will be set to now, if mode is set. 
                                                   
        if to be applied for the current component, use ``yield activate``.
        '''
        if mode!='*':
            self.mode=mode

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
                    
    def reactivate(self,at=None,delay=None,urgent=False,mode='*'):
        '''
        reactivate component

        Parameters:
        -----------
        at : float
           schedule time |n|
           if omitted, now is used |n|
           if inf, an error will be raised
           
        delay : float
           schedule with a delay |n|
           if omitted, no delay
           
        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time |n|
            if True, the component will be scheduled 
            in front of all components scheduled
            for the same time
         
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations|n|
            if nothing specified, the mode will be unchanged.|n|
            also mode_time will be set to now, if mode is set.
            
        if to be applied for the current component, use ``yield reactivate``.
        '''
        self._checknotcurrent()
        self._checkispassive()                 

        if mode!='*':
            self.mode=mode

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
                        
    def hold(self,duration=None,till=None,urgent=False,mode='*'):
        '''
        hold the current component

        Parameters:
        -----------
        at : float
           schedule time |n|
           if omitted, now is used |n|
           if inf, an error will be raised
           
        delay : float
           schedule with a delay |n|
           if omitted, no delay
           
        urgent : bool
            urgency indicator |n|
            if False (default), the component will be scheduled
            behind all other components scheduled
            for the same time |n|
            if True, the component will be scheduled 
            in front of all components scheduled
            for the same time

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations|n|
            if nothing specified, the mode will be unchanged.|n|
            also mode_time will be set to now, if mode is set.
            
        *always* use as ``yield self.hold(...)``
        '''

        self._checkcurrent()       
        if mode!='*':
            self.mode=mode
        
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
        
    def passivate(self,mode='*'):
        '''
        passivate the current component

        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations|n|
            if nothing specified, the mode will be unchanged.|n|
            also mode_time will be set to now, if mode is set.
            
        *always* use as ``yield self.passivate()``
        '''
        self._checkcurrent()          
        self.env.print_trace('','','passivate',_modetxt(self._mode))
        self._scheduled_time=inf
        if mode!='*':
            self.mode=mode
        self._status=passive
                        
    def cancel(self,mode='*'):
        '''
        cancel component (makes the component data)
          
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations|n|
            if nothing specified, the mode will be unchanged.|n|
            also mode_time will be set to now, if mode is set.
            
        if to be applied for the current component, use ``yield self.cancel()``
        '''
        self.env.print_trace('','','cancel '+self._name+' '+_modetxt(self._mode))
           
        _check_fail(self)
        self._process=None
        if self._scheduled_time!=inf:
            self._remove()
        self._scheduled_time=inf
        if mode!='*':
            self.mode=mode
        self._status=data
      
    def standby(self,mode='*'):
        '''
        puts the current container in standby mode
        
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations|n|
            if nothing specified, the mode will be unchanged.|n|
            also mode_time will be set to now, if mode is set.
            
        *always* use as ``yield self.standby()``        
        '''
        if self!=self.env._current_component:
            raise AssertionError(self._name+' is not current')            
        self.env.print_trace('','','standby',_modetxt(self._mode))
        self._scheduled_time=self.env._now
        self.env._standbylist.append(self)
        if mode!='*':
            self.mode=mode
        self._status=standby
         
    def stop_run(self):
        '''
        stops the simulation and gives control to the main program, as the next event
        '''
        scheduled_time=self.env._now
        self.env.print_trace('','','stop_run',\
          'scheduled for=%10.3f'%scheduled_time)

        if self.env._main._scheduled_time!=inf: # just to be sure
            self.env._main._remove()
        self.env._main._scheduled_time=scheduled_time
        self.env._main._push(scheduled_time,urgent=True)
        self.env._main._status=scheduled

    def request(self,*args,priority=None,greedy=False,fail_at=None,mode='*'):
        '''
        request from a resource or resources 
        
        Parameters:
        ----------
        args : sequence
            a sequence of requested resources |n|
            each resource can be optionally followed by a
            quantity and a priority |n| 
            if the quantity is not specified, 1 is assumed |n|
            if the priority is not specified, this request 
            for the resources be added to the tail of
            the requesters queue |n|
            alternatively, the request for a resource may
            be specified as a list or tuple containing
            the resource name, the quantity and the 
            priority |n|
            examples |n|
            yield self.request(r1) |n|
            --> requests 1 from r1 |n|
            yield self.request(r1,r2) |n|
            --> requests 1 from r1 and 1 from r2 |n|
            yield self.request(r1,r2,2,r3,3,100) |n|
            --> requests 1 from r1, 2 from r2 and 3 from r3 with priority 100 |n|
            yield self.request((r1,1),(r2,2)) |n|
            --> requests 1 from r1, 2 from r2 |n|
                        
        greedy : bool
            greedy indicator |n|
            if False (default), the request will be honoured
            at once when all requested quantities of the
            resources are available |n|
            if True, the components puts a pending claim
            already when sufficient capacity is available. |n|
            When the requests cannot be honoured finally,
            all pending requests will be released.
            
        fail_at : float
            time out |n|
            if the request is not honoured before fail_at,
            the request will be cancelled and the
            parameter request_failed will be set. |n|
            if not specified, the request will not time out. 
                          
        it is not allowed to claim a resource more than once by the same component |n|
        the requested quantity may exceed the current capacity of a resource |n|
        the parameter request_failed will be reset by calling request
            
        mode : str preferred
            mode |n|
            will be used in trace and can be used in animations|n|
            if nothing specified, the mode will be unchanged.|n|
            also mode_time will be set to now, if mode is set.
            
        always use as ``yield self.request(...)``
        '''
        
        if fail_at is None:
            scheduled_time=inf
        else:
            scheduled_time=fail_at

        self._checkcurrent()
        self._greedy=greedy

        self._request_failed=False
        i=0
        if mode!='*':
            self.mode=mode
        while i<len(args):
            q=1
            priority=None
            argsi=args[i]
            if isinstance(argsi,Resource):
                r=argsi
                if i+1<len(args):
                    if not isinstance(args[i+1],(Resource,list,tuple)):
                        i+=1
                        q=args[i]
                if i+1<len(args):
                    if not isinstance(args[i+1],(Resource,list,tuple)):
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
              'request for '+str(q)+' from '+r._name+addstring+' '+_modetxt(self._mode))

            i+=1
            
        for r in list(self._requests):
            r._claimtry()
            break # no need to check for other resources
            
        if len(self._requests)!=0: 
            self._status=scheduled            
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
            self._leave(r._claimers)
            if r._claimers._length==0:
                r._claimed_quantity=0 #to avoid rounding problems
            del self._claims[r]
        self.env.print_trace('','',self._name,\
          'release '+str(q)+' from '+r._name)
        r._claimtry()    
            
    def release(self,*args):
        '''
        releases a quantity from a resource or resources
        
        Parameters:
        -----------
        args : sequence
            a sequence of requested resources to be released |n|
            each resource can be optionally followed by a
            quantity |n|
            if the quantity is not specified, the current
            claimed quantity will be released |n|
            alternatively, the release for a resource may
            be specified as a list or tuple containing
            the resource name and (optionally) a quantity
            examples |n|
            suppose c1 claims currently 1 from r1 and 2 from r2 and 3 from r3
            c1.release |n|
            --> releases 1 from r1, 2 from r2 and 3 from r3 |n|
            c1.release(r2) |n|
            --> releases 2 from r2 |n|
            c1.release((r2,2),(r3,2)) |n|
            --> releases 2 from r2,and 2 from r3
        '''
        
        if len(args)==0:
            for r in list(self._claims.keys()):
                self._release(r,None)                
                
        else:
            i=0
            while i<len(args):
                q=None
                argsi=args[i]
                if isinstance(argsi,Resource):
                    r=argsi
            
                    if i+1<len(args):
                        if not isinstance(args[i+1],(Resource,list,tuple)):
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
        
        Parameters:
        -----------
            resource : Resoure
                resource to be queried
        
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
        return self._claims.keys()

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
        
        Parameters:
        -----------
        txt : str
            name of the component |n|
            if txt ends with a period, the name will be serialized |n|
            if omitted, the name will not be changed
        '''
        return self._name
        
    @name.setter
    def name(self,txt):
        self._name,self._base_name,\
          self._sequence_number=_reformatnameC(txt,self.env._nameserializeComponent)
        
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

        normally this will be the integer value of a serialized name
        '''
        return self._sequence_number
        
        
    @property
    def suppress_trace(self):
        return self._suppress_trace
        
    @suppress_trace.setter
    def suppress_trace(self,value):
        self._suppress_trace=value

    @property
    def mode(self):
        '''
        returns/sets the mode of the component
        '''
        return self._mode
        
    @mode.setter
    def mode(self,mode):
        self._mode_time=self.env._now
        self._mode=mode        
        
    @property
    def ispassive(self):
        '''
        returns True if status is passive, False otherwise
        '''
        return self.status==passive
        
    @property
    def iscurrent(self):
        '''
        returns True if status is current, False otherwise
        '''
        return self.status==current
        
    @property
    def isscheduled(self):
        '''
        returns True if status is scheduled, False otherwise
        '''
        return self.status==scheduled
        
    @property
    def isstandby(self):
        '''
        returns True if status is standby, False otherwise
        '''
        return self.status==standby   
        
    @property
    def isdata(self):
        '''
        returns True if status is data, False otherwise
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

      
    def index_in_queue(self,q):
        '''
        get index of component in a queue
        
        Parameters:
        -----------
        q : Queue
            queue to be queried
            
        Returns the index of component in q, if component belongs to q |n|
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
        
        Parameters:
        -----------
        q : Queue
            queue to enter
            
        the priority will be set to
        the priority of the tail component of the queue, if any
        or 0 if queue is empty
        '''
        self._checknotinqueue(q)
        priority=q._tail.predecessor.priority
        Qmember().insert_in_front_of(q._tail,self,q,priority)

    def enter_at_head(self,q):
        '''
        enters a queue at the head
        
        Parameters:
        -----------
        q : Queue
            queue to enter
            
        the priority will be set to
        the priority of the head component of the queue, if any
        or 0 if queue is empty
        '''
        
        self._checknotinqueue(q)
        priority=q._head.successor.priority
        Qmember().insert_in_front_of(q._head.successor,self,q,priority)
                   
    def enter_in_front_of(self,q,poscomponent):
        '''
        enters a queue in front of a component
        
        Parameters:
        -----------
        q : Queue
            queue to enter
            
        poscomponent : Component
            component to be entered in front of
                        
        the priority will be set to the priority of poscomponent
        '''
        
        self._checknotinqueue(q)
        m2=poscomponent._checkinqueue(q)
        priority=m2.priority
        Qmember().insert_in_front_of(m2,self,q,priority)

    def enter_behind(self,q,poscomponent):
        '''
        enters a queue behind a component
        
        Parameters:
        -----------
        q : Queue
            queue to enter
            
        poscomponent : Component
            component to be entered behind
                        
        the priority will be set to the priority of poscomponent
        '''
        
        self._checknotinqueue(q)
        m1=poscomponent._checkinqueue(q)
        priority=m1.priority
        Qmember().insert_in_front_of(m1.successor,self,q,priority)
        
    def enter_sorted(self,q,priority):
        '''
        enters a queue, according to the priority
        
        
        Parameters:
        -----------
        q : Queue
            queue to enter
            
        priority: float
            priority in the queue
            
        The component is placed just before the first component with a priority > given priority 
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
        
        Parameters:
        -----------
        q : Queue
            queue to leave
            
        statistics are updated accordingly
        '''

        mx=self._checkinqueue(q)
        m1=mx.predecessor
        m2=mx.successor
        m1.successor=m2
        m2.predecessor=m1
        mx.component=None
          # signal for components method that member is not in the queue
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
        
        Parameters:
        -----------
        q : Queue
            queue where the component belongs to
        '''
        
        mx=self._checkinqueue(q)
        return mx.priority


    def set_priority(self,q,priority):
        '''
        sets the priority of a component in a queue
        
        Parameters:
        -----------
        q : Queue
            queue where the component belongs to
        
        priority : float
            priority in queue

        the order of the queue may be changed
        '''
        
        mx=self._checkinqueue(q)
        if priority!=mx.priority:
            # leave.sort is not possible, because statistics will be affected

            mx.predecessor.successor=mx.successor
            mx.successor.predecessor=mx.predecessor
            
            m2=q._head.successor
            while (m2!=q._tail) and (m2.priority<=priority):
                m2=m2.successor
    
            m1=m2.predecessor
            m1.successor=mx
            m2.predecessor=mx
            mx.predecessor=m1
            mx.successor=m2
            mx.priority=priority
            for iter in q._iter_touched:
                q._iter_touched[iter]=True
            if q._resource!=None:
               q._resource._claimtry()
        
    def successor(self,q):
        '''
        successor of component in a queue
        
        Parameters:
        -----------
        q : Queue
            queue where the component belongs to
            
        returns the successor of the component in the queue
        if component is not at the tail. |n|
        returns None if component is at the tail.
        ''' 
        
        mx=self._checkinqueue(q)
        return mx.successor.component

    def predecessor(self,q):
        '''
        predecessor of component in a queue
        
        Parameters:
        -----------
        q : Queue
            queue where the component belongs to
            
        returns the predecessor of the component in the queue
        if component is not at the head. |n|
        returns None if component is at the head.
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
        '''
        
        return self._creation_time
        
    @property
    def scheduled_time(self):
        '''
        returns the time the component is scheduled for

        returns the time the component scheduled for, if it is scheduled |n|
        returns inf otherwise
        '''
        return self._scheduled_time
        
    @property
    def mode_time(self):
        '''
        returns the time the component got it's latest mode |n|
        For a new component this is
        the time the component was created. |n|
        this function is particularly useful for animations.
        '''
        return self._mode_time
        
    @property
    def status(self):
        '''
        returns the status of a component
        
        possible values are
        - data
        - passive
        - scheduled
        - current
        - standby
        '''
        
        return self._status
        
  
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
    
    Parameters:
    -----------
    mean :float
        mean of the distribtion |n|
        must be >0
       
    randomstream: randomstream
        randomstream to be used |n|
        if omitted, random will be used |n|
        if used as random.Random(12299)
        it assigns a new stream with the specified seed
    '''
    
    def __init__(self,mean,randomstream=None):
        if mean<=0:
            raise AsserionError('mean<=0')
        self._mean=mean
        if randomstream is None:
            self.randomstream=random
        else:
            assert isinstance(randomstream,random.Random)
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
                            if used as random.Random(12299)
                              it assigns a new stream with the specified seed
    '''
    def __init__(self,mean,standard_deviation,randomstream=None):
        if standard_deviation<0:
            raise AsserionError('standard_deviation<0')
        self._mean=mean
        self._standard_deviation=standard_deviation
        if randomstream is None:
            self.randomstream=random
        else:
            assert isinstance(randomstream,random.Random)
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
        return self.randomstream.normalvariate\
          (self._mean,self._standard_deviation)

class Uniform(_Distribution):
    '''
    uniform distribution
    
    Uniform(lowerbound,upperboud,seed)
    
    arguments:
        lowerbound          lowerbound of the distribution
        upperbound          upperbound of the distribution
        randomstream        randomstream
                            if omitted, random will be used
                            if used as random.Random(12299)
                              it assigns a new stream with the specified seed

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
            assert isinstance(randomstream,random.Random)
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
                            if used as random.Random(12299)
                            it assigns a new stream with the specified seed
                            
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
        self.mode=mode
        if randomstream is None:
            self.randomstream=random
        else:
            assert isinstance(randomstream,random.Random)
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
                            if used as random.Random(12299)
                              it assigns a new stream with the specified seed
    '''
    def __init__(self,value,randomstream=None):
        self._value=value
        if randomstream is None:
            self.randomstream=random
        else:
            assert isinstance(randomstream,random.Random)
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
                            if used as random.Random(12299)
                              it assigns a new stream with the specified seed
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
            assert isinstance(randomstream,random.Random)
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
                raise AssertionError\
                  ('x value %s is smaller than previous value %s'%(x,lastx))
            cum=spec.pop(0)
            if cum<lastcum:
                raise AssertionError\
                  ('cumulative value %s is smaller than previous value %s'%\
                  (cum,lastcum))
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
            self._mean+=\
              ((self._x[i]+self._x[i+1])/2)*(self._cum[i+1]-self._cum[i])

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
                return interpolate\
                  (r,self._cum[i-1],self._cum[i],self._x[i-1],self._x[i])
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
                            if used as random.Random(12299)
                              it assigns a new stream with the specified seed
    requirements:
        p1+p2=...+pn>0
        all densities are auto scaled according to the sum of p1 to pn,
        so no need to have p1 to pn add up to 1 or 100.
    '''
    def __init__(self,spec1,spec2=None,randomstream=None):
        self._x=[0] # just a place holder
        self._cum=[0] 
        if randomstream is None:
            self.randomstream=random
        else:
            assert isinstance(randomstream,random.Random)
            self.randomstream=randomstream

        sump=0
        sumxp=0
        lastx=-inf
        hasmean=True
        if spec2==None:
            spec=list(spec1)
            if len(spec)==0:
                raise AssertionError('no arguments specified')
            while len(spec)>0:
                x=spec.pop(0)
                if len(spec)==0:
                    raise AssertionError('uneven number of parameters specified')
                p=spec.pop(0)
                sump+=p
                try:
                    sumxp += float(x)*p
                except:
                    hasmean=False
                self._x.append(x)
                self._cum.append(sump)
        else:
            spec=list(spec1)
            if isinstance(spec2,(list,tuple)):
                spec2=list(spec2)
            else:
                spec2=len(spec)*[spec2]
            while len(spec)>0:
                x=spec.pop(0)
                p=spec2.pop(0)
                sump+=p
                try:
                    sumxp += float(x)*p
                except:
                    hasmean=False
                self._x.append(x)
                self._cum.append(sump)            
        if sump==0:
            raise AssertionError('at least one probability should be >0')

        for i in range (len(self._cum)):
            self._cum[i]=self._cum[i]/sump
        if hasmean:
            self._mean=sumxp/sump            
        else:
            self._mean=inf

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
                            if used as random.Random(12299)
                              it assigns a new stream with the specified seed
                            note that the rendomstream in the string is ignored
    requirements:
        spec must evakuate to a proper salabim distribution (including proper casing).
    '''

    def __init__(self,spec,randomstream=None):
        d=eval(spec)
        if randomstream is None:
            self.randomstream=random
        else:
            assert isinstance(randomstream,random.Random)
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
    '''
    Resource
    
    Parameters:
    -----------
    name : str
        name of the resource |n|
        if the name ends with a period (.),
        auto serializing will be applied |n|
        if omitted, the name resource will be used
        
    capacity : float
        capacity of the resouce |n|
        if omitted, 0
        
    strict_order : bool
        strict_order specifier |n|
        if False, requests can be honoured for components that requested 
        from the resource later |n|
        if True, requests can only honoured in the order of the claim request.
        note that this may lead to deadlock when components request from more
        than one resource, in strict order.
        
    anonymous : bool
        anonymous specifier |n|
        if True, claims are not related to any component. This is useful
        if the resource is actually just a level. |n|
        if False, claims belong to a component.
        
    env : Environment
        environment to be used |n|
        if omitted, default_env is used
    '''
    
    def __init__(self,name=None,capacity=1,strict_order=False,\
      anonymous=False,env=None):
        '''
        
        '''
        
        if (env is None):
            self.env=default_env
        else:
            self.env=env
        if name is None:
            name='resource.'            
        self._capacity=capacity
        self._name,self._base_name,self._sequence_number = \
          _reformatname(name,self.env._nameserializeResource)
        self._requesters=Queue(name='requesters:'+name,env=self.env)
        self._requesters._resource=self
        self._claimers=Queue(name='claimers:'+name,env=self.env)
        self._pendingclaimed_quantity=0
        self._claimed_quantity=0
        self.anonymous=anonymous
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
            mx=self._requesters._head.successor
            while mx!=self._requesters._tail:
                c=mx.component
                mx=mx.successor
                if self in c._pendingclaims:
                    lines.append('    '+pad(c._name,20)+\
                      ' quantity='+str(c._requests[self])+\
                      ' provisionally claimed')
                else:
                    lines.append('    '+pad(c._name,20)+\
                      ' quantity='+str(c._requests[self]))
        
        lines.append('  claimed_quantity='+str(self._claimed_quantity))
        if self._claimed_quantity>=0:
            if self.anonymous:
                lines.append('  not claimed by any components,'+\
                ' because the resource is anonymous')
            else:
                lines.append('  claimed by:')
                mx=self._claimers._head.successor
                while mx!=self._claimers._tail:
                    c=mx.component
                    mx=mx.successor
                    lines.append('    '+pad(c._name,20)+\
                      ' quantity='+str(c._claims[self]))
                 
        return '\n'.join(lines)

    def _claimtry(self):
        mx=self._requesters._head.successor
        while mx!=self._requesters._tail:
            c=mx.component
            mx=mx.successor
            if c._greedy:
                if self not in c._pendingclaims:
                    if c._requests[self]<=\
                      self._capacity-self._claimed_quantity-\
                      self._pendingclaimed_quantity+1e-8:
                        c._pendingclaims.append(self)
                        self._pendingclaimed_quantity+=c._requests[self] 
            claimed=True
            for r in c._requests:
                if r not in c._pendingclaims:
                    if c._requests[r]>r._capacity-r._claimed_quantity-\
                      r._pendingclaimed_quantity+1e-8:
                        claimed=False
                        break
            if claimed:
                for r in list(c._requests):

                    r._claimed_quantity+=c._requests[r]
                    if r in c._pendingclaims:
                        r._pendingclaimed_quantity-=c._requests[r]
                        
                    if not r.anonymous:
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
        
        Parameters:
        -----------
        quantity : float
            quantity to be released |n|
            if not specified, the resource will be emptied completely |n|
            for non-anonymous resources, all components claiming from this resource
            will be released.
                              
        quantity may not be specified for a non-anomymous resoure
        '''
        if self.anonymous:
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
                raise AssertionError\
                  ('no quantity allowed for non-anonymous resource')
                
            mx=self._claimers._head.successor
            while mx!=self._tail:
                c=mx.component
                mx=mx.successor
                c.release(self)
                
    @property
    def requesters(self):
        '''
        returns the queue containing all components with not yet honoured requests.
        '''
        return self._requesters
        
    @property
    def claimers(self):
        '''
        returns the queue with all components claiming from the resource. |n|
        will be an empty queue for an anonymous resource
        '''
        return self._claimers

    @property
    def capacity(self,cap=None):
        '''
        gets or sets the capacity of a resource.
        
        this may lead to honouring one or more requests.
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
        gets or sets the strict_order property of a resource
        
        this may lead to honouring one or more requests.        
        '''
        return self._strict_order
        
    @strict_order.setter
    def strict_order(self,strict_order):
        self._strict_order=strict_order
        self._claimtry()

    @property
    def name(self):
        '''
        gets or sets the name of a resource
        
        Parameters:
        ----------
        txt : str
            name of the resource |n|
            if txt ends with a period, the name will be serialized
        '''
        return self._name

    @name.setter
    def name(self,txt):
        self._name,self._base_name,self._sequence_number=\
          _reformatname(txt,self.env._nameserializeResource)
        
    @property
    def base_name(self):
        '''
        returns the base name of a resource (the name used at init or name)
        '''
        return self._base_name        

    @property
    def sequence_number(self):
        '''
        returns the sequence_number of a resource
        (the sequence number at init or name)

        normally this will be the integer value of a serialized name,
        but also non serialized names (without a dot at the end)
        will be numbered)
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
    if isinstance(colorspec,(tuple,list)):
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
                return (int(colorspec[1:3],16),int(colorspec[3:5],16),\
                  int(colorspec[5:7],16))
            elif len(colorspec)==9:
                return (int(colorspec[1:3],16),int(colorspec[3:5],16),\
                  int(colorspec[5:7],16),int(colorspec[7:9],16))
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
        return int(v[:2],16), int(v[2:4],16), int(v[4:6],16), int(v[6:8],16)
    raise AssertionError('Incorrect value'+str(v))

def colorspec_to_hex(colorspec,withalpha=True):
    v=colorspec_to_tuple(colorspec)
    if withalpha:
        return '#%02x%02x%02x%02x' % (int(v[0]),int(v[1]),int(v[2]),int(v[3]))
    else:
        return '#%02x%02x%02x' % (int(v[0]),int(v[1]),int(v[2]))

def spec_to_image(image):
    if isinstance(image,str):
        im = Image.open(image)
        im = im.convert('RGBA')
        return im
    else:
        return image

def getfont(fontname,fontsize): # fontsize in screen_coordinates!
    if isinstance(fontname,list):
        fonts=tuple(fontname)
    elif isinstance(fontname,str):
        fonts=(fontname,)
    else:
        fonts=fontname

    if (fonts,fontsize) in An.font_cache:
        font=An.font_cache[(fonts,fontsize)]
    else:
        font=None
        for ifont in fonts+('calibri', 'Calibri','arial','Arial'):
            try:
                font=ImageFont.truetype(font=ifont,size=int(fontsize))
                break
            except:
                pass
        if font==None:
            raise AssertionError('no matching fonts found for ',fonts)
        An.font_cache[(fonts,fontsize)]=font
    return font
        
def getwidth(text,font='',fontsize=20,screen_coordinates=False):
    if not screen_coordinates:
        fontsize=fontsize*An.scale
    f=getfont(font,fontsize)
    thiswidth,thisheight=f.getsize(text)
    if screen_coordinates:
        return thiswidth
    else:
        return thiswidth/An.scale
    return 

def getfontsize_to_fit(text,width,font='',screen_coordinates=False):
    if not screen_coordinates:
        width=width*An.scale

    lastwidth=0    
    for fontsize in range(1,300):
        f=getfont(font,fontsize)
        thiswidth,thisheight=f.getsize(text)
        if thiswidth>width:
            break
        lastwidth=thiswidth
    fontsize=interpolate(width,lastwidth,thiswidth,fontsize-1,fontsize)
    if screen_coordinates:
         return fontsize
    else:
         return fontsize/An.scale

def _i(p,v0,v1):
    if v0==v1:
        v=v0 # avoid rounding problems
    v=(1-p)*v0+p*v1
    return v

def colorinterpolate(t,t0,t1,v0,v1):
    vt0=colorspec_to_tuple(v0)
    vt1=colorspec_to_tuple(v1)
    return tuple(int(c) for c in interpolate(t,t0,t1,vt0,vt1))
    
def interpolate(t,t0,t1,v0,v1):
    if (v0 is None) or (v1 is None):
        return None
    if t0==t1:
        return v1
    if t0>t1:
        (t0,t1)=(t1,t0)
        (v0,v1)=(v1,v0)
    if t<=t0:
        return v0
    if t>=t1:
        return v1
    if t1==inf:
        return v0
    p=(0.0+t-t0)/(t1-t0)
    if isinstance(v0,(list,tuple)):
        l=[]
        for x0,x1 in zip(v0,v1):
            l.append(_i(p,x0,x1))
        return tuple(l)
    else:
        return _i(p,v0,v1)

            
def clocktext(t):
    s=''
    if (not An.paused) or (int(time.time()*2)%2==0):

        if (not An.paused) and An.env.show_fps:  
            if len(An.frametimes)>=2:
                fps=(len(An.frametimes)-1)/(An.frametimes[-1]-An.frametimes[0])
            else:
                fps=0
            s=s+'fps={:.1f}'.format(fps)
        if An.env.show_speed:
            if s!='':
                s=s+' '
            s=s+'*{:.3f}'.format(An.env.speed)
        if An.env.show_time:
            if s!='':
                s=s+' '
            s=s+'t={:.3f}'.format(t)
    return s

def pausetext():
    if An.paused:
        return 'Resume'  
    else:
        return 'Pause'  
        
def tracetext():
    if An.env._trace:
        return 'Trace off'
    else:
        return 'Trace on'
            
def _reformatname(name,_nameserialize):
    L=20
    if name in _nameserialize:
        next=_nameserialize[name]+1
    else: 
        next=0
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
        
def _modetxt(mode):
    if mode==None:
        return ''
    else:
        return 'mode='+str(mode)       
    
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
default_env=Environment(trace=False,name='default environment')
main=default_env._main
random=random.Random(-1)
   
if __name__ == '__main__':
    try:
        import salabim_test
    except:
        print ('salabim_test.py not found')
    else:
        salabim_test.test17()
