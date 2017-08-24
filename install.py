import numpy
import os
import shutil
import platform
Pythonista = (platform.system() == 'Darwin')

site_packages = '\\site-packages\\'

if Pythonista:
    documents = '/Documents'
    sp = os.getcwd().split(documents)
    if len(sp) != 2:
        print('unable to install')
        exit()
    path = sp[0] + documents + '/site-packages/salabim'

else:
    path = numpy.__file__.split(site_packages)[0] + site_packages + 'salabim'

if not os.path.isdir(path):
    os.makedirs(path)
if os.path.isfile('salabim.py'):
    shutil.copy(
        'salabim.py',
        path + ('/' if Pythonista else '\\') + 'salabim.py')
    with open(path + ('/' if Pythonista else '\\') + '__init__.py', 'w') as initfile:
        initfile.write('from .salabim import *\n')
    print('salabim succesfully installed')
else:
    print('could not find salabim.py')
