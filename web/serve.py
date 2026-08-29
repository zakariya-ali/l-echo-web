#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
    }

print("Serving L-Echo Web at http://localhost:8080")
ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
