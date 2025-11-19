#!/usr/bin/env python3
import argparse, base64, hashlib, io, os, sys, textwrap, time, zipfile
from pathlib import Path
from string import Template

TEMPLATE = r'''#!/usr/bin/env python3
# Self-extracting Python archive generated on $created
# Original folder: $orig_name
# Files: $file_count | Compressed bytes: $zip_size | SHA256: $sha256

import argparse, base64, hashlib, io, os, sys, zipfile, salabim
from pathlib import Path

# Packed payload (base64)
_PAYLOAD = r"""
$payload
""".strip()

_META = {
    "sha256": "$sha256",
    "orig_name": "$orig_name",
    "file_count": $file_count,
    "zip_size": $zip_size,
}

def _decode_payload():
    data = base64.b64decode(_PAYLOAD.encode("ascii"))
    h = hashlib.sha256(data).hexdigest()
    if h != _META["sha256"]:
        print("Integrity check failed. Expected", _META["sha256"], "but got", h, file=sys.stderr)
        sys.exit(2)
    return data

def list_contents():
    data = _decode_payload()
    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        for zi in zf.infolist():
            is_dir = zi.filename.endswith("/")
            size = zi.file_size
            print(("{:<2} {:>12}  {}").format("d" if is_dir else "f", size, zi.filename))

def extract(dest: Path, strip_top=False):
    data = _decode_payload()
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        members = zf.infolist()
        total = len(members)
        for i, m in enumerate(members, 1):
            name = m.filename
            if strip_top:
                parts = name.split("/", 1)
                name = parts[1] if len(parts) > 1 else ""
            if not name:
                continue
            target = dest / name
            if name.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(m, "r") as src, open(target, "wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
            try:
                ts = m.date_time
                import datetime, time
                dt = datetime.datetime(*ts)
                epoch = dt.timestamp()
                os.utime(target, (epoch, epoch))
            except Exception:
                pass

    print(f"Done. Extracted to: {dest}")

def info():
    print("Original folder :", _META["orig_name"])
    print("Files           :", _META["file_count"])
    print("Compressed size :", _META["zip_size"], "bytes")
    print("SHA256          :", _META["sha256"])

def main():
    ap = argparse.ArgumentParser(description="Self-extracting Python archive")
    ap.add_argument("--list", action="store_true", help="List contents only")
    ap.add_argument("--info", action="store_true", help="Show metadata")
    ap.add_argument("--dest", type=Path, help="Extraction directory (default: ./$orig_name)")
    ap.add_argument("--strip-top", action="store_true", help="Strip top-level folder")
    args = ap.parse_args()

    if args.info:
        info()
        return
    if args.list:
        list_contents()
        return

    dest=Path(*Path(salabim.__file__).parts[:-2],"OpenGL")
    extract(dest, strip_top=args.strip_top)

if __name__ == "__main__":
    main()
'''

def build_zip_bytes(folder: Path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        root = folder.resolve()
        root_name = root.name
        zf.writestr(root_name + "/", b"")  # explicit top dir
        count = 0
        for path in root.rglob("*"):
            rel = path.relative_to(root).as_posix()
            arcname = f"{root_name}/{rel}"
            if path.is_dir():
                zf.writestr(arcname + "/", b"")
                continue
            if path.is_file():
                try:
                    with path.open("rb") as f:
                        data = f.read()
                except Exception:
                    continue
                zi = zipfile.ZipInfo(arcname)
                ts = time.localtime(path.stat().st_mtime)
                zi.date_time = ts[:6]
                zi.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(zi, data)
                count += 1
    return buf.getvalue(), count

def wrap_base64(b: bytes, width: int = 10000) -> str:
    b64 = base64.b64encode(b).decode("ascii")
    return "\n".join(b64[i:i+width] for i in range(0, len(b64), width))

def main():
    folder =Path(r"C:\Users\Ruud\.pyenv\pyenv-win\versions\3.14.0\Lib\site-packages\OpenGL")
    if not folder.is_dir():
        print(f"Error: {folder} not a directory")
        sys.exit(2)

    print(f"Packing: {folder.resolve()}")
    zip_bytes, file_count = build_zip_bytes(folder)
    sha256 = hashlib.sha256(zip_bytes).hexdigest()
    payload = wrap_base64(zip_bytes)
    created = time.strftime("%Y-%m-%d %H:%M:%S")
    out_path = Path(f"opengl_installer.py")

    script = Template(TEMPLATE).substitute(
        created=created,
        orig_name=folder.name,
        file_count=file_count,
        zip_size=len(zip_bytes),
        sha256=sha256,
        payload=payload,
    )

    out_path.write_text(script, encoding="utf-8")
    size_mb = out_path.stat().st_size / (1024*1024)
    print(f"Wrote: {out_path} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
