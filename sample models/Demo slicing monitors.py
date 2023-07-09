import salabim as sim


class X(sim.Component):
    def process(self):
        while True:
            self.hold(sim.Uniform(1, 5)())
            res = sim.Pdf(resources, 1)()
            self.request(res)
            self.hold(res.sequence_number() * 1 + (env.now() % 24) * 0.01)
            self.release()


env = sim.Environment(time_unit="hours", trace=False)

for _ in range(20):
    X()

resources = [sim.Resource() for _ in range(13)]

env.run(till=env.days(100))

for res in resources:
    print(f"{res.name():13s}total {res.occupancy.mean():10.3f}")
    for hour in range(24):
        print(f"{res.name():13s}{hour:2d}-{hour+1:2d} {res.occupancy[hour: hour+1: 24].mean():10.3f}")
    print()

occupancy_aggregated = sum(res.occupancy for res in resources)

print(f"Total        total {occupancy_aggregated.mean() / len(resources):10.3f}")

for hour in range(24):
    print(f"Total        {hour:2d}-{hour+1:2d} {occupancy_aggregated[hour: hour+1: 24].mean() / len(resources):10.3f}")

occupancy_aggregated.print_histogram()