# simulates a carwash; cars queue up at the entrance; each car chooses
# one of two grades of wash, MostlyClean (1.0 unit of time) and Gleaming
# (2.0 units of time); there is only one bay in the carwash, so only one
# is served at a time; at the exit there is a buffer space where cars
# wait to go out onto the street; cross traffic does not stop, so a car
# must wait for a large enough gap in the traffic in order to move out
# onto the street

# usage:

# python CarWash.py ArrRate PropMostlyClean BufSize CrossRate ExitTime MaxSimTime

# where:

#    ArrRate = rate of arrivals of calls to carwash (reciprocal of mean
#              time between arrivals)
#    PropMostlyClean = proportion of cars that opt for the MostlyClean wash
#    BufSize = number of cars that can fit in the exit buffer
#    CrossRate = rate of arrivals of cars on the street passing the carwash
#    ExitTime = time needed for one car to get out onto the street
#    MaxSimtime = amount of time to simulate

# basic strategy of the simulation:  model the carwash itself as a
# Resource, and do the same for the buffer and the front spot in the
# buffer; when a car acquires the latter, it watches for a gap big
# enough to enter the street

import salabim as sim

class Street(sim.Component):

    def process(self):
        while True:
            self.nextarrival=env.now()+street_iat.sample()
            wakeup.trigger()
            yield self.hold(till=self.nextarrival)

class Car(sim.Component):
    def process(self):
        yield self.request(bay,mode='wait for bay')
        yield self.hold(wash_time.sample(),mode='wash')
        yield self.request(buffer,mode='wait for buffer')
        self.release(bay)
        yield self.request(bufferfront)
        # OK, now wait to get out onto the street; every time a new car
        # arrives in cross traffic, it will signal us to check the new
        # next arrival time
        while env.now()+time_to_exit >= street.nextarrival:
            yield self.wait(wakeup,mode='wait for wakeup')
        yield self.hold(time_to_exit,mode='exit')
        self.release(bufferfront)
        self.release(buffer)

class CarWash(sim.Component):
    def process(self):
        while True:
            yield self.hold(wash_iat.sample())
            Car()

env=sim.Environment(trace=True)
wakeup=sim.State(name='wakeup')
wash_time=sim.Pdf((1.0,0.7, 2.0,0.3))
street_iat=sim.Exponential(1)
wash_iat=sim.Exponential(1)
buffer=sim.Resource(capacity=4)
bufferfront=sim.Resource()
bay=sim.Resource()
time_to_exit=1
CarWash()
street=Street()

env.run(500)



