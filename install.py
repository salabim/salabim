"""
install.py

This program makes it possible to install a single file Python package to the site-packages folder,
without having to use PyPI.
So, then the single file package can be used from anywhere.

The program will copy the single file as well as optional include files.

The tuple packages should contain one or more packages to be installed, each in their own site-packages subfolder.
-
The includes tuple may contain additional files to be copied to the site_packages subfolder(s).

Note that the program automatically makes the required __init__.py file(s).
If a __version__ = statement is found in the source file, the __version__ will be included in the __init__.py file.
"""

import shutil
import glob
import sys
import site
import fnmatch

includes = "changelog.txt license.txt *.ttf".split()
packages = "salabim".split()

Pythonista = sys.platform == "ios"


def copy_package(package):
    sourcefile = package + ".py"
    if not os.path.isfile(sourcefile):
        return False

    with open(sourcefile, "r") as f:
        lines = f.read().splitlines()

    version = None
    for line in lines:
        a = line.split("__version__ =")
        if len(a) > 1:
            version = a[-1].strip().strip('"').strip("'")
            break

    if Pythonista:
        documents = os.sep + "Documents"
        sp = os.getcwd().split(documents)
        if len(sp) != 2:
            print("unable to install")
            exit()
        path = sp[0] + documents + os.sep + "site-packages" + os.sep + package

    else:
        path = site.getsitepackages()[-1] + os.sep + package

    if not os.path.isdir(path):
        os.makedirs(path)

    shutil.copy(sourcefile, path + os.sep + sourcefile)

    files = glob.iglob("*.*")

    for file in files:
        if any(fnmatch.fnmatch(file, include) for include in includes):
            shutil.copy(file, path + os.sep + file)

    with open(path + os.sep + "__init__.py", "w") as initfile:
        initfile.write("from ." + package + " import *\n")
        if version is not None:
            initfile.write("from ." + package + " import __version__\n")
    print(package + " " + ("?" if version is None else version) + " successfully installed")
    return True


def main():
    number_installed = 0
    for package in packages:
        if copy_package(package):
            number_installed += 1
    if number_installed == 0:
        print("No packages installed")


main()
