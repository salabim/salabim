import PIL

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import math

radius=60
linewidth=0
fillcolor=(255,0,0,255)

nsteps = int(math.sqrt(radius) * 6)
tangle = 2 * math.pi / nsteps
sint = math.sin(tangle)
cost = math.cos(tangle)
p = []
x = radius
y = 0

for i in range(nsteps + 1):
    x, y = (x * cost - y * sint, x * sint + y * cost)
    p.append(x + radius + linewidth)
    p.append(y + radius + linewidth)

image = Image.new('RGBA', (int(radius * 2 + 2 * linewidth),
                                 int(radius * 2 + 2 * linewidth)), (0, 0, 0, 0))
print (type(image))
draw = ImageDraw.Draw(image)
if fillcolor[3] != 0:
    draw.polygon(p, fill=fillcolor)
if (linewidth > 0) and (linecolor[3] != 0):
    draw.line(p, fill=linecolor, width=int(linewidth))
del draw

image.save('1.png')

redimage=Image.open('red.png')
redimage=redimage.convert('RGBA')
blueimage=Image.open('blue.png')
blueimage=blueimage.convert('RGBA')
if (redimage,1) == (blueimage,1):
    print('ok')
print (type(redimage))
print(isinstance(redimage,PIL.Image.Image))

