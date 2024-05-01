import salabim as sim
import math

import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut

class AnimatePyramid(sim.Animate3dBase):
    def setup(self, x=0, y=0, z=0, x_angle=0, y_angle=0, z_angle=0, side_length=1, color="white", shaded=False):
        self.x = x
        self.y = y
        self.z = z
        self.x_angle=x_angle
        self.y_angle=y_angle
        self.z_angle=z_angle
        self.color=color
        self.side_length =side_length
        self.shaded=shaded
        self.register_dynamic_attributes("x y z x_angle y_angle z_angle color side_length shaded")

    def draw(self, t):

        gl_color0 = env.colorspec_to_gl_color(self.color(t))
        if self.shaded(t):
            gl_color1 = (gl_color0[0] * 0.9, gl_color0[1] * 0.9, gl_color0[2] * 0.9)
            gl_color2 = (gl_color0[0] * 0.8, gl_color0[1] * 0.8, gl_color0[2] * 0.8)
            gl_color3 = (gl_color0[0] * 0.7, gl_color0[1] * 0.7, gl_color0[2] * 0.7)

        else:
            gl_color1 = gl_color2 = gl_color3 = gl_color0


        side_length = self.side_length(t)
        gl.glPushMatrix()

        gl.glTranslate(self.x(t), self.y(t), self.z(t))
 
        gl.glRotate(self.x_angle(t), 1.0, 0.0, 0.0)
        gl.glRotate(self.y_angle(t), 0.0, 1.0, 0.0)
        gl.glRotate(self.z_angle(t), 0.0, 0.0, 1.0)

        v1=(side_length*math.sqrt(8/9), side_length*0, -side_length*1/3)
        v2=(-side_length*math.sqrt(2/9), side_length*math.sqrt(2/3), -side_length*1/3)
        v3=(-side_length*math.sqrt(2/9), -side_length*math.sqrt(2/3), -side_length*1/3)
        v4=(side_length*0,side_length*0,side_length*1)

        """
        sim.draw_bar3d(*v1, *v2, gl_color=gl_color)
        sim.draw_bar3d(*v1, *v3, gl_color=gl_color)
        sim.draw_bar3d(*v1, *v4, gl_color=gl_color)
        sim.draw_bar3d(*v2, *v3, gl_color=gl_color)
        sim.draw_bar3d(*v2, *v4, gl_color=gl_color)
        sim.draw_bar3d(*v3, *v4, gl_color=gl_color)
        """

        gl.glBegin(gl.GL_TRIANGLES)
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color0)

        gl.glVertex3f(*v1)
        gl.glVertex3f(*v2)
        gl.glVertex3f(*v3)

        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color1)
        gl.glVertex3f(*v1)
        gl.glVertex3f(*v2)
        gl.glVertex3f(*v4)

        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color2)
        gl.glVertex3f(*v1)
        gl.glVertex3f(*v3)
        gl.glVertex3f(*v4)

        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, gl_color3)
        gl.glVertex3f(*v2)
        gl.glVertex3f(*v3)
        gl.glVertex3f(*v4)


        gl.glEnd()





        gl.glPopMatrix()


env = sim.Environment(trace=False)

do_animate = True
do_animate3d = True

env.x0(0)
env.x1(380)
env.y0(0)

env.width3d(950)
env.height3d(768)
env.position3d((0, 100))
env.background_color("black")
env.width(950)
env.height(768)
env.position((960, 100))

env.animate(do_animate)
env.animate3d(do_animate)
env.show_fps(True)
sim.Animate3dGrid(x_range=range(0, 101, 10), y_range=range(0, 101, 10))

env.view.x_eye = -100
env.view.y_eye = -100
env.view.z_eye = 100
env.view.x_center = 50
env.view.y_center = 50
env.view.z_center = 0
env.view.field_of_view_y = 50

env.show_camera_position()

sim.Animate3dSphere(x=60, y=60, z=60, radius=10, number_of_slices=32)

sim.Animate3dRectangle(x0=10, y0=10, x1=40, y1=40, z=-20, color="yellow")
sim.Animate3dLine(x0=0, y0=0,z0=0, x1=50, y1=50, z1=50, color="purple")

sim.Animate3dBar(x0=10, y0=10, z0=10, x1=40, y1=10, z1=10)
sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=40, z1=10)
sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=10, z1=40)
sim.Animate3dBar(x0=10, y0=10, z0=40, x1=10, y1=10, z1=10)


sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=40, z1=10)
sim.Animate3dBar(x0=40, y0=40, z0=10, x1=40, y1=10, z1=10)
sim.Animate3dBar(x0=40, y0=40, z0=10, x1=10, y1=40, z1=10)

sim.Animate3dBar(x0=10, y0=10, z0=40, x1=40, y1=10, z1=40)
sim.Animate3dBar(x0=10, y0=10, z0=40, x1=10, y1=40, z1=40)
sim.Animate3dBar(x0=40, y0=40, z0=40, x1=40, y1=10, z1=40)
sim.Animate3dBar(x0=40, y0=40, z0=40, x1=10, y1=40, z1=40)

sim.Animate3dBar(x0=10, y0=10, z0=10, x1=10, y1=10, z1=40)
sim.Animate3dBar(x0=10, y0=40, z0=10, x1=10, y1=40, z1=40)
sim.Animate3dBar(x0=40, y0=10, z0=10, x1=40, y1=10, z1=40)
sim.Animate3dBar(x0=40, y0=40, z0=10, x1=40, y1=40, z1=40)


sim.Animate3dCylinder(x0=0, y0=50, z0=0, x1=0, y1=50, z1=40, number_of_sides=8, radius=10, show_lids=False, color="green")

sim.Animate3dBox(x_len=10, y_len=10, z_len=10, x=0, y=0, z=0, x_ref=1, y_ref=1, z_ref=1, color="red", shaded=True)
sim.Animate3dBox(x_len=10, y_len=10, z_len=10, x=0, y=0, z=0, x_ref=-1, y_ref=-1, z_ref=-1, color="blue", edge_color="white")

AnimatePyramid(x=0, y=0, z=50, side_length=30, color="cyan", shaded=True)

sim.AnimateText("this is over 3d", x=100,y=100, over3d=True)
env.run(sim.inf)

