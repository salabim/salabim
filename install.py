import numpy
import os
import shutil
import glob
import sys

Pythonista = sys.platform == "ios"

site_packages = os.sep + "site-packages" + os.sep

if Pythonista:
    documents = "/Documents"
    sp = os.getcwd().split(documents)
    if len(sp) != 2:
        print("unable to install")
        exit()
    path = sp[0] + documents + "/site-packages/salabim"

else:
    path = numpy.__file__.split(site_packages)[0] + site_packages + "salabim"

if not os.path.isdir(path):
    os.makedirs(path)

files = glob.iglob("*.*")

ok = False
for file in files:
    if (file in ("salabim.py", "changelog.txt", "license.txt")) or (file.endswith(".ttf")):
        if file == "salabim.py":
            ok = True
        shutil.copy(file, path + os.sep + file)
if ok:
    with open("salabim.py", "r") as f:
        lines = f.read().splitlines()

    realversion = ""
    for line in lines:
        a = line.split("__version__ = ")
        if len(a) > 1:
            realversion = a[1].replace("'", "")
            realversion = a[1].replace('"', "")
            break

    with open(path + os.sep + "__init__.py", "w") as initfile:
        initfile.write("from .salabim import *\n")
    print("salabim " +realversion+ " succesfully installed")
else:
    print("could not find salabim.py")
