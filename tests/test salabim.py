import pytest
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    import os, sys # three lines to use the local package and chdir
    os.chdir(os.path.dirname(__file__))
    sys.path.insert(0, os.path.dirname(__file__) + "/../" + os.path.dirname(__file__).split(os.sep)[-2])

    pytest.main(["-vv", "-s"])
