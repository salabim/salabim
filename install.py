import os
import shutil
import glob
import sys
import site
import fnmatch

includes = ("salabim.py", "changelog.txt", "license.txt", "*.ttf")
mainfile = "salabim.py"
package = "salabim"

Pythonista = sys.platform == "ios"


def main():

    if Pythonista:
        documents = "/Documents"
        sp = os.getcwd().split(documents)
        if len(sp) != 2:
            print("unable to install")
            exit()
        path = f"{sp[0]}{documents}/site-packages/{package}"

    else:
        path = f"{site.getsitepackages()[-1]}{os.sep}{package}"

    if not os.path.isdir(path):
        os.makedirs(path)

    files = glob.iglob("*.*")

    ok = False
    for file in files:
        if any(fnmatch.fnmatch(file, include) for include in includes):
            if file == mainfile:
                ok = True
            shutil.copy(file, f"{path}{os.sep}{file}")
    if not ok:
        print(f"couldn't find {mainfile} in current directory")
        return

    with open(mainfile, "r") as f:
        lines = f.read().splitlines()

    realversion = "?"
    for line in lines:
        a = line.split("__version__ = ")
        if len(a) > 1:
            realversion = a[1].replace("'", "").replace('"', "")
            break

    with open(f"{path}{os.sep}__init__.py", "w") as initfile:
        initfile.write(f"from .{package} import *\n")
        initfile.write(f"from .{package} import __version__\n")
    print(f"{package} {realversion} successfully installed")


main()
