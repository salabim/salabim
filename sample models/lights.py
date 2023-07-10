import math
import salabim as sim
import enum
import itertools
import collections


class Directions(enum.Enum):  # order is not important
    east = enum.auto()
    north = enum.auto()
    west = enum.auto()
    south = enum.auto()


class Turns(enum.Enum):  # order is important as it drives the turn Pdf
    straight = enum.auto()
    left = enum.auto()
    right = enum.auto()


class Colors(enum.Enum):  # order is important for display of the trafiic lights
    red = enum.auto()
    amber = enum.auto()
    green = enum.auto()


PositionInfo = collections.namedtuple("position_info", "x y angle is_straight")

direction_to_angle = {Directions.east: 0, Directions.north: math.radians(90), Directions.west: math.radians(180), Directions.south: math.radians(270)}
direction_to_color = {Directions.east: "red", Directions.north: "green", Directions.west: "blue", Directions.south: "purple"}
color_to_colorspec = {Colors.green: "lime", Colors.amber: "yellow", Colors.red: "red"}


def rotate(x, y, angle):
    return x * math.cos(angle) - y * math.sin(angle), +x * math.sin(angle) + y * math.cos(angle)


class Claim:
    def __init__(self, xll, yll, xur, yur, vehicle):
        self.xll = xll
        self.yll = yll
        self.xur = xur
        self.yur = yur
        self.vehicle = vehicle
        self.color = (vehicle.color, 50)

    def set(self):
        self.vehicle.claims.append(self)
        claims.add(self)
        if show_claims:
            self.an = sim.AnimateRectangle(spec=(self.xll, self.yll, self.xur, self.yur), fillcolor=self.color)

    def reset(self):
        self.vehicle.claims.remove(self)
        claims.remove(self)
        if show_claims:
            self.an.remove()

    def overlaps(self, claims):
        return any(claim.xll < self.xur and claim.xur > self.xll and claim.yll < self.yur and claim.yur > self.yll for claim in claims)

    def __repr__(self):
        return f"Claim({self.xll:5.1f}, {self.yll:5.1f}, {self.xur:5.1f}, {self.yur:5.1f})"


class Vehicle(sim.Component):
    def position(self, l):

        is_straight = True
        if l <= self.l_start_bend:  # straight before bend
            x = self.xfrom - l
            y = self.yfrom
            angle = 0
            if self.turn == Turns.left and l > self.l_start_bend - length_vehicle / 2:
                is_straight = False  # to prevent deadlocks
        else:
            target_angle = math.radians(-90 if self.turn == Turns.right else 90)
            if l > self.l_end_bend:  # straight after bend
                if self.turn == Turns.right:
                    x = self.xto
                    y = self.yto - (self.l_end - l)
                else:
                    x = self.xto
                    y = self.yto + (self.l_end - l)
                angle = target_angle
            else:  # in the bend
                angle = sim.interpolate(l, self.l_start_bend, self.l_end_bend, 0, target_angle)
                is_straight = False
                if self.turn == Turns.right:
                    x = self.xfrom - self.l_start_bend - self.r * math.sin(-angle)
                    y = self.yfrom + self.r - self.r * math.cos(-angle)
                else:
                    x = self.xfrom - self.l_start_bend + self.r * math.sin(-angle)
                    y = self.yfrom - self.r + self.r * math.cos(-angle)

        x, y = rotate(x, y, angle=direction_to_angle[self.from_direction])
        angle += direction_to_angle[self.from_direction]

        return PositionInfo(x=x, y=y, angle=angle, is_straight=is_straight)

    def claim(self, l):
        position_info = self.position(l)
        xa, ya = rotate(-length_boundary / 2, -width_boundary / 2, angle=position_info.angle)
        xb, yb = rotate(length_boundary / 2, width_boundary / 2, angle=position_info.angle)
        xc, yc = rotate(-length_boundary / 2, width_boundary / 2, angle=position_info.angle)
        xd, yd = rotate(length_boundary / 2, -width_boundary / 2, angle=position_info.angle)
        xa, xb = min(xa, xb, xc, xd), max(xa, xb, xc, xd)
        ya, yb = min(ya, yb, yc, yd), max(ya, yb, yc, yd)
        return Claim(xll=position_info.x + xa, yll=position_info.y + ya, xur=position_info.x + xb, yur=position_info.y + yb, vehicle=self)

    def l_t(self, t):
        return sim.interpolate(t, self.t0, self.t1, self.l - resolution, self.l)

    def x(self, t, xoffset=0, yoffset=0):
        position_info = self.position(self.l_t(t))
        xdis, ydis = rotate(xoffset, yoffset, angle=position_info.angle)
        return position_info.x + xdis

    def y(self, t, xoffset=0, yoffset=0):
        position_info = self.position(self.l_t(t))
        xdis, ydis = rotate(xoffset, yoffset, angle=position_info.angle)
        return position_info.y + ydis

    def angle(self, t):
        return math.degrees(self.position(self.l_t(t)).angle)

    def has_to_stop(self):  # this should (and will) be only called when none of the tryclaims overlaps with claims
        if self.l > border_pos - light_pos:
            if not self.passed_light:
                if tl.light[self.from_direction] in (Colors.amber, Colors.red):
                    return True
                self.passed_light = True
        return False

    def setup(self, from_direction, turn, color, r=5, v=1):
        self.from_direction = from_direction
        self.turn = turn
        self.xfrom = border_pos
        self.yfrom = road_pos
        self.color = color
        self.v = v
        self.r = r  # ***

        if turn == Turns.straight:
            self.l_start_bend = self.l_end_bend = self.l_end = road_length
            self.xto = -border_pos
            self.yto = road_pos
        else:
            arclen = r * math.pi / 2
            if turn == Turns.right:
                self.xto = road_pos
                self.yto = border_pos
            if turn == Turns.left:
                self.xto = -road_pos
                self.yto = -border_pos
            self.l_start_bend = border_pos - self.xto - r
            self.l_end_bend = self.l_start_bend + arclen
            self.l_end = self.l_end_bend + self.l_start_bend

    def process(self):
        self.indicator_frequency = sim.Uniform(1, 2)()
        self.t0 = env.now()
        self.t1 = env.now()
        self.l = 0
        self.claims = []  # can't be a set as the order is important
        self.passed_light = False
        while self.claim(self.l).overlaps(claims):
            self.standby()
        self.claim(self.l).set()
        self.an_vehicle = sim.AnimateRectangle(
            x=self.x,
            y=self.y,
            angle=self.angle,
            spec=(-length_vehicle / 2, -width_vehicle / 2, length_vehicle / 2, width_vehicle / 2),
            linecolor="white",
            linewidth=unit1,
            fillcolor=self.color,
        )
        self.an3d_vehicle0 = sim.Animate3dBox(
            x=self.x, y=self.y, z=0.5, z_angle=self.angle, x_len=length_vehicle, y_len=width_vehicle, z_len=1, z_ref=1, color=self.color, shaded=True
        )
        self.an3d_vehicle1 = sim.Animate3dBox(
            x=self.x, y=self.y, z=1.5, z_angle=self.angle, x_len=length_vehicle * 0.6, y_len=width_vehicle, z_len=1, z_ref=1, color=self.color, shaded=True
        )

        if self.turn in (Turns.left, Turns.right):
            self.an_indicator = sim.AnimateRectangle(
                spec=(-2.5, -1, -2, -0.5) if self.turn == Turns.left else (-2.5, 0.5, -2, 1),
                visible=lambda arg, t: (t / env.speed() % arg.indicator_frequency < arg.indicator_frequency / 2) and (self.l_t(t) < self.l_end_bend),
                angle=self.angle,
                x=self.x,
                y=self.y,
                arg=self,
            )

            self.an3d_indicator = sim.Animate3dBox(
                x_len=0.5,
                y_len=0.5,
                z_len=0.5,
                x=lambda arg, t: arg.x(t, xoffset=-length_vehicle / 2, yoffset=-width_vehicle / 2 if self.turn == Turns.left else width_vehicle / 2),
                y=lambda arg, t: arg.y(t, xoffset=-length_vehicle / 2, yoffset=-width_vehicle / 2 if self.turn == Turns.left else width_vehicle / 2),
                z=1.5,
                color="yellow",
                visible=lambda arg, t: (t / env.speed() % arg.indicator_frequency < arg.indicator_frequency / 2) and (self.l_t(t) < self.l_end_bend),
                arg=self,
            )

        while self.l <= self.l_end:
            if len(self.claims) == 1:
                self.tryclaims = [self.claim(self.l + resolution)]
                for i in itertools.count(2):
                    if self.position(self.l + i * resolution).is_straight:
                        break
                    self.tryclaims.append(self.claim(self.l + i))

                while any(claim.overlaps(claims - set(self.claims)) for claim in self.tryclaims) or self.has_to_stop():
                    self.standby()

                for claim in self.tryclaims:
                    claim.set()

            dt = resolution / self.v
            self.t0, self.t1 = self.env.now(), self.env.now() + dt
            self.l += resolution

            self.hold(dt)

            self.claims[0].reset()
        for claim in self.claims:
            claim.reset()
        self.an_vehicle.remove()
        self.an3d_vehicle0.remove()
        self.an3d_vehicle1.remove()

        if self.turn in (Turns.right, Turns.left):
            self.an_indicator.remove()
            self.an3d_indicator.remove()


class TrafficLight(sim.Component):
    def setup(self):
        self.light = {}
        for direction, angle in direction_to_angle.items():
            self.light[direction] = Colors.red
            for distance, this_color in enumerate(Colors):
                x, y = rotate(light_pos1 + distance, 2.2 * road_pos, angle=angle)
                an = sim.AnimateCircle(
                    radius=0.4,
                    x=x,
                    y=y,
                    fillcolor=lambda arg, t: color_to_colorspec[arg.this_color] if self.light[arg.direction] == arg.this_color else "50%gray",
                )
                an.direction = direction
                an.this_color = this_color
                x, y = rotate(light_pos1, 2.2 * road_pos, angle=angle)
                an = sim.Animate3dSphere(
                    radius=0.4,
                    x=x,
                    y=y,
                    z=2.5 - distance,
                    color=lambda arg, t: color_to_colorspec[arg.this_color] if self.light[arg.direction] == arg.this_color else "50%gray",
                )
                an.direction = direction
                an.this_color = this_color

    def process(self):
        while True:
            for lightWE, lightNS, duration in (
                (Colors.red, Colors.red, red_red_duration),
                (Colors.green, Colors.red, red_green_duration),
                (Colors.amber, Colors.red, red_amber_duration),
                (Colors.red, Colors.red, red_red_duration),
                (Colors.red, Colors.green, red_green_duration),
                (Colors.red, Colors.amber, red_amber_duration),
            ):

                self.light[Directions.east] = self.light[Directions.west] = lightWE
                self.light[Directions.north] = self.light[Directions.south] = lightNS
                self.hold(duration)


class VehicleGenerator(sim.Component):
    def setup(self, from_direction, color):
        self.from_direction = from_direction
        self.color = color

    def process(self):
        while True:
            turn = sim.Pdf(Turns, (50, 25, 25))()
            v = sim.Uniform(0.5, 1.5)()
            r = 5
            Vehicle(from_direction=self.from_direction, turn=turn, color=self.color, v=v)
            self.hold(sim.Exponential(50))


env = sim.Environment()
size = 768
env.speed(8)
env.background_color("black")
env.width3d(size)
env.height3d(size)
env.position3d((0, 0))
env.width(size)
env.height(size)
env.position((size + 10, 0))
env.view(x_eye=-39.748112339561004, y_eye=-78.01006285162117, z_eye=55.71822276394165, x_center=0, y_center=0, z_center=0, field_of_view_y=45)

length_vehicle = 5
width_vehicle = 2
length_boundary = length_vehicle + 1
width_boundary = width_vehicle + 0.5

road_length = 100
road_inter_distance = 4
light_pos = 10

red_red_duration = 3
red_green_duration = 30
red_amber_duration = 3

resolution = 1
show_claims = True
do_animation = True

border_pos = road_length / 2 + length_vehicle
road_pos = road_inter_distance / 2

env.x0(-road_length / 2)
env.x1(road_length / 2)
env.y0(-road_length / 2)
unit1 = road_length / env.width()

claims = set()

y_road_left = road_pos
y_road_right = -road_pos
x_road_up = road_pos
x_road_down = -road_pos

light_pos1 = light_pos - length_boundary / 2 - resolution

y_text = env.height() - 80
sim.AnimateText("Lights!", x=12, y=y_text, screen_coordinates=True, textcolor="white", font="mono", fontsize=30)
sim.AnimateCircle(radius=6, x=39, y=y_text + 30, fillcolor=lambda: color_to_colorspec[tl.light[Directions.west]], linewidth=0, screen_coordinates=True)
sim.AnimateCircle(radius=6, x=129, y=y_text + 5, fillcolor=lambda: color_to_colorspec[tl.light[Directions.north]], linewidth=0, screen_coordinates=True)
sim.AnimateText("powered by salabim", x=12, y=y_text - 9, screen_coordinates=True, font="narrow", textcolor="white", fontsize=14, text_anchor="w")

with sim.over3d():
    sim.AnimateText("Lights!", x=12, y=y_text, screen_coordinates=True, textcolor="white", font="mono", fontsize=30)
    sim.AnimateCircle(radius=6, x=39, y=y_text + 30, fillcolor=lambda: color_to_colorspec[tl.light[Directions.west]], linewidth=0, screen_coordinates=True)
    sim.AnimateCircle(radius=6, x=129, y=y_text + 5, fillcolor=lambda: color_to_colorspec[tl.light[Directions.north]], linewidth=0, screen_coordinates=True)
    sim.AnimateText("powered by salabim", x=12, y=y_text - 9, screen_coordinates=True, font="narrow", textcolor="white", fontsize=14, text_anchor="w")


road_color = "30%gray"

for direction in Directions:
    for sign in (-1, 1):
        x0, y0 = rotate(road_length / 2, sign * y_road_left * 0.1, angle=direction_to_angle[direction])
        x1, y1 = rotate(light_pos1, sign * y_road_left * 1.9, angle=direction_to_angle[direction])
        sim.AnimateRectangle(spec=(x0, y0, x1, y1), linewidth=0, fillcolor=road_color)
        sim.Animate3dRectangle(x0=x0, y0=y0, x1=x1, y1=y1, color=road_color)

tl = TrafficLight()

for direction in Directions:
    VehicleGenerator(from_direction=direction, color=direction_to_color[direction])

make_video=False
if make_video:
    type_of_video = "2d"
    env.run(100)
    env.camera_auto_print(True)
    env.camera_move("""
    view(x_eye=-39.7481,y_eye=-78.0101,z_eye=55.7182,x_center=0.0000,y_center=0.0000,z_center=0.0000,field_of_view_y=45.0000)  # t=0.0000
    view(x_eye=-38.3806,y_eye=-78.6919)  # t=121.3576
    view(x_eye=-37.0014,y_eye=-79.3497)  # t=126.4277
    view(x_eye=-35.6109,y_eye=-79.9834)  # t=131.7427
    view(x_eye=-34.2096,y_eye=-80.5927)  # t=136.4638
    view(x_eye=-32.7978,y_eye=-81.1775)  # t=142.0032
    view(x_eye=-29.5181,y_eye=-73.0597,z_eye=50.1464)  # t=156.5674
    view(x_eye=-26.5662,y_eye=-65.7538,z_eye=45.1318)  # t=160.4352
    view(x_eye=-23.9096,y_eye=-59.1784,z_eye=40.6186)  # t=165.6155
    view(x_eye=-21.5187,y_eye=-53.2605,z_eye=36.5567)  # t=170.2758
    view(x_eye=-22.4449,y_eye=-52.8769)  # t=181.6538
    view(x_eye=-22.4449,y_eye=-52.8769,z_eye=32.9011)  # t=193.5282
    view(x_eye=-22.4449,y_eye=-52.8769,z_eye=29.6109)  # t=196.9527
    view(x_eye=-22.4449,y_eye=-52.8769,z_eye=26.6499)  # t=200.3144
    view(x_eye=-22.4449,y_eye=-52.8769,z_eye=23.9849)  # t=205.0026
    view(x_eye=-23.3643,y_eye=-52.4771)  # t=220.9797
    view(x_eye=-24.2766,y_eye=-52.0614)  # t=225.3774
    view(x_eye=-25.1815,y_eye=-51.6297)  # t=229.2660
    view(x_eye=-26.0787,y_eye=-51.1824)  # t=233.2356
    view(x_eye=-26.9680,y_eye=-50.7195)  # t=233.5740
    view(x_eye=-27.8491,y_eye=-50.2411)  # t=233.9580
    view(x_eye=-28.7217,y_eye=-49.7474)  # t=233.9580
    view(x_eye=-29.5855,y_eye=-49.2386)  # t=234.5815
    view(x_eye=-30.4403,y_eye=-48.7147)  # t=234.5815
    view(x_eye=-31.2859,y_eye=-48.1760)  # t=234.5815
    view(x_eye=-32.1219,y_eye=-47.6227)  # t=235.2451
    view(x_eye=-32.9482,y_eye=-47.0548)  # t=235.2451
    view(x_eye=-33.7644,y_eye=-46.4726)  # t=235.2451
    view(x_eye=-34.5703,y_eye=-45.8763)  # t=236.0126
    view(x_eye=-35.3657,y_eye=-45.2660)  # t=236.0126
    view(x_eye=-36.1503,y_eye=-44.6419)  # t=236.5163
    view(x_eye=-36.9239,y_eye=-44.0042)  # t=236.5163
    view(x_eye=-37.6862,y_eye=-43.3530)  # t=237.1800
    view(x_eye=-38.4371,y_eye=-42.6887)  # t=237.1800
    view(x_eye=-39.1763,y_eye=-42.0114)  # t=237.6837
    view(x_eye=-39.9035,y_eye=-41.3213)  # t=237.6837
    view(x_eye=-40.6186,y_eye=-40.6186)  # t=237.6837
    view(x_eye=-41.3213,y_eye=-39.9035)  # t=238.5312
    view(x_eye=-42.0114,y_eye=-39.1763)  # t=238.5312
    view(x_eye=-42.6887,y_eye=-38.4371)  # t=238.5312
    view(x_eye=-43.3530,y_eye=-37.6862)  # t=239.2829
    view(x_eye=-44.0042,y_eye=-36.9239)  # t=239.2829
    view(x_eye=-44.6419,y_eye=-36.1503)  # t=239.2829
    view(x_eye=-45.2660,y_eye=-35.3657)  # t=240.0583
    view(x_eye=-45.8763,y_eye=-34.5703)  # t=240.0583
    view(x_eye=-46.4726,y_eye=-33.7644)  # t=240.0583
    view(x_eye=-47.0548,y_eye=-32.9482)  # t=240.0583
    view(x_eye=-47.6227,y_eye=-32.1219)  # t=240.9858
    view(x_eye=-48.1760,y_eye=-31.2859)  # t=240.9858
    view(x_eye=-48.7147,y_eye=-30.4403)  # t=240.9858
    view(x_eye=-49.2386,y_eye=-29.5855)  # t=241.9852
    view(x_eye=-49.7474,y_eye=-28.7217)  # t=241.9852
    view(x_eye=-50.2411,y_eye=-27.8491)  # t=241.9852
    view(x_eye=-50.7195,y_eye=-26.9680)  # t=241.9852
    view(x_eye=-51.1824,y_eye=-26.0787)  # t=241.9852
    """, lag=3)
    env.show_fps(True)
    env.animate("?")
    env.animate3d("?")
    env.video_mode(type_of_video)
    env.video_repeat(0)
    env.video_pingpong(False)
    env.video(f"lights {type_of_video}.gif")
    env.run(till=300)
    env.video_close()
else:
    env.animate(True)
    env.animate3d(True)
    env.run()