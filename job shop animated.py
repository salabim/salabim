import salabim as sim


class AnimateMachineBox(sim.Animate):
    def __init__(self, machine):
        self.machine = machine
        x = groups.index(machine.group) * 70 + 100
        y = env.height - 140 - (machine.group.machines.index(machine) * 15)
        sim.Animate.__init__(self, x0=x, y0=y, rectangle0=(0, 0, 60, 12), fillcolor0='red')

    def fillcolor(self, t):
        return self.machine.task.group.color if self.machine.task else 'bg'


class AnimateMachineText(sim.Animate):
    def __init__(self, machine):
        self.machine = machine
        x = groups.index(machine.group) * 70 + 100 + 2
        y = env.height - 140 - (machine.group.machines.index(machine) * 15)
        sim.Animate.__init__(self, x0=x, y0=y + 2, anchor='sw',
            text=str(machine.group.machines.index(machine)), textcolor0='white', fontsize0=12)

    def text(self, t):
        return self.machine.task.name() if self.machine.task else ''


def animation_pre_tick(self, t):
    for i, job in enumerate(plant):
        y = env.y_top - 45 - i * 15
        job.tasks.animate(x=200, y=y, direction='e')
        job.task_in_execution.animate(x=100, y=y)
        slack = job.slack_t(t)
        job.an_slack.update(y0=y, text='{:7.2f}'.format(slack), textcolor0=('red' if slack < 0 else 'fg'))
        job.an_label.update(y0=y)


def animation():
    env.animation_parameters(synced=False, modelname='Job shop')
    sim.Environment.animation_pre_tick = animation_pre_tick

    max_len = 0
    for i, group in enumerate(groups):
        x = i * 70 + 100 + 2
        y = env.height - 140 + 20
        sim.Animate(text=group.name(), x0=x, y0=y, anchor='sw', fontsize0=12)
        for machine in group.machines:
            AnimateMachineBox(machine=machine)
            AnimateMachineText(machine=machine)
        max_len = max(max_len, len(group.machines))
    env.y_top = y - max_len * 15 - 15
    sim.Animate(line0=(0, env.y_top, 2000, env.y_top))
    sim.Animate(text='job', x0=50, y0=env.y_top - 15, anchor='ne', fontsize0=12)
    sim.Animate(text='slack', x0=90, y0=env.y_top - 15, anchor='ne', fontsize0=12)
    sim.Animate(text='in execution', x0=100, y0=env.y_top - 15, anchor='nw', fontsize0=12)
    sim.Animate(text='waiting for execution -->', x0=200, y0=env.y_top - 15, anchor='nw', fontsize0=12)


class Group(sim.Component):
    def setup(self, job_select_method, fraction, number_of_machines, color):
        if job_select_method.lower() == 'fifo':
            self.job_select = self.job_select_fifo
        elif job_select_method.lower() == 'min_slack':
            self.job_select = self.job_select_min_slack
        else:
            raise AssertionError('wrong selection_method:', job_select_method)
        self.machines = [Machine(group=self, name=self.name() + '.machine.') for _ in range(number_of_machines)]

        self.fraction = fraction
        self.color = color
        self.jobs = sim.Queue(self.name() + '.jobs')
        self.idle_machines = sim.Queue(self.name() + '.idle_machines')

    def job_select_fifo(self):
        return self.jobs.head()

    def job_select_min_slack(self):
        return min(self.jobs, key=lambda job: job.slack_t(env.now()))


class Machine(sim.Component):
    def setup(self, group):
        self.group = group
        self.task = None

    def process(self):
        while True:
            self.task = None
            self.enter(self.group.idle_machines)
            while not self.group.jobs:  # use while instead of if, to avoid any problems with multiple activates
                yield self.passivate()
            self.leave(self.group.idle_machines)
            job = self.group.job_select()
            job.slack -= (env.now() - job.enter_time(self.group.jobs))
            job.leave(self.group.jobs)
            self.task = job.tasks.pop()
            self.task.enter(job.task_in_execution)
            yield self.hold(self.task.duration)
            self.task.leave(job.task_in_execution)

            if job.tasks:
                task1 = job.tasks.head()
                job.enter(task1.group.jobs)
                if task1.group.idle_machines:
                    task1.group.idle_machines.head().activate()
            else:
                job.leave(plant)
                job.an_slack.remove()
                job.an_label.remove()
                job.tasks.animate(on=False)


class JobGenerator(sim.Component):
    def setup(self, inter_arrival_time_dist, number_of_tasks_dist, group_dist, duration_dist):
        self.inter_arrival_time_dist = sim.Exponential(8)
        self.number_of_tasks_dist = sim.IntUniform(1, 9)
        self.group_dist = group_dist
        self.duration_dist = duration_dist

    def process(self):
        while True:
            yield self.hold(self.inter_arrival_time_dist())
            Job(job_generator=self)


class Job(sim.Component):
    def setup(self, job_generator):
        self.tasks = sim.Queue(fill=[Task(job_generator=job_generator, job=self,
            name='Task ' + str(self.sequence_number()) + '.')
            for _ in range(job_generator.number_of_tasks_dist())], name='tasks.')
        self.task_in_execution = sim.Queue(name='task_in_execution.')
        self.slack = start_slack
        self.an_slack = sim.Animate(x0=90, text='', fontsize0=12, anchor='se')
        self.an_label = sim.Animate(x0=50, text=str(self.sequence_number()), fontsize0=12, anchor='se')
        self.enter(self.tasks[0].group.jobs)
        if self.tasks.head().group.idle_machines:
            self.tasks.head().group.idle_machines.head().activate()
        self.enter(plant)

    def slack_t(self, t):
        if self.task_in_execution:
            return self.slack
        else:
            return self.slack - (t - self.enter_time(self.tasks.head().group.jobs))


class Task(sim.Component):
    def setup(self, job_generator, job):
        self.group = job_generator.group_dist()
        self.duration = job_generator.duration_dist()

    def animation_objects(self, q):
        an1 = sim.Animate(rectangle0=(0, 0, 60, 12), fillcolor0=self.group.color)
        an2 = sim.Animate(text=str(self.name()), anchor='sw', textcolor0='white', fontsize0=12, offsetx0=2, offsety0=2)
        return (70, 15, an1, an2)


env = sim.Environment(trace=False)

groups = []
with sim.ItemFile('job shop.txt') as f:
    job_select_method = f.read_item()

    while True:
        name = f.read_item()
        if name == '//':
            break
        number_of_machines = f.read_item_int()
        fraction = f.read_item_float()
        color = f.read_item()
        groups.append(Group(name=name, job_select_method=job_select_method,
            fraction=fraction, number_of_machines=number_of_machines, color=color))

    duration_dist = sim.Distribution(f.read_item())
    inter_arrival_time_dist = sim.Distribution(f.read_item())
    number_of_tasks_dist = sim.Distribution(f.read_item())
    start_slack = f.read_item_float()

plant = sim.Queue('plant')

group_dist = sim.Pdf(groups, probabilities=[group.fraction for group in groups])

JobGenerator(inter_arrival_time_dist=inter_arrival_time_dist, number_of_tasks_dist=number_of_tasks_dist,
    group_dist=group_dist, duration_dist=duration_dist)

animation()
env.run(100000)
plant.print_statistics()
plant.print_info()
