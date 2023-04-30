import salabim as sim
import pytest


def test_store_filter():
    env = sim.Environment()

    # component that holds an integer value
    class MyComponent(sim.Component):
        def __init__(self, value: int, *args, **kwargs):
            sim.Component.__init__(self, *args, **kwargs)
            self.value: int = value

    # generate 10 components and put them into store my_store
    my_store = sim.Store()
    for my_component in [MyComponent(value=i) for i in range(10)]:
        my_component.enter(my_store)

    # processor shall find a specific component
    class Processor(sim.Component):
        def __init__(self, find_value: int, *args, **kwargs):
            sim.Component.__init__(self, *args, **kwargs)
            self.result: int = None
            self.find_value: int = find_value

        def process(self):
            found_component = yield self.from_store(
                my_store, 
                filter=lambda item: item.value == self.find_value
            )
            self.result = found_component.value

    # component with value 20 is not in the store s
    my_processor = Processor(find_value=20)
    env.run(1)
    assert my_processor.result is None

    # 0 is the first one
    my_processor = Processor(find_value=0)
    env.run(1)
    assert my_processor.result == 0

    # 0 is not in the store anymore
    my_processor = Processor(find_value=0)
    env.run(1)
    assert my_processor.result is None

    # find a component in the center of the store
    my_processor = Processor(find_value=5)
    env.run(1)
    assert my_processor.result == 5

    # 5 is not in the store anymore
    my_processor = Processor(find_value=5)
    env.run(1)
    assert my_processor.result is None


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
