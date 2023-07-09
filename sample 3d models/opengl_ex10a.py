"""
OpenGL experiment in Python take x

try to experiment with perspectives / lookats etc


version 0.10a (fifty dots experiment)

history
0.1   initial version
0.2   containers
0.3   fields and sea
0.4   camera xxx
0.5   box_to_vertices
0.6   draws cables, trolley and spreader
      at correct position
0.7   tank
0.8   various
0.9   now computes camera pos / direction / angles
      from camera viewpoint with / without glulookat
      camera forward/backward/left/right/up/down
      turn left / right / up / down
      roll camera anti clockwise / clockwise
0.10  and now for real

"""

import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu

import math
import datetime

# import fiftydots
from ycecream import yc

ESCAPE = b"\x1b"


SEALEVEL = -0.2
FIELDLEVEL = -0.1

window = 0

camera = None


clGREEN = (0.0, 0.3, 0.05)
clDARKGREEN = (0.0, 0.2, 0.02)
clBLUE = (0.0, 0.0, 0.5)
clDARKBLUE = (0.0, 0.0, 0.35)
clRED = (0.7, 0, 0)
clDARKRED = (0.25, 0, 0)
clDARKGREY = (0.2, 0.2, 0.2)


def cross(u, v):
    return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]


def dot(u, v):
    return sum(x * y for x, y in zip(u, v))


def dot3(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


class Camera:
    def __init__(self):
        self.fovy = 50
        self.modelview_matrix = None
        self.direction = None
        self.right = None
        self.up = None

    def setperspective(self):
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(self.fovy, glut.glutGet(glut.GLUT_WINDOW_WIDTH) / glut.glutGet(glut.GLUT_WINDOW_HEIGHT), 0.1, 1000.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def reset(self):
        glu.gluLookAt(-20.0, -20.0, 20.0, 30.0, 30.0, 0.0, 0, 0, 1)  # eye  # center  # up

        self.modelview_matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)

    def load_modelviewmatrix(self):
        self.modelview_matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)

    """ zoom out """

    def increase_fovy(self):
        self.fovy += 1

    """ zoom in """

    def decrease_fovy(self):
        self.fovy -= 1

    def turn_left_right(self, d):
        modelview_matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        gl.glLoadIdentity()
        gl.glRotate(d, 0, 1, 0)
        gl.glMultMatrixf(modelview_matrix)

    def turn_up_down(self, d):
        modelview_matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        gl.glLoadIdentity()
        gl.glRotate(d, 1, 0, 0)
        gl.glMultMatrixf(modelview_matrix)

    def roll(self, d):
        modelview_matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        gl.glLoadIdentity()
        gl.glRotate(d, 0, 0, 1)
        gl.glMultMatrixf(modelview_matrix)

    """ move forward """

    def forward(self, d):  # d = distance: negative is backward
        modelview_matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)

        direction = [modelview_matrix[0][2], modelview_matrix[1][2], modelview_matrix[2][2]]

        gl.glTranslate(d * direction[0], d * direction[1], d * direction[2])


def InitGL(Width, Height):

    gl.glClearColor(0.0, 0.0, 0.0, 0.0)
    gl.glClearDepth(1.0)
    gl.glDepthFunc(gl.GL_LESS)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glShadeModel(gl.GL_SMOOTH)

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    glu.gluPerspective(50.0, glut.glutGet(glut.GLUT_WINDOW_WIDTH) / glut.glutGet(glut.GLUT_WINDOW_HEIGHT), 0.1, 1000.0)

    print(gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX))

    #    glPushMatrix()
    #    gl.glLoadIdentity()
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()

    camera.reset()

    print("InitGL")
    camera.load_modelviewmatrix()
    yc(camera.modelview_matrix)


def key_pressed(*args):
    special_keys = glut.glutGetModifiers()
    alt_active = glut.GLUT_ACTIVE_ALT & special_keys
    shift_active = glut.GLUT_ACTIVE_SHIFT & special_keys
    ctrl_active = glut.GLUT_ACTIVE_CTRL & special_keys

    key = args[0]
    print("***", key)
    if key == ESCAPE:
        glut.glutLeaveMainLoop()
    elif key == b"o":
        camera.increase_fovy()
    elif key == b"O":
        camera.decrease_fovy()

    elif key == b"f":  # +x
        camera.forward(d=1)
    elif key == b"F":  # -x
        camera.forward(d=-1)

    elif key == b"y":  # +y
        camera.forward(d=1)
    elif key == b"Y":  # -y
        camera.forward(d=-1)

    elif key == b"z":  # +z
        camera.move(0, 0, 1)
    elif key == b"Z":  # -z
        camera.move(0, 0, -1)

    elif key == b"a":  # roll x-as
        camera.rotate_a()
    elif key == b"A":  # -z
        camera.rotate(-1, 0, 0)

    elif key == glut.GLUT_KEY_LEFT:
        print("key left")
        if ctrl_active:
            camera.turn_left_right(-1)
        elif shift_active:
            camera.roll(-1)

    elif key == glut.GLUT_KEY_RIGHT:
        print("key right")
        if ctrl_active:
            camera.turn_left_right(1)
        elif shift_active:
            camera.roll(1)

    elif key == glut.GLUT_KEY_UP:
        print("key up")
        if ctrl_active:
            camera.turn_up_down(1)
        else:
            camera.forward(d=1)

    elif key == glut.GLUT_KEY_DOWN:
        print("key down")
        if ctrl_active:
            camera.turn_up_down(-1)
        else:
            camera.forward(d=-1)

    matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)

    yc(matrix)


def mouse_wheel_rolled(button, dir, x, y):
    yc(button, dir, x, y)
    if dir > 0:
        camera.forward(1)
    else:
        camera.forward(-1)


def emptystack(x0, y0, z0):
    grid = fiftydots.grid("salabim 3d", default=" ", intra=1, proportional=True, width=None, align="c", narrow=True)
    c_max = len(grid[0])
    r_max = len(grid)
    yc(c_max, r_max)
    for r in range(1, r_max - 2):
        level = r_max - r
        for c in range(c_max):
            yc(r,c)
            if grid[r][c]:
                cilindercolor = (0.2, 0.2, 0.2)
            else:
                cilindercolor = (1, 1, 1)
            tankcontainer(
                length=6,
                width=2.40,
                height=2.55,
                x0=x0,
                y0=y0 - c * 2.40,
                z0=z0 + (r_max - 1 - r) * 2.55,
                xa=0,
                ya=0,
                za=0,
                cilindercolor=cilindercolor,
                framecolor=clDARKRED,
            )


def create_lights():
    SunPos = (0, -100, 100, 1)
    AmbiPos = (0.1, 0.1, 0.1, 1)
    gl.glEnable(gl.GL_LIGHTING)
    gl.glLightModelfv(gl.GL_LIGHT_MODEL_AMBIENT, (0.42, 0.42, 0.42, 1))

    gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (-1, -1.2, 1, 0))
    """ x, y,z = direction w = distance 0 = inf, 1 = at a point """
    # glLightfv(GL_LIGHT1, GL_AMBIENT, (0.1,0.1,0.1,1))
    # glLightfv(GL_LIGHT2, GL_DIFFUSE, (0.1,0.1,0.1,0))

    gl.glEnable(gl.GL_LIGHT0)
    # glEnable(GL_LIGHT1);
    # glEnable(GL_LIGHT2);


def cilinder(length, width, n, x0=0, y0=0, z0=0, xa=0, ya=0, za=0, color=(0.25, 0.25, 0.25)):

    assert n >= 4

    step_angle = 360 / n

    if n % 2 == 0:
        start_angle = step_angle / 2
    else:
        start_angle = 0

    radius = 0.5 * width / math.cos((step_angle / 2) * math.pi / 180.0)
    two_d_vertices = []
    for i in range(n):
        angle = (i * step_angle + start_angle) * (math.pi / 180.0)
        two_d_vertices.append((radius * math.cos(angle), radius * math.sin(angle)))

    #    print(two_d_vertices)

    gl.glPushMatrix()

    gl.glTranslate(x0, y0, z0)

    gl.glRotate(xa, 1.0, 0.0, 0.0)
    gl.glRotate(ya, 0.0, 1.0, 0.0)
    gl.glRotate(za, 0.0, 0.0, 1.0)

    gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, color)

    length05 = length / 2

    """ draw front """
    gl.glBegin(gl.GL_TRIANGLE_FAN)
    gl.glNormal3f(-1, 0, 0)
    for i in [*range(n), 0]:
        gl.glVertex3f(-length05, two_d_vertices[i][0], two_d_vertices[i][1])
    gl.glEnd()

    """ draw back """
    gl.glBegin(gl.GL_TRIANGLE_FAN)
    gl.glNormal3f(1, 0, 0)
    for i in [*range(n), 0]:
        gl.glVertex3f(length05, two_d_vertices[i][0], two_d_vertices[i][1])
    gl.glEnd()

    """ draw sides """
    gl.glBegin(gl.GL_QUADS)
    for i in range(n):
        a1 = (start_angle + (i + 0.5) * step_angle) * (math.pi / 180.0)
        gl.glNormal3f(0, math.cos(a1), math.sin(a1))
        gl.glVertex3f(-length05, *two_d_vertices[i])
        gl.glVertex3f(length05, *two_d_vertices[i])
        gl.glVertex3f(length05, *two_d_vertices[(i + 1) % n])
        gl.glVertex3f(-length05, *two_d_vertices[(i + 1) % n])
    gl.glEnd()

    gl.glPopMatrix()


def tankcontainer(length, width, height, x0=0, y0=0, z0=0, xa=0, ya=0, za=0, cilindercolor=(0.25, 0.25, 0.25), framecolor=clBLUE):

    """
    top and bottom rails
    if top z_ref = -1 else 1
    """

    def rails(l, w, h, color):
        """
        left, right, front, rear
        """
        d = 0.1
        w2 = w * 0.5
        l2 = l * 0.5
        if h == 0:
            zr = 1
        else:
            zr = -1

        """ left """
        box(length, d, d, x0=-l2, y0=-w2, z0=h, x_ref=1, y_ref=1, z_ref=zr, color=framecolor)

        """ right """
        box(length, d, d, x0=-l2, y0=w2, z0=h, x_ref=1, y_ref=-1, z_ref=zr, color=framecolor)

        """ front """
        box(d, width, d, x0=-l2, y0=-w2, z0=h, x_ref=1, y_ref=1, z_ref=zr, color=framecolor)

        """ rear """
        box(d, width, d, x0=l2, y0=-w2, z0=h, x_ref=1, y_ref=1, z_ref=zr, color=framecolor)

    gl.glPushMatrix()

    gl.glTranslate(x0, y0, z0)
    gl.glRotate(xa, 1.0, 0.0, 0.0)
    gl.glRotate(ya, 0.0, 1.0, 0.0)
    gl.glRotate(za, 0.0, 0.0, 1.0)

    cilinder(length=length - 0.1, width=width - 0.1, n=8, x0=0, y0=0, z0=height / 2, xa=0, ya=0, za=0, color=cilindercolor)

    """ bottom """
    # Box(length, width, 0.1,
    #     x0=0, y0=0, z0=0,
    #     xa=0, ya=0, za=0,
    #     z_ref=1,
    #     color = framecolor).draw()

    length05 = length / 2
    width05 = width / 2

    box(
        len_x=0.1,
        len_y=0.1,
        len_z=height,
        x0=-length05,
        y0=-width05,
        z0=0,
        # xa=0, ya=0, za=0,
        x_ref=1,
        y_ref=1,
        z_ref=1,
        color=framecolor,
    )

    box(
        len_x=0.1,
        len_y=0.1,
        len_z=height,
        x0=length05,
        y0=-width05,
        z0=0,
        # xa=0, ya=0, za=0,
        x_ref=-1,
        y_ref=1,
        z_ref=1,
        color=framecolor,
    )

    box(
        len_x=0.1,
        len_y=0.1,
        len_z=height,
        x0=-length05,
        y0=width05,
        z0=0,
        # xa=0, ya=0, za=0,
        x_ref=1,
        y_ref=-1,
        z_ref=1,
        color=framecolor,
    )

    box(
        len_x=0.1,
        len_y=0.1,
        len_z=height,
        x0=length05,
        y0=width05,
        z0=0,
        # xa=0, ya=0, za=0,
        x_ref=-1,
        y_ref=-1,
        z_ref=1,
        color=framecolor,
    )

    rails(l=length, w=width, h=height, color=framecolor)
    rails(l=length, w=width, h=0, color=framecolor)

    gl.glPopMatrix()


def drawcube(l, w, h, x0, y0, z0, xa, ya, za, color):  # from Pascal/Delphi

    l2 = 0.5 * l
    w2 = 0.5 * w
    h2 = 0.5 * w
    gl.glPushMatrix()

    #    glRotatef(45.0, 0.0, 0.0, 1.0)

    gl.glTranslate(x0, y0, z0)

    gl.glRotate(xa, 1.0, 0.0, 0.0)
    gl.glRotate(ya, 0.0, 1.0, 0.0)
    gl.glRotate(za, 0.0, 0.0, 1.0)

    #    glColor3fv(color)
    gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, color)

    gl.glBegin(gl.GL_QUADS)

    """ bottom z- """
    gl.glNormal3f(0, 0, -1)
    gl.glVertex3f(-l2, -w2, -h2)
    gl.glVertex3f(l2, -w2, -h2)
    gl.glVertex3f(l2, w2, -h2)
    gl.glVertex3f(-l2, w2, -h2)

    """ top z+ """
    gl.glNormal3f(0, 0, 1)
    gl.glVertex3f(-l2, -w2, h2)
    gl.glVertex3f(l2, -w2, h2)
    gl.glVertex3f(l2, w2, h2)
    gl.glVertex3f(-l2, w2, h2)

    """ left y- """
    gl.glNormal3f(0, -1, 0)
    gl.glVertex3f(-l2, -w2, -h2)
    gl.glVertex3f(l2, -w2, -h2)
    gl.glVertex3f(l2, -w2, h2)
    gl.glVertex3f(-l2, -w2, h2)

    """ right y+ """
    gl.glNormal3f(0, 1, 0)
    gl.glVertex3f(-l2, w2, -h2)
    gl.glVertex3f(l2, w2, -h2)
    gl.glVertex3f(l2, w2, h2)
    gl.glVertex3f(-l2, w2, h2)

    """ rear x- """
    gl.glNormal3f(-1, 0, 0)
    gl.glVertex3f(-l2, -w2, -h2)
    gl.glVertex3f(-l2, -w2, h2)
    gl.glVertex3f(-l2, w2, h2)
    gl.glVertex3f(-l2, w2, -h2)

    """ front x+ """
    gl.glNormal3f(1, 0, 0)
    gl.glVertex3f(l2, -w2, -h2)
    gl.glVertex3f(l2, -w2, h2)
    gl.glVertex3f(l2, w2, h2)
    gl.glVertex3f(l2, w2, -h2)

    gl.glEnd()
    gl.glPopMatrix()


def DrawGLScene():
    global camera
    # print(f"{datetime.datetime.now()}")
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    camera.setperspective()

    create_lights()

    gl.glMatrixMode(gl.GL_MODELVIEW)

    draw_sea()
    draw_field()

    tankcontainer(length=6, width=2.40, height=2.55, x0=10, y0=30, z0=0, xa=0, ya=0, za=0, cilindercolor=(0.25, 0.25, 0.25), framecolor=clBLUE)

    for y in range(8):
        for z in range(4):
            tankcontainer(
                length=6,
                width=2.40,
                height=2.55,
                x0=10,
                y0=24 - y * 2.40,
                z0=z * 2.55,
                xa=0,
                ya=0,
                za=0,
                cilindercolor=(0.25, 0.25, 0.25),
                framecolor=clDARKRED,
            )

    # emptystack(48, 130, 0)

    # Draw Cube (multiple quads)

    """
    for i in range(5):
        drawcube(l= 12, w= 2.40, h= 2.55,
                 x0= 30, y0= 10, z0=i*3,
                 xa= 0, ya= 0, za= 0+i*10,
                 color= clDARKGREEN)


    
    box(len_x=10, len_y=10, len_z=10,
        x0=30, y0=0, z0=0,
        xa=0, ya=45, za=0,
        x_ref=0, y_ref=0, z_ref=1,
        color= (0.5, 0.5, 0.5))

    asc = ASC(x0=0, y0=0, z0=0, za=0, spreaderheight = 2.55).draw()

    c1 = Container(0, 10, 0, 0, 45, 0, clBLUE) # 22 degrees round x
    c1.draw()

    c2 = Container(0, 20, 0, 0, 0, 22, clRED)  # 22 degrees round z-axis
    c2.draw()
    
    for i in range(0, 3):
        c = Container(i*15, 0, 0, 0, 0, 0, clRED).draw()
    """

    glut.glutSwapBuffers()


def draw_sea():

    glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, clDARKBLUE)
    #    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, clRED)

    glBegin(gl.GL_QUADS)
    glNormal3f(0, 0, 1)
    # glColor3f(*clDARKBLUE)
    glVertex3f(-1000, -1000, SEALEVEL)
    glVertex3f(1000, -1000, SEALEVEL)
    glVertex3f(1000, 1000, SEALEVEL)
    glVertex3f(-1000, 1000, SEALEVEL)
    glEnd()


def draw_sea():

    box(len_x=2000, len_y=2000, len_z=0.2, x0=0, y0=0, z0=-0.3, color=clDARKBLUE)


def draw_field():

    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (0, 0.4, 0))  # was green
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glColor3f(*clGREEN)
    glVertex3f(0, 0, FIELDLEVEL)
    glVertex3f(1000, 0, FIELDLEVEL)
    glVertex3f(1000, 1000, FIELDLEVEL)
    glVertex3f(0, 1000, FIELDLEVEL)
    glEnd()


def draw_field():
    FIELD_LEVEL = 0

    box = Box(len_x=1000, len_y=1000, len_z=0.2, x0=0, y0=0, z0=0, x_ref=1, y_ref=1, z_ref=-1, color=(0, 0.4, 0)).draw()


def box(
    len_x=1,
    len_y=1,
    len_z=1,  # unitsize 1
    x0=0,
    y0=0,
    z0=0,  # around the origin
    xa=0,
    ya=0,
    za=0,  # no rotations
    x_ref=0,
    y_ref=0,
    z_ref=0,  # centered
    edge_color=None,
    color=(1, 1, 1),
):
    """
    create_vertices
    """

    if x_ref == 0:
        x2 = len_x * 0.5
        x1 = -x2
    elif x_ref > 0:
        x1 = 0
        x2 = len_x
    else:
        x1 = -len_x
        x2 = 0

    if y_ref == 0:
        y2 = len_y * 0.5
        y1 = -y2
    elif y_ref > 0:
        y1 = 0
        y2 = len_y
    else:
        y1 = -len_y
        y2 = 0

    if z_ref == 0:
        z2 = len_z * 0.5
        z1 = -z2
    elif z_ref > 0:
        z1 = 0
        z2 = len_z
    else:
        z1 = -len_z
        z2 = 0

    bv = [[x1, y1, z1], [x2, y1, z1], [x2, y2, z1], [x1, y2, z1], [x1, y1, z2], [x2, y1, z2], [x2, y2, z2], [x1, y2, z2]]

    """
    draw
    """
    gl.glPushMatrix()

    gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, color)

    gl.glTranslate(x0, y0, z0)
    gl.glRotate(xa, 1.0, 0.0, 0.0)
    gl.glRotate(ya, 0.0, 1.0, 0.0)
    gl.glRotate(za, 0.0, 0.0, 1.0)

    gl.glBegin(gl.GL_QUADS)

    # bottom z-
    gl.glNormal(0, 0, -1)
    gl.glVertex3f(*bv[0])
    gl.glVertex3f(*bv[1])
    gl.glVertex3f(*bv[2])
    gl.glVertex3f(*bv[3])

    # top z+
    gl.glNormal3f(0, 0, 1)
    gl.glVertex3f(*bv[4])
    gl.glVertex3f(*bv[5])
    gl.glVertex3f(*bv[6])
    gl.glVertex3f(*bv[7])

    # left y-
    gl.glNormal3f(0, -1, 0)
    gl.glVertex3f(*bv[0])
    gl.glVertex3f(*bv[1])
    gl.glVertex3f(*bv[5])
    gl.glVertex3f(*bv[4])

    # right y+
    gl.glNormal3f(0, 1, 0)
    gl.glVertex3f(*bv[2])
    gl.glVertex3f(*bv[3])
    gl.glVertex3f(*bv[7])
    gl.glVertex3f(*bv[6])

    # front x+
    gl.glNormal3f(1, 0, 0)
    gl.glVertex3f(*bv[1])
    gl.glVertex3f(*bv[2])
    gl.glVertex3f(*bv[6])
    gl.glVertex3f(*bv[5])

    # front x-
    gl.glNormal3f(-1, 0, 0)
    gl.glVertex3f(*bv[3])
    gl.glVertex3f(*bv[0])
    gl.glVertex3f(*bv[4])
    gl.glVertex3f(*bv[7])

    gl.glEnd()

    if edge_color:
        gl.glBegin(gl.GL_LINES)

        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, edge_color)

        gl.glVertex3f(*bv[0])
        gl.glVertex3f(*bv[4])

        gl.glVertex3f(*bv[4])
        gl.glVertex3f(*bv[7])

        gl.glVertex3f(*bv[7])
        gl.glVertex3f(*bv[3])

        gl.glVertex3f(*bv[3])
        gl.glVertex3f(*bv[0])

        gl.glVertex3f(*bv[5])
        gl.glVertex3f(*bv[6])

        gl.glVertex3f(*bv[6])
        gl.glVertex3f(*bv[2])

        gl.glVertex3f(*bv[2])
        gl.glVertex3f(*bv[1])

        gl.glVertex3f(*bv[1])
        gl.glVertex3f(*bv[5])

        gl.glVertex3f(*bv[0])
        gl.glVertex3f(*bv[1])

        gl.glVertex3f(*bv[4])
        gl.glVertex3f(*bv[5])

        gl.glVertex3f(*bv[7])
        gl.glVertex3f(*bv[6])

        gl.glVertex3f(*bv[3])
        gl.glVertex3f(*bv[2])

        gl.glEnd()

    gl.glPopMatrix()


class Box:
    def __init__(
        self,
        len_x=1,
        len_y=1,
        len_z=1,  # unitsize 1
        x0=0,
        y0=0,
        z0=0,  # around the origin
        xa=0,
        ya=0,
        za=0,  # no rotations
        x_ref=0,
        y_ref=0,
        z_ref=0,  # centered
        color=(1, 1, 1),
    ):

        self.len_x = len_x
        self.len_y = len_y
        self.len_z = len_z
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.xa = xa
        self.ya = ya
        self.za = za
        self.x_ref = x_ref
        self.y_ref = y_ref
        self.z_ref = z_ref
        self.color = color

        self.create_vertices()

    """
    x to the right
    y backward
    z upward
    _ref -1: cling to upper
          0: centered
          1: cling to lower
          
    """

    def create_vertices(self):
        if self.x_ref == 0:
            x2 = self.len_x * 0.5
            x1 = -x2
        elif self.x_ref > 0:
            x1 = 0
            x2 = self.len_x
        else:
            x1 = -self.len_x
            x2 = 0

        if self.y_ref == 0:
            y2 = self.len_y * 0.5
            y1 = -y2
        elif self.y_ref > 0:
            y1 = 0
            y2 = self.len_y
        else:
            y1 = -self.len_y
            y2 = 0

        if self.z_ref == 0:
            z2 = self.len_z * 0.5
            z1 = -z2
        elif self.z_ref > 0:
            z1 = 0
            z2 = self.len_z
        else:
            z1 = -self.len_z
            z2 = 0

        self.bv = [[x1, y1, z1], [x2, y1, z1], [x2, y2, z1], [x1, y2, z1], [x1, y1, z2], [x2, y1, z2], [x2, y2, z2], [x1, y2, z2]]

    def draw(self):
        # Draw box (multiple quads)
        gl.glPushMatrix()

        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, self.color)

        gl.glTranslate(self.x0, self.y0, self.z0)
        gl.glRotate(self.xa, 1.0, 0.0, 0.0)
        gl.glRotate(self.ya, 0.0, 1.0, 0.0)
        gl.glRotate(self.za, 0.0, 0.0, 1.0)

        gl.glBegin(gl.GL_QUADS)

        # bottom z-
        gl.glNormal(0, 0, -1)
        gl.glVertex3f(*self.bv[0])
        gl.glVertex3f(*self.bv[1])
        gl.glVertex3f(*self.bv[2])
        gl.glVertex3f(*self.bv[3])

        # top z+
        gl.glNormal3f(0, 0, 1)
        gl.glVertex3f(*self.bv[4])
        gl.glVertex3f(*self.bv[5])
        gl.glVertex3f(*self.bv[6])
        gl.glVertex3f(*self.bv[7])

        # left y-
        gl.glNormal3f(0, -1, 0)
        gl.glVertex3f(*self.bv[0])
        gl.glVertex3f(*self.bv[1])
        gl.glVertex3f(*self.bv[5])
        gl.glVertex3f(*self.bv[4])

        # right y+
        gl.glNormal3f(0, 1, 0)
        gl.glVertex3f(*self.bv[2])
        gl.glVertex3f(*self.bv[3])
        gl.glVertex3f(*self.bv[7])
        gl.glVertex3f(*self.bv[6])

        # front x+
        gl.glNormal3f(1, 0, 0)
        gl.glVertex3f(*self.bv[1])
        gl.glVertex3f(*self.bv[2])
        gl.glVertex3f(*self.bv[6])
        gl.glVertex3f(*self.bv[5])

        # front x-
        gl.glNormal3f(-1, 0, 0)
        gl.glVertex3f(*self.bv[3])
        gl.glVertex3f(*self.bv[0])
        gl.glVertex3f(*self.bv[4])
        gl.glVertex3f(*self.bv[7])

        gl.glEnd()

        gl.glPopMatrix()


class ASC:
    PORTALWIDTH = 15
    PORTALHEIGHT = 10
    SIDELENGTH = 12
    SIDEWIDTH = 0.4
    SIDEHEIGHT = 0.4
    DIAGONALLENGTH = 10.6
    DIAGONALWIDTH = 0.3
    DIAGONALHEIGHT = 0.3
    DIAGONALLEVEL = 10.2
    TOP = 1
    TROLLEYLENGTH = 2.4  # 8 feet
    TROLLEYHEIGHT = 0.5
    TROLLEYWIDTH = 2.4
    SPREADERBOXLENGTH = 4
    SPREADERBOXWIDTH = 2.4
    SPREADERBOXHEIGHT = 0.2

    def __init__(self, x0, y0, z0, xa=0, ya=0, za=0, spreaderheight=3.00, color=clDARKGREY):
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.xa = xa
        self.ya = ya
        self.za = za
        self.color = color
        self.trolleypos = 0
        self.spreaderpos = 2.4
        self.spreaderheight = spreaderheight

    def draw(self):

        gl.glPushMatrix()

        gl.glTranslate(self.x0, self.y0, self.z0)
        gl.glRotate(self.xa, 1.0, 0.0, 0.0)
        gl.glRotate(self.ya, 0.0, 1.0, 0.0)
        gl.glRotate(self.za, 0.0, 0.0, 1.0)

        gl.glPushMatrix()
        self.draw_side(-self.PORTALWIDTH / 2)
        gl.glPopMatrix()

        gl.glPushMatrix()
        self.draw_side(self.PORTALWIDTH / 2)
        gl.glPopMatrix()

        gl.glPushMatrix()
        self.draw_top(self.PORTALHEIGHT, t_pos=-3)
        gl.glPopMatrix()

        self.draw_spreader()

        gl.glPopMatrix()

    def draw_side(self, pos_y):
        """
        box = 
        """

        gl.glPushMatrix()
        self.box_lowerlevelcase = Box(self.SIDELENGTH, self.SIDEWIDTH, self.SIDEHEIGHT, y0=pos_y, z0=0.2, z_ref=1, color=self.color)
        self.box_lowerlevelcase.draw()
        gl.glPopMatrix()

        gl.glPushMatrix()
        self.box_diagonal1 = Box(
            self.DIAGONALLENGTH,
            self.DIAGONALWIDTH,
            self.DIAGONALHEIGHT,
            x0=-0.5,
            y0=pos_y,
            z0=self.DIAGONALLEVEL,
            xa=0,
            ya=90 + 25,
            za=0,
            x_ref=1,
            y_ref=0,
            z_ref=0,
            color=self.color,
        )
        self.box_diagonal1.draw()
        gl.glPopMatrix()

        gl.glPushMatrix()
        self.box_diagonal2 = Box(
            self.DIAGONALLENGTH,
            self.DIAGONALWIDTH,
            self.DIAGONALHEIGHT,
            x0=0.5,
            y0=pos_y,
            z0=self.DIAGONALLEVEL,
            xa=0,
            ya=90 - 25,
            za=0,
            x_ref=1,
            y_ref=0,
            z_ref=0,
            color=self.color,
        )
        self.box_diagonal2.draw()
        gl.glPopMatrix()

    def draw_top(self, z_pos, t_pos):
        gl.glPushMatrix()
        self.box_top = Box(self.PORTALWIDTH + self.SIDEWIDTH, 2, 1, x0=0, y0=0, z0=z_pos, xa=0, ya=0, za=90, x_ref=0, y_ref=0, z_ref=1, color=self.color)
        self.box_top.draw()

        """ trolley box """
        box(
            self.TROLLEYLENGTH,
            self.TROLLEYWIDTH,
            self.TROLLEYHEIGHT,
            x0=0,
            y0=self.trolleypos,
            z0=z_pos + 1,
            x_ref=0,
            y_ref=0,
            z_ref=1,
            color=self.color,
            edge_color=(0.8, 0.8, 0.8),
        )

        gl.glPopMatrix()

    def draw_spreader(self):
        gl.glPushMatrix()
        self.box_spreader = Box(
            self.SPREADERBOXLENGTH, self.SPREADERBOXWIDTH, self.SPREADERBOXHEIGHT, x0=0, y0=self.trolleypos, z0=self.spreaderheight, z_ref=1, color=self.color
        )
        self.box_spreader.draw()
        # draw 4 cables
        cable_length = self.PORTALHEIGHT + 1 - self.spreaderheight  # - self.SPREADERBOXHEIGHT

        gl.glPushMatrix()

        for cable_x0 in [self.TROLLEYLENGTH / 2 - 0.1, -(self.TROLLEYLENGTH / 2 - 0.1)]:
            for cable_y0 in [self.TROLLEYWIDTH / 2 - 0.1, -(self.TROLLEYWIDTH / 2 - 0.1)]:
                self.box_cable = Box(
                    0.02, 0.02, cable_length, x0=cable_x0, y0=self.trolleypos + cable_y0, z0=self.spreaderheight, z_ref=1, color=(0, 0, 0)
                ).draw()

        gl.glPopMatrix()

        gl.glPopMatrix()


class Container:
    l = 12.00
    l2 = l / 2
    w = 2.40
    w2 = w / 2
    h = 2.55
    cv40 = [[-l2, -w2, 0], [l2, -w2, 0], [l2, w2, 0], [-l2, w2, 0], [-l2, -w2, h], [l2, -w2, h], [l2, w2, h], [-l2, w2, h]]

    cv = cv40

    def __init__(self, x, y, z, xa=0, ya=0, za=0, color=None, texture=None):
        self.x = x
        self.y = y
        self.z = z
        self.xa = xa
        self.ya = ya
        self.za = za
        self.color = color
        self.texture = texture
        # self.cv = box_to_vertices()

    def inc_x_angle(self):
        self.xa += 1

    def inc_y_angle(self):
        self.ya += 1

    def inc_z_angle(self):
        self.za += 1

    def draw_textured(self):
        # Draw Cube (multiple quads)

        glPushMatrix()

        #        glMaterialfv(GL_FRONT, GL_DIFFUSE, (0.5, 0.5, 0.5))  # was green
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, self.color)
        #        glMaterialfv(GL_FRONT, GL_AMBIENT, self.color)

        glRotate(self.xa, 1.0, 0.0, 0.0)
        glRotate(self.ya, 0.0, 1.0, 0.0)
        glRotate(self.za, 0.0, 0.0, 1.0)
        glTranslate(self.x, self.y, self.z)

        glBegin(GL_QUADS)

        # bottom z-
        #       glColor3f(0.0,0.0,0.0) # black
        glNormal3f(0, 0, -1)
        glVertex3f(*self.cv[0])
        glVertex3f(*self.cv[1])
        glVertex3f(*self.cv[2])
        glVertex3f(*self.cv[3])

        # top z+
        #        glColor3f(1.0,0.0,0.0) # red
        glNormal3f(0, 0, 1)
        glVertex3f(*self.cv[4])
        glVertex3f(*self.cv[5])
        glVertex3f(*self.cv[6])
        glVertex3f(*self.cv[7])

        # left y-
        #        glColor3f(0.0,1.0,0.0) # green
        glNormal3f(0, -1, 0)
        glVertex3f(*self.cv[0])
        glVertex3f(*self.cv[1])
        glVertex3f(*self.cv[5])
        glVertex3f(*self.cv[4])

        # right y+
        #        glColor3f(0.0,1.0,0.0) # green
        glNormal3f(0, 1, 0)
        glVertex3f(*self.cv[2])
        glVertex3f(*self.cv[3])
        glVertex3f(*self.cv[7])
        glVertex3f(*self.cv[6])

        # front x+
        #        glColor3f(1.0,1.0,0.0) # red/green
        glNormal3f(1, 0, 0)
        glVertex3f(*self.cv[1])
        glVertex3f(*self.cv[2])
        glVertex3f(*self.cv[6])
        glVertex3f(*self.cv[5])

        # front x-
        #        glColor3f(1.0,1.0,0.0) # red/green
        glNormal3f(-1, 0, 0)
        glVertex3f(*self.cv[3])
        glVertex3f(*self.cv[0])
        glVertex3f(*self.cv[4])
        glVertex3f(*self.cv[7])

        glEnd()

        glPopMatrix()

    def draw(self):
        # Draw Cube (multiple quads)
        gl.glPushMatrix()

        #        glMaterialfv(GL_FRONT, GL_DIFFUSE, (0.5, 0.5, 0.5))  # was green
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, self.color)
        #        glMaterialfv(GL_FRONT, GL_AMBIENT, self.color)

        gl.glTranslatef(self.x, self.y, self.z)
        gl.glRotatef(self.xa, 1.0, 0.0, 0.0)
        gl.glRotatef(self.ya, 0.0, 1.0, 0.0)
        gl.glRotatef(self.za, 0.0, 0.0, 1.0)

        gl.glBegin(gl.GL_QUADS)

        # bottom z-
        #       glColor3f(0.0,0.0,0.0) # black
        gl.glNormal(0, 0, -1)
        gl.glVertex3f(*self.cv[0])
        gl.glVertex3f(*self.cv[1])
        gl.glVertex3f(*self.cv[2])
        gl.glVertex3f(*self.cv[3])

        # top z+
        #        glColor3f(1.0,0.0,0.0) # red
        gl.glNormal3f(0, 0, 1)
        gl.glVertex3f(*self.cv[4])
        gl.glVertex3f(*self.cv[5])
        gl.glVertex3f(*self.cv[6])
        gl.glVertex3f(*self.cv[7])

        # left y-
        #        glColor3f(0.0,1.0,0.0) # green
        gl.glNormal3f(0, -1, 0)
        gl.glVertex3f(*self.cv[0])
        gl.glVertex3f(*self.cv[1])
        gl.glVertex3f(*self.cv[5])
        gl.glVertex3f(*self.cv[4])

        # right y+
        #        glColor3f(0.0,1.0,0.0) # green
        gl.glNormal3f(0, 1, 0)
        gl.glVertex3f(*self.cv[2])
        gl.glVertex3f(*self.cv[3])
        gl.glVertex3f(*self.cv[7])
        gl.glVertex3f(*self.cv[6])

        # front x+
        #        glColor3f(1.0,1.0,0.0) # red/green
        gl.glNormal3f(1, 0, 0)
        gl.glVertex3f(*self.cv[1])
        gl.glVertex3f(*self.cv[2])
        gl.glVertex3f(*self.cv[6])
        gl.glVertex3f(*self.cv[5])

        # front x-
        #        glColor3f(1.0,1.0,0.0) # red/green
        gl.glNormal3f(-1, 0, 0)
        gl.glVertex3f(*self.cv[3])
        gl.glVertex3f(*self.cv[0])
        gl.glVertex3f(*self.cv[4])
        gl.glVertex3f(*self.cv[7])

        gl.glEnd()

        gl.glPopMatrix()


def main():

    global window
    global camera

    glut.glutInit([""])
    glut.glutInitDisplayMode(glut.GLUT_RGBA | glut.GLUT_DOUBLE | glut.GLUT_DEPTH)
    glut.glutInitWindowSize(640, 480)
    glut.glutInitWindowPosition(200, 200)

    window = glut.glutCreateWindow("OpenGL Python Cube")

    glut.glutDisplayFunc(DrawGLScene)
    glut.glutIdleFunc(DrawGLScene)
    glut.glutKeyboardFunc(key_pressed)
    glut.glutSpecialFunc(key_pressed)
    glut.glutMouseWheelFunc(mouse_wheel_rolled)

    camera = Camera()
    camera.load_modelviewmatrix()
    print(camera.modelview_matrix)

    InitGL(640, 480)

    glut.glutMainLoop()


def test():
    print(box_to_vertices(len_x=2, len_y=2, len_z=2, x0=0, y0=0, z0=0, xa=0, ya=0, za=0, x_ref=0, y_ref=0, z_ref=-1, color=clDARKRED))


if __name__ == "__main__":
    main()
#    test()
