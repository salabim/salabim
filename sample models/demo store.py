# demo store
import salabim as sim


class Consumer(sim.Component):
    def process(self):
        while True:
            product = self.from_store(products)
            self.hold(sim.Uniform(0, 2))


class Producer(sim.Component):
    def process(self):
        while True:
            self.hold(1)
            product = sim.Component("product.")
            self.to_store(products, product)


env = sim.Environment(trace=False)

products = sim.Store("products", capacity=3)

consumer = Consumer()
producer = Producer()

env.run(100)

producer.status.print_histogram(values=True, graph_scale=30)
consumer.status.print_histogram(values=True, graph_scale=30)
products.contents().length.print_histogram(graph_scale=None)