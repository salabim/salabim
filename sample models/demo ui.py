import salabim as sim

sim.yieldless(True)
import PySimpleGUI as sg


class ClientGenerator(sim.Component):
    def process(self):
        while True:
            Client()
            self.hold(env.Uniform(0, 2 * env.mean_iat))


class Client(sim.Component):
    def process(self):
        self.request(env.servers)
        self.hold(env.Normal(env.mean_service_time, 5), cap_now=True)
        self.release()


def user_handle_event(env, window, event, values):
    env.servers.set_capacity(int(values["-NUMBER-OF-SERVERS-"]))
    env.mean_iat = float(values["-IAT-"])
    env.mean_service_time = float(values["-SERVICE-TIME-"])


env = sim.Environment(trace=False)

env.mean_iat = 2
env.mean_service_time = 15
ClientGenerator()

env.servers = env.Resource(capacity=3)

env.servers.requesters().animate(x=850, y=100, direction="w", title="")
env.servers.claimers().animate(x=950, y=100, direction="n", title="")
env.AnimateText(text=lambda: f"Number of servers={env.servers.capacity()}", x=950, y=50, text_anchor="e", font="calibri")
env.AnimateText(text=lambda: f"Inter arrival time={env.mean_iat}", x=950, y=30, text_anchor="e", font="calibri")
env.AnimateText(text=lambda: f"Service time={env.mean_service_time}", x=950, y=10, text_anchor="e", font="calibri")
env.AnimateText(text="Watermark", angle=30, fontsize=100, x=512, y=384, text_anchor="c", visible=lambda: env.ui_window()["-SHOW-WATERMARK-"].get())


env.start_ui(
    window_size=(400, 650),
    window_position=(1200, 100),
    actions=[
        [sg.Text("Number of servers", key=""), sg.Input(env.servers.capacity(), key="-NUMBER-OF-SERVERS-", size=(4, 10))],
        [sg.Text("Inter arrival time", key=""), sg.Input(env.mean_iat, key="-IAT-", size=(4, 10))],
        [
            sg.Text("Service time", key=""),
            sg.Slider(range=(1, 30), default_value=env.mean_service_time, expand_x=True, enable_events=False, orientation="horizontal", key="-SERVICE-TIME-"),
        ],
        [sg.Checkbox("Show watermark", True, key="-SHOW-WATERMARK-", metadata=[1, 2])],  # metadata=[1,2] means that this checkbox is always shown
    ],
    user_handle_event=user_handle_event,
)

env.animate(True)
env.paused(True)


try:
    env.run(10)
    env.trace(True)
    env.run()
except:
    sim.reset()

env.stop_ui()
print("done")
