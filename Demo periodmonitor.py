import salabim as sim

'''
This model demonstrates the use of period monitors.
The model let 15 components randomly enter and leave a queue, called q.
After running for 30 * 24 hours, it shows the statistics per hour and finally
shows the result of some checks by aggregating the hourly data.
'''

class X(sim.Component):

    def process(self):
        while True:
            yield self.hold(sim.Uniform(0, 20)())
            self.enter(q)
            yield self.hold(sim.Uniform(0, 20)())
            self.leave()

env = sim.Environment(trace=False)

q = sim.Queue(name='q')
qlength_per_hour = sim.PeriodMonitor(parent_monitor=q.length, periods=(24 * [1]))
qlength_of_stay_per_hour = sim.PeriodMonitor(parent_monitor=q.length_of_stay, periods=(24 * [1]))
[X() for i in range(15)]

env.run(30 * 24)
q.print_statistics()

for hour in range(24):
    qlength_per_hour[hour].print_statistics()
    qlength_of_stay_per_hour[hour].print_statistics()

print()
print('checks')
print('======')
print(f'mean of length                                             {q.length.mean():10.7f}')
print(f'weighted sum of mean of period monitors of length          {sum(qlength_per_hour[hour].mean()/24 for hour in range(24)):10.7f}')
print(f'mean of length_of_stay                                     {q.length_of_stay.mean():10.7f}')
tot1 = 0
tot2 = 0
for hour in range(24):
    if qlength_of_stay_per_hour[hour].number_of_entries != 0:
        tot1 += qlength_of_stay_per_hour[hour].number_of_entries() * qlength_of_stay_per_hour[hour].mean()
        tot2 += qlength_of_stay_per_hour[hour].number_of_entries()

print(f'weighted sum of mean of period monitors of length_of_stay  {tot1 / tot2:10.7f}')


