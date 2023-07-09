# coding: utf-8

# ### Lock animated

# This is a simulation of a ship lock, similar to the ones we can see in the Panama Canal or in some North European ports.
# The lock has two doors (left and right) which can open when the level of water is the same at both sides of the door.
# The picture below shows a particular moment of the simulation where we can observe the different components of the system.
# Ships are queueing at both sides of the lock: those coming from the left side(lship.number) are presented in blue colour while those coming from the right side(rship.number) are presented in red colour. In the picture below, lship.6 and lship.7 are queueing on the left, while rship.12, rship.13 and rship.14 are waiting on the right side. Both doors of the lock are closed because the water level inside the lock is switching from low level to high level, carrying two ships.

# ![image.png](attachment:image.png)

# In[1]:


import salabim as sim

left = -1  # Lock on the left side, actually meaning that the lock is open on the left (left door is open).
right = +1  # Lock on the right side, actually meaning that the lock is open on the right (right door is open).


# In[2]:


# We name the lock sides as 'l' for left and 'r' right
def sidename(side):
    return "l" if side == left else "r"


# Ships coming from the left are blue and those coming from the right are red
def shipcolor(side):
    return "blue" if side == left else "red"


# We create a polygon to represent a ship, this polygon has four coordinates (x, y).
# The polygon has a lenght according to the ship length and 3 units in height.
# This will be used later by the Class Ship to create an animation object.
def ship_polygon(ship):
    return (ship.side * (ship.length - 2), 0, ship.side * 3, 0, ship.side * 2, 3, ship.side * (ship.length - 2), 3)


# In[3]:


# We define a rectangle representing the water inside the lock.
# If the lock is in mode 'Switch' the water level will be moving between the two lock levels (low and high).
def lock_water_rectangle(t):
    if lock.mode() == "Switch":
        y = sim.interpolate(t, lock.mode_time(), lock.scheduled_time(), ylevel[lock.side], ylevel[-lock.side])
    # Interpolate is a method of Salabim that provides linear interpolation: (t, t0, t1, f(t0), f(t1))
    # mode_time() is a method of sim.Component that returns the time the component got its latest mode
    # schedule_time() is a method of Component that returns the time the component is scheduled for
    else:
        y = ylevel[lock.side]
        # When not switching, the water level will be one of the door levels
    return (xdoor[left], -waterdepth, xdoor[right], y)
    # Returns the two coordinates (x,y) defining the rectangle


# We define a rectangle representing the left door
def lock_door_left_rectangle(t):
    if lock.mode() == "Switch" or lock.side == right:
        # The left door will be closed when the lock is switching water level or when the right door is open.
        # The height of the door is 2 units above the water level
        y = ylevel[right] + 2  # y = lockheight + 2 = 7
    else:
        y = ylevel[left] - waterdepth  # 0 - waterdepth = -2
    return (xdoor[left] - 1, -waterdepth, xdoor[left] + 1, y)
    # Returns the two coordinates defining the rectangle


# We define a rectangle representing the right door; the logic is similar to the one used for the left door.
def lock_door_right_rectangle(t):
    if lock.mode() == "Switch" or lock.side == left:
        y = ylevel[right] + 2  # y = lockheight + 2 = 7
    else:
        y = ylevel[right] - waterdepth  # Lockheight - waterdepth = 5 - 2 = 3
    return (xdoor[right] - 1, -waterdepth, xdoor[right] + 1, y)


# The following sketch can help in understanding the variables used in the animation:

# ![image.png](attachment:image.png)

# In[4]:


def do_animation():
    global ylevel, xdoor, waterdepth

    lockheight = 5  # Maximum height of the water inside the lock
    waterdepth = 2  # Minimum level of water
    ylevel = {left: 0, right: lockheight}  # Dictionary, defining the (fixed) water level at both sides of the lock
    xdoor = {left: -0.5 * locklength, right: 0.5 * locklength}  # x-coordinate of the doors
    xbound = {left: -1.2 * locklength, right: 1.2 * locklength}  # x-coordinate of the limits of the screen

    # animation_parameters is a method of salabim.Environment to set animation parameters and to start the animation
    env.animation_parameters(animate=True, x0=xbound[left], y0=-waterdepth, x1=xbound[right], modelname="Lock", speed=8, background_color="20%gray")

    for side in [left, right]:
        sim.AnimateQueue(queue=wait[side], x=xdoor[side], y=10 + ylevel[side], direction="n")
        # AnimateQueue is a class of Salabim to animate the component in a queue
        # wait[left] and wait[right] are ship queues at both sides of the lock

    # AnimateRectangle is a class of Salabim to display a rectangle, optinally with a text
    # The first rectangle represents the water at the left side of the lock (fixed level)
    sim.AnimateRectangle(spec=(xbound[left], ylevel[left] - waterdepth, xdoor[left], ylevel[left]), fillcolor="aqua")
    # The second rectangle represents the water at the right side of the lock (fixed level)
    sim.AnimateRectangle(spec=(xdoor[right], ylevel[right] - waterdepth, xbound[right], ylevel[right]), fillcolor="aqua")
    # The third rectangle represents the water inside the lock, which will be switching
    sim.AnimateRectangle(spec=lock_water_rectangle, fillcolor="aqua")
    # The fourth rectangle is the left door, which will be apearing and dissapearing
    sim.AnimateRectangle(spec=lock_door_left_rectangle)
    # The fifth rectangle is the right door, which will be apearing and dissapearing
    sim.AnimateRectangle(spec=lock_door_right_rectangle)

    # AnimateSlider is a class of Salabim to allow adjusting some parameters on the screen during the simulation
    # In this example, we can adjust the interarrival time and the ships mean length
    sim.AnimateSlider(x=520, y=0, width=100, height=20, vmin=16, vmax=60, resolution=4, v=iat, label="iat", action=set_iat, xy_anchor="nw")
    sim.AnimateSlider(
        x=660, y=0, width=100, height=20, vmin=10, vmax=60, resolution=5, v=meanlength, label="mean length", action=set_meanlength, xy_anchor="nw"
    )

    # The class AnimateMonitor allows display monitors on the screen while running the simulation
    sim.AnimateMonitor(
        wait[left].length,
        linecolor="orange",
        fillcolor="bg",
        x=-225,
        y=-200,
        xy_anchor="n",
        horizontal_scale=1,
        width=450,
        linewidth=2,
        title=lambda: "Number of waiting ships left. Mean={:10.2f}".format(wait[left].length.mean()),
    )
    sim.AnimateMonitor(
        wait[right].length,
        linecolor="orange",
        fillcolor="bg",
        x=-225,
        y=-300,
        xy_anchor="n",
        horizontal_scale=1,
        width=450,
        linewidth=2,
        title=lambda: "Number of waiting ships right. Mean={:10.2f}".format(wait[right].length.mean()),
    )
    sim.AnimateMonitor(
        wait[left].length_of_stay,
        linecolor="white",
        fillcolor="bg",
        x=-225,
        y=-400,
        xy_anchor="n",
        vertical_scale=0.5,
        horizontal_scale=5,
        width=450,
        height=75,
        linewidth=4,
        title=lambda: "Waiting time of ships left. Mean={:10.2f}".format(wait[left].length_of_stay.mean()),
    )
    sim.AnimateMonitor(
        wait[right].length_of_stay,
        linecolor="white",
        fillcolor="bg",
        x=-225,
        y=-500,
        xy_anchor="n",
        vertical_scale=0.5,
        horizontal_scale=5,
        width=450,
        height=75,
        linewidth=4,
        title=lambda: "Waiting time of ships left. Mean={:10.2f}".format(wait[right].length_of_stay.mean()),
    )

    # There is another queue in the system, the one inside the lock while switching: lockqueue
    sim.AnimateQueue(queue=lockqueue, x=lambda: xdoor[-lock.sideq], y=lock_y, direction=lambda: "w" if lock.sideq == left else "e")
    #  Note that the y-coordinate is dynamic, making it possible that the queue moves up or down


# In[5]:


# A function to set the global variable iat (interarrival time)
def set_iat(val):
    global iat
    iat = float(val)


# A function to set the global variable meanlength (mean length of the ships)
def set_meanlength(val):
    global meanlength
    meanlength = float(val)


# In[6]:


# Generator of ships for each side of the lock
class Shipgenerator(sim.Component):
    def process(self):
        while True:  # Infinite loop to generate ships
            self.hold(sim.Exponential(iat).sample())
            ship = Ship(name=sidename(self.side) + "ship.")  # The name os the ship is lship.# of rship.#
            ship.side = self.side
            ship.length = meanlength * sim.Uniform(2.0 / 3, 4.0 / 3).sample()
            if lock.mode() == "Idle":  # If lock is idle then activate it
                lock.activate()


# The component Ship can have the following modes:
# - Wait
# - Sail in
# - In lock
# - Sail out

# In[7]:


class Ship(sim.Component):
    # animation_objects is a method of Component that defines how to display a component in AnimateQueue
    def animation_objects(self, q):
        size_x = self.length  # how much to display the ship in x-direction
        size_y = 5  # how much to display the ship in y-direction
        # an0 is an instance of Animate class - a polygon representing the ship
        an0 = sim.AnimatePolygon(
            spec=ship_polygon(self),
            fillcolor=shipcolor(self.side),
            linewidth=0,
            text=" " + self.name(),
            textcolor="white",
            layer=1,
            fontsize=2.6,
            text_anchor=("e" if self.side == left else "w"),
        )
        return (size_x, size_y, an0)

    def process(self):
        self.enter(wait[self.side])  # Ship enters the queue at the corresponding side
        self.passivate(mode="Wait")  # Ship is passivated and mode is set at Wait
        self.hold(intime, mode="Sail in")  # Ship starts moving towards the lock
        self.leave(wait[self.side])  # Ship leaves the queue at one side of the lock
        self.enter(lockqueue)  # Ship enters the queue inside the lock
        lock.activate()  # Ship activates the lock after accessing the lock
        self.passivate(mode="In lock")  # Ship is passivated and mode is set at In Lock
        self.leave(lockqueue)  # Ship leaves the queue located inside the lock
        self.hold(outtime, mode="Sail out")  # Ship sails out the lock
        lock.activate()  # Ship activates the lock after sailing out


# In[8]:


# This function calculates, by interpolation, the level of the water inside the lock when switching
def lock_y(t):
    if lock.mode() == "Switch":
        y = sim.interpolate(t, lock.mode_time(), lock.scheduled_time(), ylevel[lock.side], ylevel[-lock.side])
    else:
        y = ylevel[lock.side]
    return y


# The component Lock can have the following modes:
# - Idle
# - Wait for sail in
# - Switch
# - Wait for sail out

# In[9]:


class Lock(sim.Component):
    def process(self):
        while True:
            if len(wait[left]) + len(wait[right]) == 0:
                self.passivate(mode="Idle")  # Passivate lock if no ships in queue

            usedlength = 0  # Occupied length within the lock

            for ship in wait[self.side]:  # We check if another ship in the queue fits into the remaining space
                if usedlength + ship.length <= locklength:  # There is still room for this ship
                    usedlength += ship.length
                    ship.activate()
                    self.passivate("Wait for sail in")  # Passivate (mode)

            self.hold(switchtime, mode="Switch")  # Component.hold(duration, mode), water level moving
            self.side = -self.side  # After switching the water level, the side is changed
            for ship in lockqueue:  # Ships inside the lock
                ship.activate()  # Activates the ships that has to sail out and then they leave the system
                self.passivate("Wait for sail out")  # Lock waits for the ship to sail out
            self.sideq = -self.sideq  # Now we are ready to serve the opposite queue


# In[10]:


env = sim.Environment()


# In[11]:


locklength = 60  # Length of the lock (see sketch above)
switchtime = 10  # Time required to switch the water level from high to low or vice versa
intime = 2  # Time required to let ships sail in
outtime = 2  # Time required to let ships sail out
meanlength = 30  # Ships mean length (used to generate ships)
iat = 20  # Interarrival time of ships


# In[12]:


lockqueue = sim.Queue("lockqueue")  # This is the queue inside the lock


# In[13]:


wait = {}  # A dictionary containing the two queues: left and right


# In[14]:


for side in (left, right):
    wait[side] = sim.Queue(name=sidename(side) + "Wait")  # Queues at both sides are generated
    shipgenerator = Shipgenerator(name=sidename(side) + "Shipgenerator")  # lShipgenerator or rShipgenerator
    shipgenerator.side = side


# In[15]:


lock = Lock(name="lock")  # Lock is instantiated
lock.side = left  # When starting the simulation the side is left
lock.sideq = left  # The queue we are going to serve


# In[16]:


do_animation()


# In[17]:


env.run()