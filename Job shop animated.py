import salabim as sim

def animation():
    env.animation_parameters(synced=False, modelname='Job shop', background_color='20%gray')
    
    max_len = 0
    for i, group in enumerate(groups):
        x = i * 70 + 100 + 2
        y = env.height() - 140 + 20
        sim.AnimateText(text=group.name(), x=x, y=y, text_anchor='sw', fontsize=12)
        for j, machine in enumerate(group.machines):
            sim.AnimateRectangle(spec=(0,0,60,12), x=x, y=y - 20  - j * 15,
                fillcolor=lambda machine, t: machine.group.color if machine.task else (machine.group.color,100),
                textcolor='white',
                text=lambda machine, t: machine.task.name() if machine.task else '',
                arg=machine)
            
        max_len = max(max_len, len(group.machines))
        
    env.y_top = y - max_len * 15 - 15
    sim.AnimateLine(spec=(0, env.y_top, 2000, env.y_top))
    sim.AnimateText(text='job', x=50, y=env.y_top - 15, text_anchor='ne', fontsize=12)
    sim.AnimateText(text='slack', x=90, y=env.y_top - 15, text_anchor='ne', fontsize=12)

class Group(sim.Component):
    def setup(self, job_select_method, fraction, number_of_machines, color):
        if job_select_method.lower() == 'fifo':
            self.job_select = self.job_select_fifo
        elif job_select_method.lower() == 'min_slack':
            self.job_select = self.job_select_min_slack
        else:
            raise AssertionError('wrong selection_method:', job_select_method)
        self.machines = [Machine(group=self, name=self.name() + '.') for _ in range(number_of_machines)]

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
            self.task = job.tasks.head()
            self.task.machine = self
            self.task.start_execution = env.now()
            yield self.hold(self.task.duration)
            self.task.leave(job.tasks)
            self.task.an_bar.remove()

            if job.tasks:
                task1 = job.tasks.head()
                job.enter(task1.group.jobs)
                if task1.group.idle_machines:
                    task1.group.idle_machines.head().activate()
            else:
                for ao in (job.an_due, job.an_slack, job.an_label, job.an_execute, job.an_tasks):
                    ao.remove()
                job.leave(plant)


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
        self.an_slack = sim.AnimateText(x=90, y=self.y,
            text=lambda job,t:'{:7.2f}'.format(job.slack_t(t)),
            textcolor=lambda job,t: 'white' if job.slack_t(t)<0 else '50%gray',
            fontsize=12, text_anchor='se', arg=self)
        self.an_label = sim.AnimateText(text=str(self.sequence_number()),
            x=50, y=self.y,
            fontsize=12, text_anchor='se')
        self.an_execute = sim.AnimateRectangle(spec=(0,0,72,12),
            x=100, y=self.y,
            fillcolor=lambda job, t: '' if job.tasks[0].start_execution is None else job.tasks[0].group.color,
            text=lambda job,t: '' if job.tasks[0].start_execution is None else job.tasks[0].machine.name(),
            textcolor='white', text_anchor='sw', arg=self)
        self.an_due = sim.AnimateLine(spec=(0,-1, 0, 13),
            x=lambda job,t: 200 + job.due_t(t) * scale_x, y=self.y,
            layer = -1,
            arg=self)
        self.an_tasks = sim.AnimateQueue(queue=self.tasks,
            x=200,
            y = self.y,
            direction='e',
            arg=self)
        self.enter(self.tasks[0].group.jobs)
        if self.tasks.head().group.idle_machines:
            self.tasks.head().group.idle_machines.head().activate()
        self.enter(plant)

    def y(self, t):
        return env.y_top - 45 - self.index(plant) * 15
        
    def due_t(self, t):
        due_t = self.slack_t(t)
        for task in self.tasks:
            if task.start_execution is None:
                due_t += task.duration
            else:
                due_t += task.duration - (t - task.start_execution)
        return due_t  
        
    def slack_t(self, t):
        task1 = self.tasks.head()

        if self in task1.group.jobs:
            return self.slack - (t - self.enter_time(task1.group.jobs))
        else:
            return self.slack

class Task(sim.Component):
    def setup(self, job_generator, job):
        self.group = job_generator.group_dist()
        self.duration = job_generator.duration_dist()
        self.start_execution = None
        self.an_bar = sim.Animate(rectangle0=(0, 0, 0, 0))
        
    def animation_objects(self):
        ao0 = sim.AnimateRectangle(
           spec=lambda task,t: (0,0, (task.duration - (0 if task.start_execution is None else (t-task.start_execution))) * scale_x, 12),
           fillcolor=lambda task, t: (task.group.color, 80) if task.start_execution is None else task.group.color,
           arg=self)
        return lambda task,t: (task.duration - (0 if task.start_execution is None else (t-task.start_execution))) * scale_x, 0, ao0
       

sim.reset()
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

scale_x = 1

animation()
env.run(100000)

plant.print_statistics()
plant.print_info()
