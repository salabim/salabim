"""
This is an animation of the movement of all NS trains on 5 January 2022.
It is not an ordinary discrete event simulation as the event time and
the movements are read from a (sorted) csv file.

Instead of making an animation circle for every train movement, we reuse the
animation of object.

The 'tricky' part is ion the projection of the coordinates into the projection of the map
of the Netherlands.

Requires:
    salabim >= 24.0.0
    24_hours_train_gps_7_jan_2022.csv
    map-netherlands.jpg
"""

import salabim as sim
import csv
import datetime

start = datetime.datetime.strptime("2022-01-05 04:00:00", "%Y-%m-%d %H:%M:%S")

X_LONGITUDE_4_AT_Y_0 = 195
X_LONGITUDE_4_AT_T_1200 = 218
X_LONGITUDE_7_AT_Y_0 = 876
X_LONGITUDE_7_AT_Y_1200 = 855
Y_LATTITUDE_51 = 103
Y_LATTITUDE_53 = 817


def long_lat_to_xy(long, lat):
    y = sim.interpolate(lat, 51, 53, Y_LATTITUDE_51, Y_LATTITUDE_53)
    x_0 = sim.interpolate(long, 4, 7, X_LONGITUDE_4_AT_Y_0, X_LONGITUDE_7_AT_Y_0)
    x_1200 = sim.interpolate(long, 4, 7, X_LONGITUDE_4_AT_T_1200, X_LONGITUDE_7_AT_Y_1200)
    x = sim.interpolate(y, 0, 1200, x_0, x_1200)
    return x, y


class ShowMovements(sim.Component):
    def process(self):
        ans = [sim.AnimateCircle(2, x=-1) for _ in range(500)]  # start invisible (x=-1 is out of the screen)

        with open("24_hours_train_gps_7_jan_2022.csv", "r") as f:
            reader = csv.DictReader(f)
            ans_iter = iter(ans)
            last_t = 0
            for row in reader:
                t = (datetime.datetime.strptime(row["time"][:-1] + "0", "%Y-%m-%d %H:%M:%S") - start).total_seconds()
                an = next(ans_iter)
                an.x, an.y = long_lat_to_xy(long=float(row[" long"]), lat=float(row[" lat"]))

                if t != last_t:
                    for an in ans_iter:  # set remaining ans to invisible
                        if an.x == -1:
                            break
                        an.x = -1

                    self.hold(till=last_t)
                    last_t = t
                    ans_iter = iter(ans)


env = sim.Environment(animate=True, height=1000, width=975, x1=975)

env.show_time(False)

sim.AnimateImage("map-netherlands.jpg", y=-40, screen_coordinates=True)
sim.AnimateText(text=lambda: (start + datetime.timedelta(seconds=env.t())).strftime("%Y-%m-%d %H:%M:%S"), x=40, y=890, font="calibri", fontsize=30)
sim.AnimateText("Actual NS train movements", x=40, y=920, font="calibri", fontsize=30)

ShowMovements()  # this is the actual simulation code (just one component!)

env.speed(400)  # runs 400 times real time
env.run()
