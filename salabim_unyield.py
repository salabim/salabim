import sys
from pathlib import Path


def unyield(filename):
    filename = str(filename)
    if not filename.endswith('.py'):
        return 0
        
    if filename.endswith("_yieldless.py"):
        print(f"{filename:60} file not converted as it endswith _yieldless.py")
        return 0

    with open(filename, "r") as f:
        text = f.read()

    number_of_added_lines = 0
    number_of_modified_lines = 0

    output = []

    for line in text.splitlines():
        parts = line.split("yield ", 1)
        result1 = ""
        if "import salabim as sim" in line:
            result = line
            result1 = line.replace("import salabim as sim", "sim.yieldless(True)")
        if len(parts) > 1:
            parts[1] = parts[1].lstrip()
            if parts[0].strip():
                if parts[0].strip().endswith("="):
                    result = f"{parts[0]}{parts[1]}"
                else:
                    result = line
            else:
                if parts[1].lstrip().startswith("from "):
                    parts[1] = parts[1].replace("from ", "").lstrip()
                result = f"{parts[0]}{parts[1]}"
        else:
            result = line
        number_of_modified_lines += result != line
        output.append(result)
        if result1:
            output.append(result1)
            number_of_added_lines += 1

    if number_of_modified_lines == 0:
        print(f"{filename:60} file not converted as it does not contain any yield")
        return 0
    else:
        new_filename = filename.replace(".py", "_yieldless.py")
        with open(new_filename, "w") as f:
            f.write("\n".join(output))
        print(f"{filename:60} converted file: {new_filename} ")
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: salabim_unyield spec")
        print("       spec can be a filename or a wildcard")
        print("       relative to the current directory")
    else:
        number_of_files_changed = 0
        for filename in Path(".").glob(sys.argv[1]):
            number_of_files_changed += unyield(filename)
        print(f"{number_of_files_changed} file(s) changed")
