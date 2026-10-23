"""Lists the files in a Godot 4 .pck, one path a line, or with --sizes the
total per top folders. Used by export.sh to check what the browser demo holds.

    python3 tools/build/pck_list.py build/web/index.pck [--sizes]
"""

import collections
import struct
import sys


def entries(path: str) -> list[tuple[str, int]]:
    with open(path, "rb") as f:
        if f.read(4) != b"GDPC":
            raise SystemExit(f"{path} is not a Godot pack")
        version, = struct.unpack("<I", f.read(4))
        f.read(12)  # engine version
        f.read(4)  # flags
        f.read(8)  # file base
        if version >= 3:
            directory, = struct.unpack("<Q", f.read(8))
            f.seek(directory)
        else:
            f.read(64)
        count, = struct.unpack("<I", f.read(4))
        rows = []
        for _ in range(count):
            length, = struct.unpack("<I", f.read(4))
            name = f.read(length).rstrip(b"\0").decode()
            _offset, size = struct.unpack("<QQ", f.read(16))
            f.read(16)  # md5
            f.read(4)  # flags
            rows.append((name.removeprefix("res://"), size))
        return rows


if __name__ == "__main__":
    rows = entries(sys.argv[1])
    if "--sizes" in sys.argv:
        totals = collections.Counter()
        for name, size in rows:
            totals["/".join(name.split("/")[:2])] += size
        for folder, size in totals.most_common(20):
            print(f"{size / 1e6:8.1f} MB  {folder}")
        print(f"{sum(size for _, size in rows) / 1e6:8.1f} MB  in {len(rows)} files")
    else:
        for name, _size in rows:
            print(name)
