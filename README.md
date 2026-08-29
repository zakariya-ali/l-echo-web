# L-Echo Web Port Kit

This kit patches the archived **LibreGamesArchive/l-echo** C++ source for an Emscripten/WebAssembly build.

It does four things:

1. Adds an `ECHO_WEB` platform while reusing the existing PC gameplay/input/rendering path.
2. Maps the game's executable directory to Emscripten's virtual `/game` filesystem.
3. Removes the native blocking `usleep()` frame limiter in the browser and keeps the original ~30 FPS simulation by gating GLUT display ticks.
4. Builds the existing legacy OpenGL/GLUT renderer with Emscripten's legacy OpenGL emulation and bundles the XML stages into `index.data`.
5. Replaces the unsupported old GLUT bitmap-font HUD path with an HTML level/control shell for the first browser port.

## Easiest route: GitHub Actions

Create a repository containing this kit and push it. Open **Actions → Build L-Echo Web → Run workflow**. The workflow checks out upstream L-Echo, installs Emscripten, applies the patch, compiles it, and uploads a `l-echo-web` artifact containing the browser build.

## Local build

Have Emscripten active so `em++` is on PATH, then:

```bash
git clone https://github.com/LibreGamesArchive/l-echo.git
./build-web.sh ./l-echo
cd l-echo/dist
python3 serve.py
```

Open `http://localhost:8080`.

## Expected output

```text
l-echo/dist/
├── index.html
├── index.js
├── index.wasm
├── index.data
└── serve.py
```

## Controls

- Use the HTML **Level** selector above the game to change stages.
- Arrow keys: rotate the world
- `P`: start or pause
- `W`: walk
- `R`: run
- Mouse drag: rotate the world

## Notes

L-Echo is GPL-licensed upstream. If you redistribute a modified build/source, preserve the applicable GPL notices and source availability obligations.

This is a compatibility port kit, not a rewrite of the game. The intent is to keep L-Echo's original C++ gameplay and XML levels and compile them to WebAssembly.
