#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"
DIST="$ROOT/dist"

if ! command -v em++ >/dev/null 2>&1; then
  echo "error: em++ not found. Activate an Emscripten SDK first." >&2
  exit 1
fi

python3 "$(cd "$(dirname "$0")" && pwd)/apply_web_port.py" "$ROOT"
mkdir -p "$DIST"
rm -f "$DIST"/index.{html,js,wasm,data}

cd "$ROOT"

# Bundle only the stage XML files into Emscripten's virtual /game directory.
PRELOAD=()
shopt -s nullglob
for f in *.xml *.xml.real; do
  PRELOAD+=(--preload-file "$f@/game/$f")
done
shopt -u nullglob

if ((${#PRELOAD[@]} == 0)); then
  echo "error: no L-Echo stage XML files found in $ROOT" >&2
  exit 1
fi

SHELL_FILE="$(cd "$(dirname "$0")" && pwd)/web/shell.html"

em++ \
  *.cpp pugixml/*.cpp \
  -I. \
  -std=gnu++98 \
  -DTIXML_USE_STL \
  -DUSE_IK \
  -DUSE_PUGIXML \
  -O2 \
  -sLEGACY_GL_EMULATION=1 \
  -sGL_FFP_ONLY=1 \
  -sALLOW_MEMORY_GROWTH=1 \
  -sASSERTIONS=1 \
  -sENVIRONMENT=web \
  "${PRELOAD[@]}" \
  --shell-file "$SHELL_FILE" \
  -o "$DIST/index.html"

cp "$(cd "$(dirname "$0")" && pwd)/web/serve.py" "$DIST/serve.py"

echo
echo "Built: $DIST/index.html"
echo "Run:   cd $DIST && python3 serve.py"
echo "Open:  http://localhost:8080"
