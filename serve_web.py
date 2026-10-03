"""
Super-fast local server for Recoil Wing Web / Mobile testing.
Serves pre-cached WebAssembly assets locally with zero internet delay.
"""
import http.server
import socketserver
import mimetypes
import sys

PORT = 8000
DIRECTORY = "build/web"

mimetypes.init()
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("application/octet-stream", ".data")
mimetypes.add_type("application/octet-stream", ".apk")
mimetypes.add_type("text/javascript", ".js")


class FastWebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Content-Disposition", "inline")
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # Client refreshed or aborted connection, safe to ignore

    def log_message(self, format, *args):
        # Concise logging for mobile and desktop requests
        sys.stdout.write(f"[RecoilServer] {args[0]} - {args[1]}\n")
        sys.stdout.flush()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), FastWebHandler) as httpd:
        print(f"=======================================================")
        print(f"  RECOIL WING ULTRA-FAST LOCAL WEB SERVER ACTIVE!     ")
        print(f"  PC Localhost  : http://localhost:{PORT}            ")
        print(f"  HP Android    : http://192.168.1.6:{PORT}           ")
        print(f"  All WASM & Python assets are SERVED 100% LOCALLY!   ")
        print(f"=======================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
