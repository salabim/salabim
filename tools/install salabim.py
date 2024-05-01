from __future__ import print_function

import sys
import site
import shutil
import hashlib
import base64
from pathlib import Path
import configparser
import six
import os
from six.moves import urllib

# import urllib.request
# import urllib.error


def _install(files, url=None):
    """
    install one file package from GitHub or current directory

    Parameters
    ----------
    files : list
        files to be installed
        the first item (files[0]) will be used as the name of the package''
        optional files should be preceded with an exclamation mark (!)

    url : str
        url of the location of the GitHub repository
        this will start usually with https://raw.githubusercontent.com/ and end with /master/
        if omitted, the files will be copied from the current directory (not GitHub)


    Returns
    -------
    info : Info instance
        info.package : name of the package installed
        info.path : name where the package is installed in the site-packages
        info.version : version of the package (obtained from <package>.py)
        info.files_copied : list of copied files

    Notes
    -----
    The program automatically makes the required __init__.py file (unless given in files) and
    <package><version>.dist-info folder with the usual files METADATA, INSTALLER and RECORDS.
    As the setup.py is not run, the METADATA is very limited, i.e. is contains just name and version.

    If a __init__.py is in files that file will be used.
    Otherwise, an __init__/py file will be generated. In thet case, if a __version__ = statement
    is found in the source file, the __version__ will be included in that __init__.py file.

    Version history
    ---------------
    version 1.0.6  2024-05-01
        If the first source file can't be found in the current working directory,
        the program will search one level deep
        
    version 1.0.5  2020-06-24
        Bug with removing the dist-info of packages starting with the same name fixed.

    version 1.0.4  2020-03-29
        Linux and ios versions now search in sys.path for site-packages,
        whereas other platforms now use site.getsitepackages().
        This is to avoid installation in a roaming directory on Windows.

    version 1.0.2  2020-03-07
        modified several open calls to be compatible with Python < 3.6
        multipe installation for Pythonista removed. Now installs only in site-packages

    version 1.0.1  2020-03-06
        now uses urllib instead of requests to avoid non standard libraries
        installation for Pythonista improved

    version 1.0.0  2020-03-04
        initial version

    (c)2020 Ruud van der Ham - www.salabim.org
    """

    class Info:
        version = "?"
        package = "?"
        path = "?"
        files_copied = []

    info = Info()
    Pythonista = sys.platform == "ios"
    if not files:
        raise ValueError("no files specified")
    if files[0][0] == "!":
        raise ValueError("first item in files (sourcefile) may not be optional")
    package = Path(files[0]).stem
    sourcefile = files[0]

    if Path(sourcefile).is_file():
        prefix = Path("")
    else:
        prefix = Path(sourcefile).stem # one level deep
    file_contents = {}
    for file in files:
        optional = file[0] == "!"
        if optional:
            file = file[1:]

        if url:
            try:
                with urllib.request.urlopen(url + file) as response:
                    page = response.read()

                file_contents[file] = page
                exists = True
            except urllib.error.URLError:
                exists = False

        else:
            exists = (prefix / Path(file)).is_file()
            if exists:
                with open(prefix / Path(file), "rb") as f:
                    file_contents[file] = f.read()

        if (not exists) and (not optional):
            raise FileNotFoundError(file + " not found. Nothing installed.")

    version = "unknown"
    for line in file_contents[sourcefile].decode("utf-8").split("\n"):
        line_split = line.split("__version__ =")
        if len(line_split) > 1:
            raw_version = line_split[-1].strip(" '\"")
            version = ""
            for c in raw_version:
                if c in "0123456789-.":
                    version += c
                else:
                    break
            break

    info.files_copied = list(file_contents.keys())
    info.package = package
    info.version = version

    file = "__init__.py"
    if file not in file_contents:
        file_contents[file] = ("from ." + package + " import *\n").encode()
        if version != "unknown":
            file_contents[file] += ("from ." + package + " import __version__\n").encode()
    if sys.platform.startswith("linux") or (sys.platform == "ios"):
        search_in = sys.path
    else:
        search_in = site.getsitepackages()

    for f in search_in:
        sitepackages_path = Path(f)
        if sitepackages_path.name == "site-packages" and sitepackages_path.is_dir():
            break
    else:
        raise ModuleNotFoundError("can't find the site-packages folder")

    path = sitepackages_path / package
    info.path = str(path)

    if path.is_file():
        path.unlink()

    if not path.is_dir():
        path.mkdir()

    for file, contents in file_contents.items():
        with (path / file).open("wb") as f:
            f.write(contents)

    if Pythonista:
        pypi_packages = sitepackages_path / ".pypi_packages"
        config = configparser.ConfigParser()
        config.read(pypi_packages)
        config[package] = {}
        config[package]["url"] = "pypi"
        config[package]["version"] = version
        config[package]["summary"] = ""
        config[package]["files"] = path.as_posix()
        config[package]["dependency"] = ""
        with pypi_packages.open("w") as f:
            config.write(f)
    else:
        for entry in sitepackages_path.glob("*"):
            if entry.is_dir():
                if entry.stem.startswith(package + "-") and entry.suffix == ".dist-info":
                    shutil.rmtree(str(entry))
        path_distinfo = Path(str(path) + "-" + version + ".dist-info")
        if not path_distinfo.is_dir():
            path_distinfo.mkdir()
        with open(str(path_distinfo / "METADATA"), "w") as f:  # make a dummy METADATA file
            f.write("Name: " + package + "\n")
            f.write("Version: " + version + "\n")

        with open(str(path_distinfo / "INSTALLER"), "w") as f:  # make a dummy METADATA file
            f.write("github\n")
        with open(str(path_distinfo / "RECORD"), "w") as f:
            pass  # just to create the file to be recorded

        with open(str(path_distinfo / "RECORD"), "w") as record_file:
            for p in (path, path_distinfo):
                for file in p.glob("**/*"):
                    if file.is_file():
                        name = file.relative_to(sitepackages_path).as_posix()  # make sure we have slashes
                        record_file.write(name + ",")

                        if (file.stem == "RECORD" and p == path_distinfo) or ("__pycache__" in name.lower()):
                            record_file.write(",")
                        else:
                            with file.open("rb") as f:
                                file_contents = f.read()
                                hash = "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(file_contents).digest()).decode("latin1").rstrip("=")
                                # hash calculation derived from wheel.py in pip

                                length = str(len(file_contents))
                                record_file.write(hash + "," + length)

                        record_file.write("\n")

    return info



if __name__ == "__main__":
    info = _install(files="salabim.py !calibri.ttf !mplus-1m-regular.ttf !license.txt !DejaVuSansMono.ttf !changelog.txt".split())
    print(info.package + " " + info.version + " successfully installed in " + info.path)
    print("files copied: ", ", ".join(info.files_copied))
