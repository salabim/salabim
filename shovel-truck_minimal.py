# -*- coding: utf-8 -*-
# A Shovel-Truck Simulator Minimal (Deterministic) - for checking failures-repairs times of trucks
# Python Ver. 2.7.13
# salabim Ver. 2.2.9
__author__ = 'panagiotou'
#
import salabim as sim
#
# INPUT DATA SECTION
# General
RND_NUM_STREAM = 12345              # random number stream
WARMUP_TIME = 120                  # warm-up time in min
SIMULATION_TIME = 8                 # simulation time, in hours
# Facilities (Resources)
SHOVELS_NUMBER = 1                  # number of shovels
CRUSHERS_NUMBER = 1                 # number of crushers
# Trucks
TRUCKS_NUMBER = 1                   # number of trucks
TRUCKS_INTERARRIVAL_TIME = 2        # interarrival time for n trucks at the loading station (initially)
# Trucks Times
TRUCK_LOADING_TIME = 3                  # time for truck to be loaded by the shovel (includes spotting time), in min
TRUCK_TRAVEL_TO_CRUSHER_TIME = 8                # time for truck to travel to crushers, in min
TRUCK_UNLOAD_INTO_CRUSHER_TIME = 1              # time for truck to unload into crushers, in min
TRUCK_RETURN_FROM_CRUSHER_TO_SHOVEL_TIME = 15   # time for truck to return from crushers to the loading station, in min
# Failure & Repair Times
TRUCK_MTTF = 60                                 # time to occur a failure of a truck (MTTF), in  min
TRUCK_MTTR = 20                                 # time to repair a truck (MTTR), in  min


class Truck(sim.Component):
    """
    Circulates trucks from shovels to crushers or dump sites
    """
    def setup(self, truck=0):
        self.broken = False
        self.truckfailure = TruckFailure(truck=self)

    def process(self):
        while True:
            self.enter(queue_loading)   # truck enters the 'Queue_for_Loading'
            yield self.request((shovels, 1))  # truck requests if one shovel is available to load this truck
            self.leave(queue_loading)   # truck leaves the 'Queue_for_Loading'
            yield self.hold(truck_loading_time)  # time the shovel needs to load one truck
            self.release((shovels, 1))  # truck releases the shovel
            yield self.hold(truck_travel_to_crusher_time)  # time for truck to travel to crushers
            self.enter(queue_crusher)  # truck enters the 'Queue_for_Crusher'
            yield self.request((crushers, 1))  # truck requests if one dump is available to unload this truck
            self.leave(queue_crusher)  # truck leaves the 'Queue_for_Crusher'
            yield self.hold(truck_unload_into_crusher_time)  # time the truck needs to unload
            self.release((crushers, 1))  # truck releases the crushers
            yield self.hold(truck_return_from_crusher_to_shovel_time)  # time the truck needs to return to shovels


class TruckGenerator(sim.Component):
    """
    Generates n trucks, the 1st truck arrives at the loading station at time=0, the rest trucks arrive in
    time intervals = trucks_interarrival_time
    After all n trucks have been arrived, TruckGenerator "ends" and the n trucks circulate within the system.
    """
    def process(self):
        while True:
            for i in range(trucks_number):
                Truck(name='TR{:02d}'.format(i))  # trucks are named: TR00, TR01, TR02 etc.
                yield self.hold(trucks_interarrival_time)
            break


class TruckFailure(sim.Component):
    """
    Generates failures for trucks
    """
    def setup(self, truck):
        self.truck = truck

    def process(self):
        while True:
            yield self.hold(truck_mttf)   # time to occur a failure of a truck
            if not self.truck.broken:
                self.truck.broken = True
                self.truck.passivate()
                yield self.hold(truck_mttr)   # time to repair this truck
                self.truck.activate()


def main():
        env.trace(True)
        env.run(warmup_time)
        shovels.reset_monitors()
        crushers.reset_monitors()
        queue_loading.reset_monitors()
        queue_crusher.reset_monitors()
        env.trace(False)
        #env.run(till=(simulation_time * 60))  # sim time in hours * 60 = minutes
        env.run(till=(simulation_time * 60) + warmup_time )  # sim time in hours * 60 = minutes
        # print-outs
        shovels.print_statistics()
        crushers.print_statistics()
        queue_loading.print_statistics()
        queue_crusher.print_statistics()

# HOUSEKEEPING STATEMENTS
env = sim.Environment()
TruckGenerator()
# Assignment of input data to variables
# General
sim.random_seed(RND_NUM_STREAM)
warmup_time = WARMUP_TIME
simulation_time = SIMULATION_TIME
# Facilities (Resources)
shovels_number = SHOVELS_NUMBER
crushers_number = CRUSHERS_NUMBER
# Trucks
trucks_number = TRUCKS_NUMBER
trucks_interarrival_time = TRUCKS_INTERARRIVAL_TIME
# Trucks Times
truck_loading_time = TRUCK_LOADING_TIME
truck_travel_to_crusher_time = TRUCK_TRAVEL_TO_CRUSHER_TIME
truck_unload_into_crusher_time = TRUCK_UNLOAD_INTO_CRUSHER_TIME
truck_return_from_crusher_to_shovel_time = TRUCK_RETURN_FROM_CRUSHER_TO_SHOVEL_TIME
# Failure & Repair Times
truck_mttf = TRUCK_MTTF
truck_mttr = TRUCK_MTTR
# Declarations
shovels = sim.Resource(name="SHOVEL", capacity=shovels_number)
crushers = sim.Resource(name='CRUSHER', capacity=crushers_number)
queue_loading = sim.Queue('Queue_for_Loading')
queue_crusher = sim.Queue('Queue_for_Crusher')

if __name__ == '__main__':
    main()
