#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

changed_files = []
replacement_count = 0

# L-Echo's generated desktop models use GL_QUAD_STRIP heavily. Emscripten's
# legacy GL emulation aborts on that primitive (mode 8). The model vertices
# are emitted as alternating edge pairs, so GL_TRIANGLE_STRIP represents the
# same strip surface with triangles that WebGL supports.
for path in root.glob("*.cpp"):
    text = path.read_text(encoding="utf-8")
    count = text.count("GL_QUAD_STRIP")
    if not count:
        continue

    path.write_text(text.replace("GL_QUAD_STRIP", "GL_TRIANGLE_STRIP"), encoding="utf-8")
    changed_files.append(path.name)
    replacement_count += count

print(f"web primitive patch: replaced {replacement_count} GL_QUAD_STRIP occurrence(s)")
for name in changed_files:
    print(f"  patched {name}")
