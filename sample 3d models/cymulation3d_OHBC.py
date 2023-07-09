import salabim as sim
import math
from ycecream import yc
from pathlib import Path
import functools

yc.show_line_number = True
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut

MAX_CONTAINERS_IN_PILE = 8
SLACK_HEIGHT = 1  # space between top container and container in flight

CONTAINER_WIDTH = 2.5
CONTAINER_HEIGHT = 2.5
CHASSIS_HEIGHT = 1.5

BAR_WIDTH = 1
BAR_WIDTH1 = 0.5

BRIDGE_SIZE_X = 4
BRIDGE_SIZE_Y = 26

PORTALWIDTH = 26.5
PORTALHEIGHT = MAX_CONTAINERS_IN_PILE * CONTAINER_HEIGHT + SLACK_HEIGHT + 3
SIDELENGTH = 15
TROLLEYLENGTH = SIDELENGTH - BAR_WIDTH
TROLLEYWIDTH = 2.4
TROLLEYHEIGHT = 2.5

Z_RAIL = 25


class Row:
    def __init__(self, x, function):
        self.x = x
        self.function = function

    def __repr__(self):
        return f"Row(x={self.x:5.1f}, function={self.function})"


def logical_to_world(block, slot, row):
    x = block.x + row.x
    y = block.y + (4 - slot) * inter_slot / 2
    return x, y


def logical_height_to_z(height):
    if height == "top":
        return MAX_CONTAINERS_IN_PILE * CONTAINER_HEIGHT + CONTAINER_HEIGHT + SLACK_HEIGHT
    if height == "chassis":
        return CHASSIS_HEIGHT + CONTAINER_HEIGHT
    return height * CONTAINER_HEIGHT


def lva_to_t(l, v, a):
    l = abs(l)
    if l < v * v / a:
        t = 2 * math.sqrt(l / a)
    else:
        t = (l / v) + (v / a)
    return t


def container_rectangle(z, length):
    y0 = TEU_width / 2
    x0 = (TEU_length * length / 20) / 2
    y1 = y0 * 0.4
    x1 = x0 * 0.4
    return sim.interpolate(z, z_top, z_bottom, (-x0, -y0, x0, y0), (-x1, -y1, x1, y1))


class AnimateOHBC(sim.Animate3dBase):
    def setup(self, x0, y0, z_angle=0, trolley_pos=0, spreader_height=15, spreader_length=12.2, upper=True):
        self.x0 = x0
        self.y0 = y0
        self.z_angle = z_angle
        self.trolley_pos = trolley_pos
        self.spreader_height = spreader_height
        self.spreader_length = spreader_length

        self.register_dynamic_attributes("x0 y0 z_angle trolley_pos spreader_height spreader_length")
        self.upper = upper

    def draw(self, t):
        self.gl_color = env.colorspec_to_gl_color("50%gray")
        self.gl_trolley_color = env.colorspec_to_gl_color("80%gray")
        gl.glPushMatrix()

        gl.glTranslate(self.x0(t), self.y0(t), 0)
        gl.glRotate(self.z_angle(t), 0.0, 0.0, 1.0)
        self.draw_bridge(self.upper, t)
        #        self.draw_top(t)
        self.draw_spreader(t)

        gl.glPopMatrix()

    def draw_bridge(self, upper, t):
        l = 30
        w = 5
        if upper:
            z0 = Z_RAIL
            z1 = Z_RAIL + 3
        else:
            z0 = Z_RAIL
            z1 = Z_RAIL - 3
        for y in (-0.5 * w, 0.5 * w):
            sim.draw_bar3d(x0=-0.5 * l, y0=y, z0=z0, x1=0.5 * l, y1=y, z1=z0, bar_width=0.5, gl_color=self.gl_color)
            sim.draw_bar3d(x0=-0.4 * l, y0=y, z0=z1, x1=0.4 * l, y1=y, z1=z1, bar_width=0.5, gl_color=self.gl_color)

            sim.draw_bar3d(x0=-0.5 * l, y0=y, z0=z0, x1=-0.4 * l, y1=y, z1=z1, bar_width=0.5, gl_color=self.gl_color)
            sim.draw_bar3d(x0=-0.4 * l, y0=y, z0=z1, x1=-0.3 * l, y1=y, z1=z0, bar_width=0.5, gl_color=self.gl_color)

            sim.draw_bar3d(x0=-0.3 * l, y0=y, z0=z0, x1=-0.2 * l, y1=y, z1=z1, bar_width=0.5, gl_color=self.gl_color)
            sim.draw_bar3d(x0=-0.2 * l, y0=y, z0=z1, x1=-0.1 * l, y1=y, z1=z0, bar_width=0.5, gl_color=self.gl_color)

            sim.draw_bar3d(x0=-0.1 * l, y0=y, z0=z0, x1=-0.0 * l, y1=y, z1=z1, bar_width=0.5, gl_color=self.gl_color)
            sim.draw_bar3d(x0=-0.0 * l, y0=y, z0=z1, x1=0.1 * l, y1=y, z1=z0, bar_width=0.5, gl_color=self.gl_color)

            sim.draw_bar3d(x0=0.1 * l, y0=y, z0=z0, x1=0.2 * l, y1=y, z1=z1, bar_width=0.5, gl_color=self.gl_color)
            sim.draw_bar3d(x0=0.2 * l, y0=y, z0=z1, x1=0.3 * l, y1=y, z1=z0, bar_width=0.5, gl_color=self.gl_color)

            sim.draw_bar3d(x0=0.3 * l, y0=y, z0=z0, x1=0.4 * l, y1=y, z1=z1, bar_width=0.5, gl_color=self.gl_color)
            sim.draw_bar3d(x0=0.4 * l, y0=y, z0=z1, x1=0.5 * l, y1=y, z1=z0, bar_width=0.5, gl_color=self.gl_color)

        sim.draw_bar3d(x0=-0.5 * l, y0=-0.5 * w, z0=z0, x1=-0.5 * l, y1=0.5 * w, z1=z0, bar_width=0.5, gl_color=self.gl_color)
        sim.draw_bar3d(x0=0.5 * l, y0=-0.5 * w, z0=z0, x1=0.5 * l, y1=0.5 * w, z1=z0, bar_width=0.5, gl_color=self.gl_color)
        sim.draw_bar3d(x0=-0.4 * l, y0=-0.5 * w, z0=z1, x1=-0.4 * l, y1=0.5 * w, z1=z1, bar_width=0.5, gl_color=self.gl_color)
        sim.draw_bar3d(x0=0.4 * l, y0=-0.5 * w, z0=z1, x1=0.4 * l, y1=0.5 * w, z1=z1, bar_width=0.5, gl_color=self.gl_color)

    def draw_spreader(self, t):

        sim.draw_box3d(
            x_len=self.spreader_length(t),
            y_len=BAR_WIDTH1,
            z_len=BAR_WIDTH1,
            x=self.trolley_pos(t),
            y=TROLLEYWIDTH / 2,
            z=self.spreader_height(t),
            z_ref=1,
            gl_color=self.gl_trolley_color,
        )
        sim.draw_box3d(
            x_len=self.spreader_length(t),
            y_len=BAR_WIDTH1,
            z_len=BAR_WIDTH1,
            x=self.trolley_pos(t),
            y=-TROLLEYWIDTH / 2,
            z=self.spreader_height(t),
            z_ref=1,
            gl_color=self.gl_trolley_color,
        )

        sim.draw_box3d(
            x_len=BAR_WIDTH1,
            y_len=TROLLEYWIDTH,
            z_len=BAR_WIDTH1,
            x=self.trolley_pos(t) - self.spreader_length(t) / 2,
            y=0,
            z=self.spreader_height(t),
            z_ref=1,
            gl_color=self.gl_trolley_color,
        )
        sim.draw_box3d(
            x_len=BAR_WIDTH1,
            y_len=TROLLEYWIDTH,
            z_len=BAR_WIDTH1,
            x=self.trolley_pos(t) + self.spreader_length(t) / 2,
            y=0,
            z=self.spreader_height(t),
            z_ref=1,
            gl_color=self.gl_trolley_color,
        )


class AnimateChassis(sim.Animate3dBase):
    def setup(self, animate_route):
        self.animate_route = animate_route
        self.register_dynamic_attributes("x y z_angle")
        self.gl_color = self.env.colorspec_to_gl_color("orange")

    def x(self, t):
        return self.animate_route.x(t)

    def y(self, t):
        return self.animate_route.y(t)

    def z_angle(self, t):
        return self.animate_route.angle(t)

    def draw(self, t):
        sim.draw_box3d(
            x_len=14, y_len=2.5, z_len=0.5, x=self.x(t), y=self.y(t), z=CHASSIS_HEIGHT, z_angle=self.z_angle(t), z_ref=-1, gl_color=self.gl_color, shaded=True
        )


class Task(object):
    def __init__(self, t, v):
        self.t = t
        self.v = v


def getv(tasks, t, interpolate):
    while len(tasks) > 1:
        if tasks[1].t < t:
            del tasks[0]
        else:
            break
    i1 = 1 if len(tasks) > 1 else 0

    if interpolate:
        return sim.interpolate(t, tasks[0].t, tasks[i1].t, tasks[0].v, tasks[i1].v)
    else:
        return tasks[0].v


class AnimateGantry(sim.Animate):
    def __init__(self, ohbc, *arg, **kwargs):
        self.ohbc = ohbc
        x, _ = logical_to_world(ohbc.block, ohbc.slot, ohbc.row)
        self.ymid = ohbc.block.y  # + PORTALWIDTH / 2

        sim.Animate.__init__(self, rectangle0=(-gantry_width / 2, 0, gantry_width / 2, PORTALWIDTH), y0=ohbc.y, fillcolor0="", linewidth0=1)

    def x(self, t):
        return getv(self.ohbc.tasksx, t, True)


class AnimateTrolley(sim.Animate):
    def __init__(self, ohbc, *arg, **kwargs):
        self.ohbc = ohbc
        sim.Animate.__init__(self, rectangle0=(-trolleylength / 2, -trolleywidth / 2, trolleylength / 2, trolleywidth / 2), fillcolor0="", linewidth0=0.5)

    def x(self, t):
        return getv(self.ohbc.tasksx, t, True)

    def y(self, t):
        return getv(self.ohbc.tasksy, t, True)


class AnimateSpreader(sim.Animate):
    def __init__(self, ohbc, *arg, **kwargs):
        self.ohbc = ohbc
        sim.Animate.__init__(self, rectangle0="", linewidth0=0.5)

    def x(self, t):
        return getv(self.ohbc.tasksx, t, True)

    def y(self, t):
        return getv(self.ohbc.tasksy, t, True)

    def z(self, t):
        return getv(self.ohbc.tasksz, t, True)

    def rectangle(self, t):
        return container_rectangle(getv(self.ohbc.tasksz, t, True), getv(self.ohbc.taskslength, t, False))

    def fillcolor(self, t):
        if getv(self.ohbc.taskshascontainer, t, False):
            return "red"
        else:
            return ""


class Container(sim.Component):
    def x(self, t):
        if isinstance(self.equipment, OHBC):
            return self.equipment.ao.x0(t)
        elif isinstance(self.equipment, Truck):
            return self.equipment.ao.x(t)
        else:
            return self.x_now

    def y(self, t):
        if isinstance(self.equipment, OHBC):
            return self.equipment.ao.y0(t) + self.equipment.ao.trolley_pos(t)
        elif isinstance(self.equipment, Truck):
            return self.equipment.ao.y(t)
        else:
            return self.y_now

    def z(self, t):
        if isinstance(self.equipment, OHBC):
            return self.equipment.ao.spreader_height(t)
        elif isinstance(self.equipment, Truck):
            return CHASSIS_HEIGHT + CONTAINER_HEIGHT
        else:
            return self.z_now

    def z_angle(self, t):
        if isinstance(self.equipment, OHBC):
            return 0
        elif isinstance(self.equipment, Truck):
            return self.equipment.ao.angle(t) + 90
        else:
            return 0

    def setup(self, length=40, color="lime", edge_color="", equipment=None, x_now=0, y_now=0, z_now=0, angle=0, slot=None, row=None, height=None):
        self.length = length
        self.color = color
        self.edge_color = edge_color
        self.equipment = equipment
        self.x_now = x_now
        self.y_now = y_now
        self.z_now = z_now
        self.angle = angle
        self.slot = slot
        self.row = row
        self.height = height
        self.ao = AnimateContainer(length=length, x=self.x, y=self.y, z=self.z, z_ref=-1, z_angle=self.z_angle, color=color, edge_color=edge_color)


class AnimateContainer(sim.Animate3dBox):
    def __init__(self, length, x=0, y=0, z=0, z_angle=0, z_ref=1, color="red", edge_color="white"):
        super().__init__(
            x_len=CONTAINER_WIDTH,
            y_len=length * 12.2 / 40,
            z_len=CONTAINER_HEIGHT,
            x=x,
            y=y,
            z=z,
            z_angle=z_angle,
            x_ref=0,
            y_ref=0,
            z_ref=z_ref,
            color=color,
            edge_color=edge_color,
            shaded=True,
        )


class OHBC(sim.Component):
    def setup(self, id, upper, block):
        self.id = id
        self.upper = upper
        self.block = block
        if self.upper:
            self.row = rows[0]
        else:
            self.row = rows[5]
        self.slot = 1
        self.height = "top"
        self.hascontainer = False
        self.orderqueue = sim.Queue()
        self.preorderqueue = sim.Queue()

        self.y = block.y
        x, y = logical_to_world(self.block, self.slot, self.row)
        z = logical_height_to_z(self.height)
        if do_animate:

            self.tasksx = [Task(0, x)]
            self.tasksy = [Task(0, y)]
            self.tasksz = [Task(0, z)]
            self.taskshascontainer = [Task(0, False)]
            self.taskslength = [Task(0, 40)]

            self.ao_gantry = AnimateGantry(self)
            self.ao_trolley = AnimateTrolley(self)
            self.ao_spreader = AnimateSpreader(self)

        if do_animate3d:
            self.ao = AnimateOHBC(
                upper=self.upper,
                x0=lambda arg, t: arg.ao_gantry.x(t),
                y0=self.ao_gantry.ymid,
                z_angle=90,
                trolley_pos=lambda arg, t: arg.ao_trolley.y(t) - arg.ao_gantry.ymid,
                spreader_height=lambda arg, t: arg.ao_spreader.z(t),
                arg=self,
            )

    def get(self, slot, row, height):
        x, y = logical_to_world(self.block, self.slot, self.row)
        z = logical_height_to_z(self.height)

        xto, yto = logical_to_world(self.block, slot, row)
        zto = logical_height_to_z(height)
        ta = env.now()
        tx = lva_to_t(x - xto, vx, ax)
        if do_animate:
            self.tasksx.append(Task(ta, x))
            self.tasksx.append(Task(ta + tx, xto))
        ty = lva_to_t(y - yto, vy, ay)
        if do_animate:
            self.tasksy.append(Task(ta, y))
            self.tasksy.append(Task(ta + ty, yto))
        ta = ta + max(tx, ty)
        if do_animate:
            self.tasksx.append(Task(ta, xto))
            self.tasksy.append(Task(ta, yto))

            self.tasksz.append(Task(ta, z))
        tz = lva_to_t(z - zto, vz, az)
        ta = ta + tz
        if do_animate:
            self.tasksz.append(Task(ta, zto))
        t_transfer = ta
        ta = ta + t_connect
        if do_animate:
            self.tasksz.append(Task(ta, zto))
            self.taskshascontainer.append(Task(ta, True))
        tz = lva_to_t(zto - z, vz, az)
        ta = ta + tz
        if do_animate:
            self.tasksz.append(Task(ta, z))

        self.row = row
        self.slot = slot
        self.hascontainer = True

        return ta, t_transfer

    def put(self, slot, row, height):
        xto, yto = logical_to_world(self.block, slot, row)
        zto = logical_height_to_z(height)
        x, y = logical_to_world(self.block, self.slot, self.row)
        z = logical_height_to_z(self.height)
        ta = env.now()
        tx = lva_to_t(x - xto, vx, ax)
        if do_animate:
            self.tasksx.append(Task(ta, x))
            self.tasksx.append(Task(ta + tx, xto))
        ty = lva_to_t(y - yto, vy, ay)
        if do_animate:
            self.tasksy.append(Task(ta, y))
            self.tasksy.append(Task(ta + ty, yto))
        ta = ta + max(tx, ty)
        if do_animate:
            self.tasksx.append(Task(ta, xto))
            self.tasksy.append(Task(ta, yto))

            self.tasksz.append(Task(ta, z))
        tz = lva_to_t(z - zto, vz, az)
        ta = ta + tz
        if do_animate:
            self.tasksz.append(Task(ta, zto))
        t_transfer = ta
        ta = ta + t_disconnect
        if do_animate:
            self.tasksz.append(Task(ta, zto))
            self.taskshascontainer.append(Task(ta, False))
        tz = lva_to_t(zto - z, vz, az)
        ta = ta + tz
        if do_animate:
            self.tasksz.append(Task(ta, z))

        self.row = row
        self.slot = slot
        self.hascontainer = False

        return ta, t_transfer

    def move(self, slot, row):
        x, y = logical_to_world(self.block, self.slot, self.row)
        z = logical_height_to_z(self.height)
        xto, yto = logical_to_world(self.block, slot, row)
        zto = z
        ta = env.now()
        tx = lva_to_t(x - xto, vx, ax)
        if do_animate:
            self.tasksx.append(Task(ta, x))
            self.tasksx.append(Task(ta + tx, xto))
        ty = lva_to_t(y - yto, vy, ay)
        if do_animate:
            self.tasksy.append(Task(ta, y))
            self.tasksy.append(Task(ta + ty, yto))
        ta = ta + max(tx, ty)
        if do_animate:
            self.tasksx.append(Task(ta, xto))
            self.tasksy.append(Task(ta, yto))

        self.row = row
        self.slot = slot

        return ta

    def process(self):
        self.pre_positioned = False
        while True:
            if self.orderqueue:
                min_distance = 10000000
                order = None
                for search_order in self.orderqueue:
                    this_distance = abs(search_order.fromslot - self.slot)
                    if this_distance < min_distance:
                        order = search_order
                        min_distance = this_distance

                t_finish, t_transfer = self.get(order.fromslot, order.fromrow, order.fromheight)

                self.hold(till=t_transfer)
                if order.type_ == "in":
                    order.truck.container.equipment = self
                else:
                    order.truck.container.equipment = self
                    self.block.pile[order.fromslot, order.fromrow].remove(order.truck.container)

                self.hold(till=t_finish)
                if order.type_ == "in":
                    order.truck.activate()
                t_finish, t_transfer = self.put(order.toslot, order.torow, order.toheight)
                self.hold(till=t_transfer)
                if order.type_ == "in":
                    order.truck.container.equipment = None
                    order.truck.container.x_now, order.truck.container.y_now = logical_to_world(self.block, order.toslot, order.torow)
                    order.truck.container.z_now = logical_height_to_z(order.toheight)
                    self.block.pile[order.toslot, order.torow].append(order.truck.container)
                else:
                    order.truck.container.equipment = order.truck

                self.hold(till=t_finish)

                if order.type_ == "out":
                    order.truck.activate()

                order.leave(self.orderqueue)
                self.pre_positioned = False
            else:
                if self.preorderqueue and not self.pre_positioned:
                    order = self.preorderqueue[0]  # goto location of first preorder in order_queue
                    t = self.move(order.fromslot, order.fromrow)
                    self.hold(till=t)
                    self.pre_positioned = True
                else:
                    self.passivate()


class Block:
    def __init__(self, id, x, y, enabled):
        self.id = id
        self.x = x
        self.y = y
        self.enabled = enabled

        self.orders = []
        self.pile = {}
        for slot in slots:
            for row in rows:
                self.pile[slot, row] = []

        xa, ya = logical_to_world(self, slot=slots[-1], row=rows[0])
        xb, yb = logical_to_world(self, slot=slots[0], row=rows[-1])

        x0 = xa - 2.5
        y0 = ya - 2.5
        x1 = xb + 2.5
        y1 = yb + 2.5

        if self.enabled:
            color = "20%gray"
        else:
            color = "10%gray"
        sim.AnimateRectangle(spec=(x0, y0, x1, y1), linewidth=0, fillcolor=color)

        sim.Animate3dRectangle(x0=x0, y0=y0, x1=x1, y1=y1, color=color)
        if self.enabled:
            sim.Animate3dBar(x0=x0, y0=y0 - 2, x1=x1, y1=y0 - 2, z0=Z_RAIL, z1=Z_RAIL, bar_width=0.5, color="white")
            sim.Animate3dBar(x0=x0, y0=y1 + 2, x1=x1, y1=y1 + 2, z0=Z_RAIL, z1=Z_RAIL, bar_width=0.5, color="white")

        if self.enabled:
            self.ohbcs = (OHBC(id=id, upper=True, block=self), OHBC(id=id, upper=False, block=self))
            print(id)
            self.ohbc = self.ohbcs[int(id) % 2]  # *** just to get going]

    def __repr__(self):
        return f"Block(id= {self.id} x={self.x:5.1f}, y={self.y:5.1f} enabled={self.enabled})"


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point({str(self.x)}, {str(self.y)})"


class Segment:
    def __init__(self, p0, p1):
        self.p0 = p0
        self.p1 = p1
        self._length = math.sqrt((self.p0.x - self.p1.x) ** 2 + (self.p0.y - self.p1.y) ** 2)
        try:
            self._angle = math.atan((self.p0.y - self.p1.y) / (self.p0.x - self.p1.x)) * 180 / math.pi
        except ZeroDivisionError:
            self._angle = 90

    def length(self):
        return self._length

    def __repr__(self):
        return f"Segment({str(self.p0)}, {str(self.p1)})"

    def angle(self):
        return self._angle


class Route:
    def __init__(self, segments):
        self.segments = segments
        self._length = sum(segment.length() for segment in self.segments)

    def length(self):
        return self._length

    def __repr__(self):
        return f"Route({', '.join(str(segment) for segment in self.segments)})"


class AnimateRoute(sim.AnimateRectangle):
    def l_done(self, t):
        t_done = t - self.tstart
        return min(t_done * self.v, self.route.length())

    def current_segment(self, t):
        l = 0
        for segment in self.route.segments:
            if l + segment.length() > self.l_done(t):
                return segment
            l += segment.length()

        return segment

    def current_point(self, t):
        l = 0
        for segment in self.route.segments:
            if l + segment.length() > self.l_done(t):
                break
            l += segment.length()
        else:
            l -= segment.length()

        l_done_on_segment = self.l_done(t) - l

        x = sim.interpolate(l_done_on_segment, 0, segment.length(), segment.p0.x, segment.p1.x)
        y = sim.interpolate(l_done_on_segment, 0, segment.length(), segment.p0.y, segment.p1.y)
        return Point(x, y)

    def x(self, t):
        return self.current_point(t).x

    def y(self, t):
        return self.current_point(t).y

    def angle(self, t):
        return self.current_segment(t).angle()

    def __init__(self, route, v, *args, **kwargs):
        self.route = route
        self.v = v
        self.tstart = env.now()
        kwargs["linewidth"] = 1
        kwargs["linecolor"] = "white"
        super().__init__(*args, **kwargs)


def get_target_position(type_):
    if type_ == "in":
        length = sim.CumPdf((20, 40), (40, 100))()
        while True:
            block = sim.Pdf(enabled_blocks, 1)()
            if length == 20:
                slot = sim.Pdf((1, 3, 5, 7))()
            else:
                slot = sim.Pdf((2, 6))()
            row = sim.Pdf(buffer_rows, 1)()
            #            height = len(block.pile[slot, row]) + 1
            height = sim.IntUniform(1, 5)()
            break  # check for maximum height
        color = sim.Pdf(colors, 1)()
        container = Container(length=length, color=color)
        return (block, slot, row, height, length, color, container)
    else:
        block = sim.Pdf(enabled_blocks, 1)()
        while True:
            container = sim.Pdf(block.containers, 1)()
            slot = container.slot
            row = container.row
            container = block.pile[slot, row][-1]  # top of this pile
            if container in block.containers:
                break  # it is possible that the top container is not anymore in containers, so retry
        length = container.length
        height = container.height
        color = container.color
        block.containers.remove(container)
        return (block, slot, row, height, length, color, container)


class Truck(sim.Component):
    def setup(self, order, position, v):
        self.order = order
        self.position = position
        self.v = v

    def process(self):
        x, y = logical_to_world(self.order.block, self.order.slot, self.order.row)
        p0 = self.position
        p1 = Point(truck_row1.x, p0.y)
        p2 = Point(truck_row1.x, self.order.block.y)
        p3 = Point(truck_row1.x, self.order.block.y)
        s0 = Segment(p0, p1)
        s1 = Segment(p1, p2)
        s2 = Segment(p2, p3)

        self.container = self.order.container
        route = Route((s0, s1, s2))
        if self.order.type_ == "in":
            fillcolor = "red"
            #            self.container = Container(length=self.order.length, color=self.order.color)
            self.container.equipment = self
        else:
            fillcolor = ""

        order = sim.Component()
        order.type_ = self.order.type_
        if order.type_ == "in":
            order.fromrow = truck_row1
            order.fromslot = 4  # self.order.slot
            order.fromheight = "chassis"
            order.torow = self.order.row
            order.toslot = self.order.slot
            order.toheight = self.order.height
            order.length = self.order.length
        else:
            order.fromrow = self.order.row
            order.fromslot = self.order.slot
            order.fromheight = self.order.height
            order.torow = truck_row1
            order.toslot = 4  # self.order.slot
            order.toheight = "chassis"
            order.length = self.order.length
        order.enter(self.order.block.ohbc.preorderqueue)
        if self.order.block.ohbc.ispassive():
            self.order.block.ohbc.activate()
        duration = route.length() / self.v
        if do_animate:
            self.ao = AnimateRoute(route=route, v=self.v, spec=(-7, -1.25, 7, 1.25), fillcolor=fillcolor)
            self.ao3d = AnimateChassis(animate_route=self.ao)
        self.hold(duration)
        order.leave(self.order.block.ohbc.preorderqueue)
        order.enter(self.order.block.ohbc.orderqueue)
        if self.order.block.ohbc.ispassive():
            self.order.block.ohbc.activate()

        order.truck = self
        self.passivate()
        p0 = Point(truck_row1.x, self.order.block.y)
        p1 = Point(truck_row1.x, 0)
        s0 = Segment(p0, p1)
        route = Route((s0,))

        if self.order.type_ == "out":
            fillcolor = "red"
        else:
            fillcolor = ""

        duration = route.length() / self.v
        if do_animate:
            self.ao.remove()
            self.ao = AnimateRoute(route=route, v=self.v, spec=(-7, -1.25, 7, 1.25), fillcolor=fillcolor)
            self.ao3d.animate_route = self.ao
        self.hold(duration)
        if do_animate:
            self.ao.remove()
            self.ao3d.remove()
            if order.type_ == "out":
                self.container.ao.remove()

        env.n_trucks += 1


class TruckOrder:
    def __init__(self, block, slot, row, height, type_, length, color, container):
        self.block = block
        self.slot = slot
        self.row = row
        self.height = height
        self.type_ = type_
        self.length = length
        self.color = color
        self.container = container

    def __repr__(self):
        return f"TruckOrder({self.block.id}, {self.slot:2d}, {self.row}, {self.type_}, {self.length}, {self.color})"


class Source(sim.Component):
    def setup(self, position, iat, type_, v):
        self.position = position
        self.iat = iat
        self.type_ = type_
        self.v = v
        sim.AnimateCircle(radius=5, x=position.x, y=position.y, fillcolor="orange")

    def process(self):
        while True:
            self.hold(self.iat)

            type_ = self.type_()
            block, slot, row, height, length, color, container = get_target_position(type_)
            order = TruckOrder(block, slot, row, height, type_, length, color, container)
            Truck(order=order, position=self.position, v=self.v)


class QC(sim.Component):
    def process(self):
        while True:
            self.hold(qc_iat)

            type_ = qc_type()
            block, slot, row, height, length, color, container = get_target_position()
            order = TruckOrder(block, slot, row, height, type_, length, color, container)
            Truck(order=order, position=Point(xqc, yqc))


env = sim.Environment(trace=False)

do_animate = True
do_animate3d = True


env.x0(0)
env.x1(380)
env.y0(0)

env.width3d(950)
env.height3d(768)
env.position3d((0, 0))
env.background_color("black")
env.width(950)
env.height(768)
env.position((960, 100))

if Path("Upward Systems logo horizontal reverse.gif").is_file():
    sim.Animate(
        text="cymulation",
        x0=env.width() + 10,
        y0=env.height() - 78,
        font="Cabin Sketch",
        fontsize0=60,
        text_anchor="se",
        textcolor0="dark turquoise",
        screen_coordinates=True,
    )
    sim.Animate(
        text="container yard simulation",
        x0=env.width() + 2,
        y0=env.height() - 88,
        font="Cabin Sketch",
        fontsize0=22,
        text_anchor="se",
        textcolor0="dark turquoise",
        screen_coordinates=True,
    )

    #    sim.Animate(image="salabim logo red white 200.png", x0=env.width(), y0=env.height() - 89, width0=150, anchor="ne", screen_coordinates=True)
    sim.Animate(image="Upward Systems logo horizontal reverse.gif", x0=env.width() + 4, y0=env.height() - 89, width0=200, anchor="ne", screen_coordinates=True)


env.n_trucks = 0
n_rows_per_block = 7
n_TEUslots_per_block = 24
max_height = 5

inter_row = 3
inter_slot = 6.5

gantry_width = 15
ohbc_width = 10
trolleywidth = 4
trolleylength = 15
TEU_width = 2.5
TEU_length = 6.25

z_top = logical_height_to_z("top")
z_bottom = logical_height_to_z(1)

vx = 4
ax = 0.35
vy = 1.33
ay = 0.25
vz = 1.5
az = 0.35

slots = {20: [1, 3, 5, 7], 40: [2, 6]}
rows = []
buffer_rows = []
available_rows = []
x = 2
for _ in range(6):
    rows.append(Row(x=x, function="repair"))
    x += 4
for _ in range(6):
    rows.append(Row(x=x, function="cleaning"))
    x += 4
for _ in range(22):
    rows.append(Row(x=x, function="buffer"))
    buffer_rows.append(rows[-1])
    x += 4
x += 10
truck_row1 = Row(x=x, function="truck_row1")
x += 10
for _ in range(46):
    rows.append(Row(x=x, function="available"))
    available_rows.append(rows[-1])
    x += 2.7
x + 10
truck_row2 = Row(x=x, function="truck_row2")
yc(truck_row1)
yc(rows)

slots = (1, 2, 3, 4, 5, 6, 7)

t_connect = 10
t_disconnect = 10


gate_iat = sim.Uniform(30, 90)
gate_type = sim.CumPdf(("in", 50, "out", 100))

qc_iat = sim.Uniform(30, 90)
qc_type = sim.CumPdf(("in", 100, "out", 100))

v_external_trucks = 5
v_internal_trucks = 5

Source(position=Point(truck_row1.x, 500), iat=sim.Uniform(60, 180), type_=sim.CumPdf(("in", 50, "out", 100)), v=v_external_trucks)
# Source(position=Point(100, 30), iat=sim.Uniform(60, 180), type_=sim.CumPdf(("in", 50, "out", 100)), v=v_external_trucks)
# Source(position=Point(200, 220), iat=sim.Uniform(60, 180), type_=sim.CumPdf(("in", 100, "out", 100)), v=v_internal_trucks)
# ource(position=Point(300, 225), iat=sim.Uniform(60, 180), type_=sim.CumPdf(("in", 0, "out", 100)), v=v_internal_trucks)

n_blocks = 7

BLOCK_SIZE_Y = BRIDGE_SIZE_Y + 5


y = 40
x = 0

blocks = []
enabled_blocks = []
for iblock in range(n_blocks):
    block = Block(id=f"{iblock}", x=x, y=y + (iblock + 0.5) * BLOCK_SIZE_Y, enabled=iblock >= 4)
    blocks.append(block)
    if block.enabled:
        enabled_blocks.append(block)

for row in (truck_row1, truck_row2):
    xroad, _ = logical_to_world(blocks[0], slot=slots[-1], row=row)
    yc(xroad)
    sim.AnimateLine(spec=(xroad, 0, xroad, 1000), linewidth=0.5, linecolor="red")
    sim.Animate3dLine(x0=xroad, y0=0, x1=xroad, y1=1000, color="red")

env.view(x_eye=152.4121810628927, y_eye=119.16179982924429, z_eye=84.92336955333289, x_center=90, y_center=200, z_center=0, field_of_view_y=45)

colors = "red blue green lime yellow violet indigo maroon".split()
color1 = env.colorspec_to_tuple("blue")

colors = "cyan cornflowerblue cadetblue darkturquoise dodgerblue red green blue yellow purple lightgreen white".split()

for block in blocks:
    if block.enabled:
        block.containers = []
        for row in rows:
            if row.function == "available":
                slots_to_use_dis = sim.Pdf(((1, 3, 5, 7), 10, (1, 3, 6), 20, (2, 5, 7), 10, (2, 6), 60))
                pile_height_dis = sim.Pdf((0, 1, 2, 3, 4, 5, 6, 7, 8), (140, 20, 10, 5, 5, 5, 5, 5, 5))
            if row.function == "buffer":
                slots_to_use_dis = sim.Pdf(((1, 3, 5, 7), 10, (1, 3, 6), 20, (2, 5, 7), 10, (2, 6), 60))
                pile_height_dis = sim.Pdf((0, 1, 2, 3, 4, 5), (140, 20, 10, 5, 5, 5))

            if row.function in ("cleaning", "repair"):
                slots_to_use_dis = sim.Pdf(((4,), 80, (3, 5), 20))
                pile_height_dis = sim.Pdf((0, 1), (50, 50))

            for islot in slots_to_use_dis():
                pile_height = pile_height_dis()
                x, y = logical_to_world(block, islot, row)
                length = 20 if islot % 2 else 40
                pile_colors = sim.Pdf(colors, 1)(n=pile_height)
                if row.function == "available":
                    pile_colors = pile_height * ["red"]
                for height, color in enumerate(pile_colors, 1):
                    z = logical_height_to_z(height)
                    container = Container(
                        length=length, color=color, edge_color="", equipment=None, x_now=x, y_now=y, z_now=z, slot=islot, row=row, height=height
                    )
                    block.containers.append(container)
                    block.pile[islot, row].append(container)

env.animate(do_animate)
env.animate3d(do_animate3d)
env.show_fps(True)
env.show_camera_position()

env.run()

sim.Animate3dGrid(x_range=range(0, 401, 100), y_range=range(0, 301, 100))


env.speed(20)

make_video = False
if make_video:
    env.run(120)
    env.video("cymulation3d.mp4")
    env.run(400)
    env.video_close()
else:
    env.run(3600 * 24 * 365)
