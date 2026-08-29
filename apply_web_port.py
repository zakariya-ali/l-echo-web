#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

def read(name: str) -> str:
    p = root / name
    if not p.exists():
        raise SystemExit(f"Missing {p}; run this script from/against an L-Echo checkout")
    return p.read_text(encoding="utf-8")

def write(name: str, text: str) -> None:
    (root / name).write_text(text, encoding="utf-8")

# 1) Teach the old platform switch about Emscripten while keeping the PC codepath.
name = "echo_platform.h"
text = read(name)
if "ECHO_WEB" not in text:
    pattern = r"#if defined\(ARM9\) \|\| defined\(ARM7\)"
    repl = "#if defined(__EMSCRIPTEN__)\n\t#define                                                         ECHO_PC                 1\n\t#define                                                         ECHO_WEB                1\n#elif defined(ARM9) || defined(ARM7)"
    text, n = re.subn(pattern, repl, text, count=1)
    if n != 1:
        raise SystemExit("Could not patch echo_platform.h: platform selector changed upstream")
    write(name, text)
    print("patched echo_platform.h")
else:
    print("echo_platform.h already patched")

# 2) Emscripten has a virtual filesystem, not /proc/<pid>/exe. Point the loader at /game.
name = "echo_ingame_loader.cpp"
text = read(name)
if 'const char* webdir = "/game";' not in text:
    pattern = r"(#ifdef\s+ECHO_NDS\s*\n\s*return\(echo_genroot\(save\)\);\s*\n)#elif\s+ECHO_WIN"
    repl = (r"\1#elif defined(ECHO_WEB)\n"
            r'\t\tconst char* webdir = "/game";\n'
            r"\t\t*save = new char[strlen(webdir) + 1];\n"
            r"\t\tstrcpy(*save, webdir);\n"
            r"\t\treturn(WIN);\n"
            r"#elif ECHO_WIN")
    text, n = re.subn(pattern, repl, text, count=1)
    if n != 1:
        raise SystemExit("Could not patch echo_ingame_loader.cpp: echo_execdir layout changed upstream")
    write(name, text)
    print("patched echo_ingame_loader.cpp")
else:
    print("echo_ingame_loader.cpp already patched")

# 3) The desktop renderer sleeps to force 30 FPS. In the browser, never block the main thread.
#    Instead, keep GLUT's event loop and simply skip render/simulation ticks until 33.3ms elapsed.
name = "main.cpp"
text = read(name)
if "ECHO_WEB_FRAME_GATE" not in text:
    pattern = r"static void display\(\)\s*\n\{"
    repl = ("static void display()\n"
            "{\n"
            "#ifdef ECHO_WEB\n"
            "\t// ECHO_WEB_FRAME_GATE: preserve L-Echo's original 30 FPS simulation without blocking the browser.\n"
            "\tconst int web_now = glutGet(GLUT_ELAPSED_TIME);\n"
            "\tif(web_now - prev_time < WAIT)\n"
            "\t\treturn;\n"
            "\tprev_time = web_now;\n"
            "#endif")
    text, n = re.subn(pattern, repl, text, count=1)
    if n != 1:
        raise SystemExit("Could not patch main.cpp: display() signature changed upstream")

    # Wrap the old sleep-based limiter at the bottom of display().
    old = """\tint elapsed = glutGet(GLUT_ELAPSED_TIME) - prev_time;\n\tif(elapsed < WAIT)\n\t{\n\t\tECHO_SLEEP(WAIT - elapsed);\n\t\t//ECHO_PRINT(\"not fskip\\n\");\n\t}\n\t//frameskip =(\n\t//else\n\t//\tECHO_PRINT(\"fskip: %f\\n\", elapsed - WAIT);\n\tprev_time = glutGet(GLUT_ELAPSED_TIME);\n"""
    new = """#ifndef ECHO_WEB\n\tint elapsed = glutGet(GLUT_ELAPSED_TIME) - prev_time;\n\tif(elapsed < WAIT)\n\t{\n\t\tECHO_SLEEP(WAIT - elapsed);\n\t\t//ECHO_PRINT(\"not fskip\\n\");\n\t}\n\t//frameskip =(\n\t//else\n\t//\tECHO_PRINT(\"fskip: %f\\n\", elapsed - WAIT);\n\tprev_time = glutGet(GLUT_ELAPSED_TIME);\n#endif\n"""
    if old not in text:
        raise SystemExit("Could not patch main.cpp: original frame limiter changed upstream")
    text = text.replace(old, new, 1)
    write(name, text)
    print("patched main.cpp")
else:
    print("main.cpp already patched")

# 3b) A CLI-specified stage is parsed before init() creates the GLUT/WebGL context.
#     Native L-Echo calls resize() from load() anyway; on web, defer that GL work until init().
name = "main.cpp"
text = read(name)
if "ECHO_WEB_DEFER_RESIZE" not in text:
    pattern = r"(?m)^(?P<indent>\s*)//resize, since we change the depth of the stage\s*\n(?P=indent)resize\(my_width, my_height\);\s*$"
    def defer_resize(match):
        indent = match.group("indent")
        return (f"{indent}//resize, since we change the depth of the stage\n"
                f"{indent}// ECHO_WEB_DEFER_RESIZE: init() will perform the first resize after WebGL exists.\n"
                f"{indent}#ifdef ECHO_WEB\n"
                f"{indent}if(my_width > 0 && my_height > 0)\n"
                f"{indent}\tresize(my_width, my_height);\n"
                f"{indent}#else\n"
                f"{indent}resize(my_width, my_height);\n"
                f"{indent}#endif")
    text, n = re.subn(pattern, defer_resize, text, count=1)
    if n != 1:
        raise SystemExit("Could not patch main.cpp: load()/resize block changed upstream")
    write(name, text)
    print("patched main.cpp pre-context resize guard")

# 4) GLU is not needed by the current renderer and should not be required for the WebGL build.
for name in ("main.cpp", "echo_gfx.cpp"):
    text = read(name)
    if "ECHO_WEB_GLU_GUARD" not in text:
        pattern = r"(?m)^(?P<indent>\s*)#include <GL/glu\.h>\s*$"
        def guard(match):
            indent = match.group("indent")
            return (f"{indent}// ECHO_WEB_GLU_GUARD\n"
                    f"{indent}#ifndef ECHO_WEB\n"
                    f"{indent}#include <GL/glu.h>\n"
                    f"{indent}#endif")
        text, n = re.subn(pattern, guard, text)
        if n:
            write(name, text)
            print(f"patched {name} GLU include")


# 5) Emscripten's built-in GLUT layer does not provide the old GLUT bitmap-font path reliably.
#    The Web shell supplies the visible controls/level selector, so compile the legacy HUD text calls as no-ops.
name = "main.cpp"
text = read(name)
if "ECHO_WEB_BITMAP_FONT_SHIM" not in text:
    pattern = r"(?m)^(?P<indent>\s*)#define ENTER\s+13\s*$"
    def add_font_shim(match):
        indent = match.group("indent")
        line = match.group(0)
        return (line + "\n"
                + f"{indent}#ifdef ECHO_WEB\n"
                + f"{indent}\t// ECHO_WEB_BITMAP_FONT_SHIM: browser build uses HTML UI instead of GLUT bitmap fonts.\n"
                + f"{indent}\t#define glutBitmapCharacter(font, character) ((void)0)\n"
                + f"{indent}\t#define glutBitmapWidth(font, character) (8)\n"
                + f"{indent}#endif")
    text, n = re.subn(pattern, add_font_shim, text, count=1)
    if n != 1:
        raise SystemExit("Could not patch main.cpp: ENTER key define changed upstream")
    write(name, text)
    print("patched main.cpp GLUT bitmap-font shim")

print("L-Echo web source patch complete")
