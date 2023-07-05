import salabim as sim
import pytest


def test_queue_iter():
    env = sim.Environment()
    x = [sim.Component(name="x.") for _ in range(20)]
    q = sim.Queue("q", fill=x[:10])
    collect = []
    for c in q:
        collect.append(c)
        if c == x[5]:
            x[2].leave(q)
            x[3].leave(q)
            x[3].enter(q)
            x[7].priority(q, -1)
            x[11].enter(q)
            x[12].enter(q)
        if c == x[12]:
            x[1].leave(q)
            x[1].enter(q)
            x[13].enter(q)

    assert collect == [x[0], x[1], x[2], x[3], x[4], x[5], x[7], x[6], x[8], x[9], x[3], x[11], x[12], x[1], x[13]]


def test_queue_reversed():
    env = sim.Environment()
    x = [sim.Component(name="x.") for _ in range(20)]
    q = sim.Queue("q", fill=x[:10])
    collect = []
    for c in reversed(q):
        collect.append(c)
        if c == x[5]:
            x[2].leave(q)
            x[3].leave(q)
            x[3].enter(q)
            x[7].priority(q, -1)
            x[11].enter(q)
            x[12].enter(q)
        if c == x[12]:
            x[1].leave(q)
            x[1].enter(q)
            x[13].enter(q)

    assert collect == [x[9], x[8], x[7], x[6], x[5], x[12], x[13], x[1], x[11], x[3], x[4], x[0]]


def test_queue_operations():
    env = sim.Environment()
    x = [sim.Component(name="x.") for _ in range(9)]
    q0 = sim.Queue("q.", fill=x[:6])
    q1 = sim.Queue("q.", fill=x[3:])

    qintersection = q0.intersection(q1)
    qand = q0 & q1
    assert qintersection == qand == x[3:6]
    qdifference = q0.difference(q1)
    qminus = q0 - q1
    assert qdifference == qminus == x[:3]
    qunion = q0.union(q1)
    qplus = q0 + q1
    qor = q0 | q1
    assert qunion == qplus == qor == sim.Queue(fill=x)
    qsymmetric_difference = q0.symmetric_difference(q1)
    qcaret = q0 ^ q1
    qcaretrev = q1 ^ q0
    assert qsymmetric_difference == qcaret == qcaretrev == x[:3] + x[6:]
    qcopy = q0.copy()
    assert qcopy == q0
    q1 = q0.move()
    assert len(q0) == 0
    assert q1 == sim.Queue(fill=x[:6])
    q0.clear()
    assert len(q0) == 0
    q0 = sim.Queue("q.", fill=x[:6])
    q1 = sim.Queue("q.", fill=x[3:])
    q0.extend(q1)
    assert q0 == x


def test_queue_comparisons():
    env = sim.Environment()
    x = [sim.Component(name="x.") for _ in range(9)]
    assert sim.Queue(fill=x[:3]) == sim.Queue(fill=x[:3]) == x[:3]
    assert sim.Queue(fill=x[:3]) == sim.Queue(fill=x[:3]) == set(x[:3])
    assert sim.Queue(fill=x[:3]) <= x
    assert sim.Queue(fill=x[:3]) < x
    assert x >= sim.Queue(fill=x[:3])
    assert x > sim.Queue(fill=x[:3])
    assert not (sim.Queue(fill=x[:3]) >= x)
    assert not (sim.Queue(fill=x[:3]) > x)
    assert not (x <= sim.Queue(fill=x[:3]))
    assert not (x < sim.Queue(fill=x[:3]))
    assert sim.Queue(fill=x[:3]) != sim.Queue(fill=x[2:3])


def test_queue_naming():
    env = sim.Environment()
    q0 = sim.Queue("q.")
    q1 = sim.Queue("q.")
    assert q0.name() == "q.0"
    assert q1.name() == "q.1"
    q0copy = q0.copy()
    assert q0copy.name() == "copy of q.0"
    q0copy.rename("q0copy")
    assert q0copy.name() == "q0copy"


def test_queue_priorities():
    env = sim.Environment()
    x = [sim.Component(name="x.") for _ in range(9)]
    q = sim.Queue("q")

    x[0].enter(q)
    x[1].enter_sorted(q, priority=1)
    x[2].enter(q)
    x[3].enter_sorted(q, priority=-1)
    x[4].enter_at_head(q)
    assert list(q) == [x[4], x[3], x[0], x[1], x[2]]
    assert [c.priority(q) for c in q] == [-1, -1, 0, 1, 1]

    # resort after priority change
    x[0].priority(q, 2)
    assert list(q) == [x[4], x[3], x[1], x[2], x[0]]
    assert [c.priority(q) for c in q] == [-1, -1, 1, 1, 2]


def test_queue_priorities_update():
    env = sim.Environment()
    x = [sim.Component(name="x.") for _ in range(9)]
    q = sim.Queue("q")

    for i, c in enumerate(x):
        c.enter_sorted(q, priority=-i)
    assert list(q) == list(reversed(x))

    for i, c in enumerate(q):
        c.priority(q, -i)
    assert list(q) == x
    
    
def test_queue_capacity():
    class X(sim.Component):
        pass
        
    q0 = sim.Queue('q0')
    q1 = sim.Queue('q1', capacity=4)
    for _ in range(3):
        x = X()
        x.enter(q0)
        x.enter(q1)
    x = X()
    q0.capacity.value = 4
    x.enter(q0)
    x.enter(q1)
    x = X()
    with pytest.raises(sim.QueueFullError):
        x.enter(q0)
    with pytest.raises(sim.QueueFullError):
        x.enter(q1) 
    q0.capacity.value=3
    assert len(q0) == 4
    q0.capacity.value = sim.inf
    x = X()
    x.enter(q0)  
    assert len(q0) == 5
    q2 = q0.copy() 
    q3 = q1.copy(copy_capacity=True)
    x = X()
    with pytest.raises(sim.QueueFullError):
        x.enter(q3)
    q4 = q1 + q1 
    assert q4.capacity.value == sim.inf  
    q5 = q1.move()
    assert q1.capacity.value == 4
    assert q5.capacity.value == sim.inf
    q6 = q1.move(copy_capacity=True)
    assert q1.capacity.value == 4
    assert q6.capacity.value == 4


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
