"""
ELEVATOR ANIMATED
This sample code simulates an elevator using salabim's capabilities, including animation.
The user can set some values on the animation screen: number of floors, number of elevator cabins,
capacity of the cabins (persons) and the number of visitors requesting an elevator.
The default values set in the code are as follows:
    Number of floors: topfloor = 15
    Number of elevator cabins: ncars = 3
    Capacity of each cabin: capacity = 4
    Number of visitors requesting a lift:
        From level 0 to level n: load_0_n = 50
        From level n to level n: load_n_n = 100
        From level n to level 0: load_n_0 = 100
"""

from __future__ import print_function  # compatibility with Python 2.x
from __future__ import division  # compatibility with Python 2.x

import salabim as sim


def do_animation():  # Animation initialisation is done in this function
    # In this example, the simulation code is completely separated from the animation code

    # Some global variables accesible from any classes and functions in the code
    global xvisitor_dim  # x-dimension of the square representing a visitor
    global yvisitor_dim  # y-dimension of the square representting a visitor
    global xcar  # x-dimension of the elevator car/s
    global capacity_last, ncars_last, topfloor_last

    # Some general parameters about the simulation (See Reference: salabim.Environment)
    env.modelname("Elevator")
    env.speed(32)
    env.background_color("20%gray")
    if make_video:
        env.video("Elevator.mp4")

    # We assign values to some the global variables
    xvisitor_dim = 30  # x-dimension of the square representing a visitor
    yvisitor_dim = xvisitor_dim  # y-dimension of the square representing a visitor
    yfloor0 = 20  # y-coordinate of floor 0

    xcar = {}  # This is a dictionary containing the x-coordinates of the cars
    xled = {}  # This is a dictionary containing the x-coordinates of the leds

    x = env.width()  # Width of the animation in screen coordinates (See Reference)
    # This is the width available to display all the elements on the screen
    # Now we assign x-coordinates, from the right to left of the screen

    for car in cars:  # We assign x-coordinates to the elevator cars
        x -= (capacity + 1) * xvisitor_dim  # Each car must contain visitors
        xcar[car] = x  # We store the car x-coordinate in the dictionary
    x -= xvisitor_dim  # Additional space (one square)
    xsign = x  # Position of the text with the number of floor
    x -= xvisitor_dim / 2  # Additional space (half square)
    for direction in (up, down):  # Position of the leds (red/green)
        x -= xvisitor_dim / 2
        xled[direction] = x  # We store the led x-coordinates in the dictionary
    x -= xvisitor_dim  # Another square to the right
    xwait = x  # Where to show the queues at different floors

    for floor in floors:  # Components needed to display the floors
        y = yfloor0 + floor.n * yvisitor_dim  # y-coordinate of the floors
        floor.y = y
        for direction in (up, down):  # Led indicating the direction of the car
            if (direction == up and floor.n < topfloor) or (direction == down and floor.n > 0):
                b = xvisitor_dim / 4  # Dimension used to define the triangle
                animate_led = sim.AnimatePolygon(  # See Reference AnimatePolygon
                    spec=(-b, -b, b, -b, 0, b),  # this is triangle
                    x=xled[direction],
                    y=y + 2 * b,
                    angle=0 if direction == up else 180,  #  up points up, down points down
                    fillcolor=direction_color(direction),  #  up is red, down is green
                    visible=lambda arg, t: arg in requests,
                    arg=(floor, direction),
                )
                #  if (floor, direction) in requests, show, otherwise do not show

        sim.AnimateLine(x=0, y=y, spec=(0, 0, xwait, 0))  # Horizontal lines for floors
        sim.AnimateText(
            x=xsign, y=y + yvisitor_dim / 2, text=str(floor.n), fontsize=xvisitor_dim / 2
        )  # Text indicating the floor number

        sim.AnimateQueue(queue=floor.visitors, x=xwait - xvisitor_dim, y=floor.y, direction="w")
        # The queue at each floor of people waiting for the elevator, build westward

    for car in cars:  # Components needed to display the cars
        x = xcar[car]  # A dictionary containing the x-coordinates of the cars
        car.pic = sim.AnimateRectangle(
            x=x,
            y=car.y,  # Main rectangle representing the car
            spec=(0, 0, capacity * xvisitor_dim, yvisitor_dim),
            fillcolor="lightblue",
            linewidth=0,
        )
        sim.AnimateQueue(queue=car.visitors, x=xcar[car], y=car.y, direction="e", arg=car)
        #  note that both the rectangle and the queue have a dynamic y-coordinate that
        #  is controlled by the car.y method

    # The following Animate elements are sliders, which allow controlling different variables
    # on the animation screen
    ncars_last = ncars
    sim.AnimateSlider(
        x=510,
        y=0,
        width=90,
        height=20,
        vmin=1,
        vmax=5,
        resolution=1,
        v=ncars,
        label="#elevators",
        action=set_ncars,
        xy_anchor="nw",
    )

    topfloor_last = topfloor
    sim.AnimateSlider(
        x=610,
        y=0,
        width=90,
        height=20,
        vmin=5,
        vmax=20,
        resolution=1,
        v=topfloor,
        label="top floor",
        action=set_topfloor,
        xy_anchor="nw",
    )

    capacity_last = capacity
    sim.AnimateSlider(
        x=710,
        y=0,
        width=90,
        height=20,
        vmin=2,
        vmax=6,
        resolution=1,
        v=capacity,
        label="capacity",
        action=set_capacity,
        xy_anchor="nw",
    )

    sim.AnimateSlider(
        x=510,
        y=-50,
        width=90,
        height=25,
        vmin=0,
        vmax=400,
        resolution=25,
        v=load_0_n,
        label="Load 0->n",
        action=set_load_0_n,
        xy_anchor="nw",
    )

    sim.AnimateSlider(
        x=610,
        y=-50,
        width=90,
        height=25,
        vmin=0,
        vmax=400,
        resolution=25,
        v=load_n_n,
        label="Load n->n",
        action=set_load_n_n,
        xy_anchor="nw",
    )

    sim.AnimateSlider(
        x=710,
        y=-50,
        width=90,
        height=25,
        vmin=0,
        vmax=400,
        resolution=25,
        v=load_n_0,
        label="Load n->0",
        action=set_load_n_0,
        xy_anchor="nw",
    )

    env.animate(True)  # starts the animation


def set_load_0_n(val):  # Setter for numer of visitors from level 0 to level n
    global load_0_n
    load_0_n = float(val)
    if vg_0_n.ispassive():  # vg_0_n is a VisitorGenerator
        vg_0_n.activate()


def set_load_n_n(val):  # Setter for numer of visitors from level n to level n
    global load_n_n
    load_n_n = float(val)
    if vg_n_n.ispassive():  # vg_n_n is a VisitorGenerator
        vg_n_n.activate()


def set_load_n_0(val):  # Setter for number of visitors from level n to level 0
    global load_n_0
    load_n_0 = float(val)
    if vg_n_0.ispassive():  # vg_n_0 is a VisitorGenerator
        vg_n_0.activate()


def set_capacity(val):  # Setter for capacity of the elevator cabins
    global capacity
    global capacity_last
    capacity = int(val)
    if capacity != capacity_last:
        capacity_last = capacity
        env.main().activate()


def set_ncars(val):  # Setter for number of cars (cabins)
    global ncars
    global ncars_last
    ncars = int(val)
    if ncars != ncars_last:
        ncars_last = ncars
        env.main().activate()


def set_topfloor(val):  # Setter for number of floors
    global topfloor
    global topfloor_last
    topfloor = int(val)
    if topfloor != topfloor_last:
        topfloor_last = topfloor
        env.main().activate()


def direction_color(direction):  # Function to assign color of a visitor or led
    if direction == 1:
        return "red"
    if direction == -1:
        return "green"
    return "yellow"


class VisitorGenerator(sim.Component):  # Class inheriting from sim.Component
    def setup(self, from_, to, id):  # Setup is a method of Component, can be overriden
        # It is called immediately after initialisation of a Component
        self.from_ = from_
        self.to = to
        self.id = id  # There are 3 types: 0_n, n_0, n_n

    def process(self):
        while True:  # Infinite loop
            # Selects randomly the origin floor of that visitor
            fromfloor = floors[sim.IntUniform(self.from_[0], self.from_[1]).sample()]
            # Selects randomly the destination floor of that visitor
            while True:
                tofloor = floors[sim.IntUniform(self.to[0], self.to[1]).sample()]
                if fromfloor != tofloor:  # The selection is valid if origin and destination are different
                    break

            Visitor(fromfloor=fromfloor, tofloor=tofloor)  # Generates an instance of Visitor
            if self.id == "0_n":
                load = load_0_n
            elif self.id == "n_0":
                load = load_n_0
            else:
                load = load_n_n

            if load == 0:  # If there is no load then passivate the VisitorGenerator
                yield self.passivate()
            else:
                iat = 3600 / load
                r = sim.Uniform(0.5, 1.5).sample()
                yield self.hold(r * iat)  # Holds during interarrival time


class Visitor(sim.Component):  # Class inheriting from sim.Component
    def setup(self, fromfloor, tofloor):
        self.fromfloor = fromfloor
        self.tofloor = tofloor
        self.direction = getdirection(self.fromfloor, self.tofloor)

    # animation_objects defines how to display a component in AnimateQueue
    # This method is overriden
    def animation_objects(self, q):
        size_x = xvisitor_dim  # how much to displace the next component in x-direction
        size_y = yvisitor_dim  # how much to displace the next component in y-direction
        b = 0.1 * xvisitor_dim
        # Instances of Animate class:
        an0 = sim.AnimateRectangle(
            spec=(b, 2, xvisitor_dim - b, yvisitor_dim - b),
            linewidth=0,
            fillcolor=direction_color(self.direction),
            text=str(self.tofloor.n),
            fontsize=xvisitor_dim * 0.7,
            textcolor="white",
        )
        return size_x, size_y, an0

    def process(self):
        self.enter(self.fromfloor.visitors)  # Visitor enters the queue at its floor floor
        # Visitor requests a trip between one origin floor and one direction
        # That trip is added to requests if nobody has requested it before
        if not (self.fromfloor, self.direction) in requests:
            requests[self.fromfloor, self.direction] = self.env.now()
            #  the arrival of the first request is used for the decision process where a car should go to
        for car in cars:  # Every passive car is activated
            if car.ispassive():
                car.activate()  # this is not a very efficient way, but it's simple ...

        yield self.passivate()  # The visitor will wait until it has arrived at its tofloor


class VisitorsInCar(sim.Queue):  # A queue of visitors inside the car
    pass


class Car(sim.Component):  # Class that inherits from sim.Component
    def setup(self):  # Setup is a method of Component, can be overriden
        self.capacity = capacity  # Capacity (visitors) of the car
        self.direction = still  # Direction can be still, up or down
        self.floor = floors[0]  # Stores the floor where the car is positioned, start at ground level
        self.visitors = VisitorsInCar()  # Queue of visitors in the car

    def y(self, t):  # This is used by the animation to define the level of a car
        # When the car is in mode 'Move' the level (y) will be varying over time
        if self.mode() == "Move":
            y = sim.interpolate(t, self.mode_time(), self.scheduled_time(), self.floor.y, self.nextfloor.y)
            # linear interpolation between self.floor.y and self.next_floor.y based on
            # the time it left self.floor.y (i.e. self.mode_time() and
            # the time it arrives at self.next_floor.y (i.e. self.scheduled_time())
        else:
            y = self.floor.y
        return y

    def process(self):
        dooropen = False  # Local variable controlling the state of the door
        self.floor = floors[0]  # Car initiates at floor 0
        self.direction = still  # Car initiates as still
        while True:
            if self.direction == still:
                # If car is still and no requests then passivate and mode Idle
                if not requests:
                    yield self.passivate(mode="Idle")
            if self.count_to_floor(self.floor) > 0:
                # If there are visitors inside the car for this floor then open door
                yield self.hold(dooropen_time, mode="Door open")
                dooropen = True
                for visitor in self.visitors:
                    # A loop to allow all visitors for this floor to leave
                    if visitor.tofloor == self.floor:
                        visitor.leave(self.visitors)
                        visitor.activate()  # end of the visitor
                yield self.hold(exit_time, mode="Let exit")

            if self.direction == still:
                self.direction = up  # just random

            for self.direction in (self.direction, -self.direction):
                # A loop to allow visitors going in the specific direction (up/down)
                # enter the car.
                if (self.floor, self.direction) in requests:
                    del requests[self.floor, self.direction]
                    # We, initialy, delete that job from requests
                    if not dooropen:
                        yield self.hold(dooropen_time, mode="Door open")
                        dooropen = True
                    for visitor in self.floor.visitors:
                        if visitor.direction == self.direction:
                            # If visitor goes in that direction then allow him to enter
                            if len(self.visitors) < self.capacity:
                                visitor.leave(self.floor.visitors)
                                # Leaves the queue at that floor
                                visitor.enter(self.visitors)
                                # Enters the queue inside the car
                        yield self.hold(enter_time, mode="Let in")
                    if self.floor.count_in_direction(self.direction) > 0:
                        # If there are still visitors going up/down in that floors
                        # then add the request to the list of requests
                        if not (self.floor, self.direction) in requests:
                            requests[self.floor, self.direction] = self.env.now()

                if self.visitors:
                    break
            else:
                if requests:
                    # If we still have requests, which is the earliest?
                    earliest = sim.inf
                    for (floor, direction) in requests:
                        if requests[floor, direction] < earliest:
                            self.direction = getdirection(self.floor, floor)
                            earliest = requests[floor, direction]  # find the earliest request
                else:
                    self.direction = still
            if dooropen:
                yield self.hold(doorclose_time, mode="Door close")
                dooropen = False

            if self.direction != still:
                # Finally, the car is moving up or down to the next floor
                self.nextfloor = floors[self.floor.n + self.direction]
                yield self.hold(move_time, mode="Move")  # the mode_time is used in the animation
                self.floor = self.nextfloor

    def count_to_floor(self, tofloor):
        # Function to count the number of visitors inside the car for that floor
        n = 0
        for visitor in self.visitors:
            if visitor.tofloor == tofloor:
                n += 1
        return n


class Visitors(sim.Queue):  # A class to define a queue of visitors
    pass


class Floor:
    # A class defining the floors with a method to count its visitors
    def __init__(self):
        self.visitors = Visitors()
        self.n = self.visitors.sequence_number()

    def count_in_direction(self, dir):
        n = 0
        for visitor in self.visitors:
            if visitor.direction == dir:
                n += 1
        return n


def getdirection(fromfloor, tofloor):
    # A function to calculate the direction up or down
    if fromfloor.n < tofloor.n:
        return +1
    if fromfloor.n > tofloor.n:
        return -1
    return 0


up = 1  # Direction of move up
still = 0  # Car is still
down = -1  # Direction of move down

move_time = 10  # Time for the car to move one floor up or down
dooropen_time = 3  # Time required to open doors
doorclose_time = 3  # Time required to close doors
enter_time = 3  # Time required to let visitors enter the car
exit_time = 3  # Time required to let visitors leave the car

load_0_n = 50  # Initial number of visitors per hour willing to go from level 0 to level n
load_n_n = 100  # Initial number of visitors per hour willing to go from level n to level n
load_n_0 = 100  # Initial number of visitors per hour willing to go from level n to level 0
# These parameters are used in the class VisitorGenerator

capacity = 4  # Inital capacity (persons) of the car (elevator cabin)
ncars = 3  # Initial number of cars
topfloor = 15  # Initial top floor to be reached by elevator

while True:
    # The simulation (re)initialization in done here
    # The code is inside a while loop to reinitialize when a capacity, number of floors or number of cars
    # have been changed with the slider

    env = sim.Environment(trace=False)

    vg_0_n = VisitorGenerator(from_=(0, 0), to=(1, topfloor), id="0_n", name="vg_0_n")
    vg_n_0 = VisitorGenerator(from_=(1, topfloor), to=(0, 0), id="n_0", name="vg_n_0")
    vg_n_n = VisitorGenerator(from_=(1, topfloor), to=(1, topfloor), id="n_n", name="vg_n_n")

    requests = {}
    floors = [
        Floor() for _ in range(topfloor + 1)
    ]  # create the required number of floors and put them in  the floors list

    cars = [Car() for _ in range(ncars)]  # create the required number of cars and put them in the cars list

    make_video = False

    do_animation()

    if make_video:
        env.run(1000)
        break  # if we make a video, only 1000 seconds are simulated
    else:
        env.run()

    env.animation_parameters(animate=False)
