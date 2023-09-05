import salabim as sim
import time
import PySimpleGUI as sg


class ClientGenerator(sim.Component):
    def process(self):
        while True:
            self.hold(env.Uniform(0, 2 * env.mean_iat))
            Client()


class Client(sim.Component):
    def process(self):
        env.client_count += 1
        if self.env.pause_at_10 and env.client_count % 10 == 0:
            self.env.paused(True)
        self.request(env.servers)
        self.hold(env.Normal(env.mean_service_time, 5), cap_now=True)
        self.release()


def user_handle_event(env, window, event, values):
    env.servers.set_capacity(int(values["-NUMBER-OF-SERVERS-"]))
    env.mean_iat = float(values["-IAT-"])
    env.mean_service_time = float(values["-SERVICE-TIME-"])
    env.pause_at_10 = values["-PAUSE-AT-10-"]


env = sim.Environment(trace=False, datetime0="2023-1-1", time_unit="hours")
# env = sim.Environment(trace=False, time_unit="hours")

env.pause_at_10 = False
env.client_count = 0
env.mean_iat = 5
env.mean_service_time = 15
ClientGenerator()

env.servers = env.Resource(capacity=3)

env.servers.requesters().animate(x=850, y=100, direction="w", title="")
env.servers.claimers().animate(x=950, y=100, direction="n", title="")
env.AnimateText(text=lambda: f"Number of servers={env.servers.capacity()}", x=950, y=50, text_anchor="e", font="calibri")
env.AnimateText(text=lambda: f"Inter arrival time={env.mean_iat}", x=950, y=30, text_anchor="e", font="calibri")
env.AnimateText(text=lambda: f"Service time={env.mean_service_time}", x=950, y=10, text_anchor="e", font="calibri")
env.AnimateText(text=lambda: f"Arrival of client {env.client_count}" if env.client_count else "", x=50, y=10, text_anchor="w", font="calibri")
env.AnimateText(text="Watermark", angle=30, fontsize=100, x=512, y=384, text_anchor="c", visible=lambda: env.ui_window()["-SHOW-WATERMARK-"].get())

env.AnimateMonitor(env.servers.requesters().length, x=50, y=300, width=800, height=100)
env.AnimateMonitor(env.servers.claimers().length, x=50, y=450, width=800, height=100)

env.start_ui(
    elements=[
        [sg.Text("Number of servers", key=""), sg.Input(env.servers.capacity(), key="-NUMBER-OF-SERVERS-", size=(4, 10))],
        [sg.Text("Inter arrival time", key=""), sg.Input(env.mean_iat, key="-IAT-", size=(4, 10))],
        [
            sg.Text("Service time", key=""),
            sg.Slider(range=(1, 30), default_value=env.mean_service_time, expand_x=False, enable_events=False, orientation="horizontal", key="-SERVICE-TIME-"),
        ],
        [sg.HorizontalSeparator()],
        [sg.Checkbox("Pause at each 10th client arrival", False, key="-PAUSE-AT-10-", metadata=[1, 2], enable_events=True)],
        [sg.Checkbox("Show watermark", True, key="-SHOW-WATERMARK-", metadata=[1, 2])],
    ],
    user_handle_event=user_handle_event,
    default_elements=True,
)
env.animate(True)

env.speed(50)
env.show_time(False)
env.paused(True)
try:
    env.run()
except:
    sim.reset()

env.stop_ui()
print("done")
