import salabim as sim

env = sim.Environment()

monitor_names = sim.Monitor(name="names")
for _ in range(10000):
    name = sim.Pdf(("John", 30, "Peter", 20, "Mike", 20, "Andrew", 20, "Ruud", 5, "Jan", 5)).sample()
    monitor_names.tally(name)

monitor_names.print_histograms(values=True)
