import salabim as sim
import math


def distance(comp1, comp2):
    return math.sqrt((comp1.x - comp2.x) ** 2 + (comp1.y - comp2.y) ** 2)


class Restaurant(sim.Component):
    def setup(self):
        self.x = env.x_dis()
        self.y = env.y_dis()


class Customer(sim.Component):
    def setup(self, inter_arrival_time):
        self.x = env.x_dis()
        self.y = env.y_dis()
        self.inter_arrival_time = inter_arrival_time
        
    def process(self):
        while True:
            yield self.hold(self.inter_arrival_time())
            Order(restaurant=sim.Pdf(env.restaurants, 1)(), customer=self)


class Order(sim.Component):
    def setup(self, restaurant, customer):
        self.restaurant = restaurant
        self.customer = customer
        self.driver = sim.Pdf(env.drivers, 1)()
        self.enter(self.driver.orders)
        self.enter(env.orders)
        if self.driver.ispassive():
            self.driver.activate()


class Driver(sim.Component):
    def setup(self, v):
        self.x = env.x_dis()
        self.y = env.y_dis()
        self.v = v
        self.orders = sim.Queue(self.name() + '.orders')

    def process(self):
        while True:
            while not self.orders:
                yield self.passivate()
            order = self.orders[0]
            for try_order in self.orders[1:]:
                if distance(self, try_order.restaurant) < distance(self, order.restaurant):
                    order = try_order
            driving_duration = distance(self, order.restaurant) / self.v
            yield self.hold(driving_duration)
            driving_duration = distance(order.restaurant, order.customer) / self.v
            yield self.hold(driving_duration)
            self.x = order.customer.x
            self.y = order.customer.y
            order.leave()  # leave all (two) queues the order is in


env = sim.Environment(trace=True, random_seed=1021021)

x_min = 25
y_min = 25
x_max = 1000
y_max = 550

n_drivers = 3
n_restaurants = 5
n_customers = 25
v = 10
inter_arrival_time = sim.Exponential(1000)

env.x_dis = sim.Uniform(x_min, x_max)
env.y_dis = sim.Uniform(y_min, y_max)

env.customers = [Customer(inter_arrival_time=inter_arrival_time) for _ in range(n_customers)]
env.drivers = [Driver(v=v) for _ in range(n_drivers)]
env.restaurants = [Restaurant() for _ in range(n_restaurants)]

env.orders=sim.Queue('all orders')
env.run(100)
env.trace(False)
env.run(till=100000)
env.orders.print_histograms()