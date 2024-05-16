import pytest
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    file_folder = Path(__file__).parent
    top_folder = (file_folder / "..").resolve()
    sys.path.insert(0, str(top_folder))
    os.chdir(file_folder)

    pytest.main(["-vv", "-s"])