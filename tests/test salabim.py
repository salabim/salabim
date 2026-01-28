import pytest
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    import os, sys # three lines to use the local package and chdir
    os.chdir(os.path.dirname(__file__))
    sys.path.insert(0, os.path.dirname(__file__) + "/../")

    pytest.main(["-vv", "-s"])
