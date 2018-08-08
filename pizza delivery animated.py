import salabim as sim
import math


def distance(comp1, comp2):
    return math.sqrt((comp1.x - comp2.x) ** 2 + (comp1.y - comp2.y) ** 2)


class Restaurant(sim.Component):
    def setup(self):
        self.x = env.x_dis()
        self.y = env.y_dis()
        self.an = sim.AnimateRectangle((-10, -10, 10, 10),
            text='R' + str(self.sequence_number()), x=self.x, y=self.y, text_anchor='c')


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
        self.pic_customer = sim.AnimateRectangle((-10, -10, 10, 10), text=str(self.customer.sequence_number()), fillcolor='gray', x=self.customer.x, y=self.customer.y)
        self.pic_order = sim.AnimateLine((self.restaurant.x,
            self.restaurant.y, self.customer.x, self.customer.y),
            linecolor=self.driver.color, text=self.name(), textcolor=self.driver.color, linewidth=2)
        if self.driver.ispassive():
            self.driver.activate()


class Driver(sim.Component):
    def setup(self, v):
        self.x = env.x_dis()
        self.y = env.y_dis()
        self.v = v
        self.orders = sim.Queue(self.name() + '.orders')
        self.color = ('red', 'blue', 'green', 'purple', 'black', 'pink')[self.sequence_number()]
        self.pic_driver = sim.Animate(circle0=10, x0=self.x, y0=self.y,
            fillcolor0='', linecolor0=self.color, linewidth0=2)

    def process(self):
        while True:
            while not self.orders:
                yield self.passivate()
            order = self.orders[0]
            for try_order in self.orders[1:]:
                if distance(self, try_order.restaurant) < distance(self, order.restaurant):
                    order = try_order
            driving_duration = distance(self, order.restaurant) / self.v
            self.pic_driver.update(x1=order.restaurant.x, y1=order.restaurant.y, t1=env.now() + driving_duration, fillcolor0='')
            yield self.hold(driving_duration)
            driving_duration = distance(order.restaurant, order.customer) / self.v
            self.pic_driver.update(x1=order.customer.x, y1=order.customer.y, t1=env.now() + driving_duration, fillcolor0=self.color)
            yield self.hold(driving_duration)
            self.x = order.customer.x
            self.y = order.customer.y
            order.leave()  # leave all (tw) queues the order is in
            order.pic_order.remove()
            order.pic_customer.remove()


env = sim.Environment(trace=False, random_seed=1021021)

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
sim.AnimateRectangle((x_min, y_min, x_max, y_max), fillcolor='90%gray')

env.customers = [Customer(inter_arrival_time=inter_arrival_time) for _ in range(n_customers)]
env.drivers = [Driver(v=v) for _ in range(n_drivers)]
env.restaurants = [Restaurant() for _ in range(n_restaurants)]

env.orders=sim.Queue('all orders')
env.animate(True)
env.speed(16)
env.modelname('pizza delivery')
env.orders.length.animate(x=x_min, y=y_max + 20, horizontal_scale=2, width=x_max - x_min, title='Number of orders in system')

#env.video('pizza delivery.mp4')
env.run(1000)
#env.video(False)
env.orders.print_histograms()