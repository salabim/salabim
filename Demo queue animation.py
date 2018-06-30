import salabim as sim


class X(sim.Component):
    def setup(self, i):
        self.i = i

    def animation_objects(self, id):
        if id == 'text':
            ao0 = sim.AnimateText(text=self.name(), textcolor='fg', text_anchor='nw')
            return 0, 16, ao0
        else:
            ao0 = sim.AnimateRectangle((0, 0, 40, 20),
                text=self.name(), fillcolor=id, textcolor='white', arg=self)
            return 45, 0, ao0

    def process(self):
        while True:
            yield self.hold(sim.Uniform(0, 20)())
            self.enter(q)
            yield self.hold(sim.Uniform(0, 20)())
            self.leave()


env = sim.Environment(trace=False)
env.background_color('20%gray')

q = sim.Queue('queue')

sim.AnimateText('queue, normal', x=100, y=50, text_anchor='nw')
qa0 = sim.AnimateQueue(q, x=100, y=50, direction='e', id='blue')

sim.AnimateText('queue, limited to six components', x=100, y=250, text_anchor='nw')
qa1 = sim.AnimateQueue(q, x=100, y=250, direction='e', max_length=6, id='red')

sim.AnimateText('queue, reversed', x=100, y=150, text_anchor='nw')
qa2 = sim.AnimateQueue(q, x=100, y=150, direction='e', reverse=True, id='green')

sim.AnimateText('queue, text only', x=80, y=460, text_anchor='sw', angle=270)
qa3 = sim.AnimateQueue(q, x=100, y=460, direction='s', id='text')

sim.AnimateMonitor(q.length, x=10, y=480, width=450, height=100, horizontal_scale=5, vertical_scale=5)

sim.AnimateMonitor(q.length_of_stay, x=10, y=600, width=450, height=100, horizontal_scale=5, vertical_scale=5)

sim.AnimateText(text=lambda: q.length.print_histogram(as_str=True), x=500, y=700,
    text_anchor='nw', font='narrow', fontsize=10)

sim.AnimateText(text=lambda: q.print_info(as_str=True), x=500, y=340,
    text_anchor='nw', font='narrow', fontsize=10)

[X(i=i) for i in range(15)]
env.animate(True)
env.run()
