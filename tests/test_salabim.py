import pytest
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0,str(Path.cwd()/"salabim"))
    os.chdir("tests")    
    pytest.main(["-vv", "-s"])
