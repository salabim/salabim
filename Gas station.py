import salabim as sim

GAS_STATION_SIZE = 200     # liters
THRESHOLD = 25             # Threshold for calling the tank truck (in %)
FUEL_TANK_SIZE = 50        # liters
# Min/max levels of fuel tanks (in liters)
FUEL_TANK_LEVEL = sim.Uniform(5, 25)
REFUELING_SPEED = 2        # liters / second
TANK_TRUCK_TIME = 300      # Seconds it takes the tank truck to arrive
T_INTER = sim.Uniform(10, 100)  # Create a car every [min, max] seconds
SIM_TIME = 200000           # Simulation time in seconds


class Car(sim.Component):
    '''
    A car arrives at the gas station for refueling.

    It requests one of the gas station's fuel pumps and tries to get the
    desired amount of gas from it. If the stations reservoir is
    depleted, the car has to wait for the tank truck to arrive.

    '''

    def process(self):
        fuel_tank_level = int(FUEL_TANK_LEVEL.sample())
        yield self.request(gas_station)
        liters_required = FUEL_TANK_SIZE - fuel_tank_level
        if (fuel_pump.available_quantity() - liters_required) / fuel_pump.capacity() * 100 < THRESHOLD:
            if tank_truck.ispassive():
                tank_truck.activate()
        yield self.request((fuel_pump, liters_required))
        yield self.hold(liters_required / REFUELING_SPEED)
#        yield self.release((fuel_pump,0))
        self.release(gas_station)


class TankTruck(sim.Component):
    '''
    Periodically check the level of the *fuel_pump* and call the tank
    truck if the level falls below a threshold.
    '''

    def process(self):
        while True:
            yield self.passivate()
            yield self.hold(TANK_TRUCK_TIME)
            fuel_pump.release()


class CarGenerator(sim.Component):
    '''
    Generate new cars that arrive at the gas station.
    '''

    def process(self):
        while True:
            yield self.hold(T_INTER.sample())
            Car()


# Setup and start the simulation
env = sim.Environment()
print('Gas Station refuelling')

# Create environment and start processes
gas_station = sim.Resource('gas_station', 2)
fuel_pump = sim.Resource(
    'fuel_pump', capacity=GAS_STATION_SIZE, anonymous=True)
tank_truck = TankTruck()
CarGenerator()

env.run(SIM_TIME)

fuel_pump.capacity.print_histogram()
fuel_pump.claimed_quantity.print_histogram()
fuel_pump.available_quantity.print_histogram()


gas_station.requesters().length.print_histogram()
gas_station.requesters().length_of_stay.print_histogram(30, 10, 0)
