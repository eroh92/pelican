from __future__ import print_function

import argparse

try:
    import SimpleHTTPServer as srvmod
except ImportError:
    import http.server as srvmod

try:
    import SocketServer as socketserver
except ImportError:
    import socketserver

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch a pelican server")
    parser.add_argument('-p', '--port', default=8000, type=int,
                        help="port for pelican server")
    args = parser.parse_args()
    PORT = args.port
    Handler = srvmod.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), Handler)
    print("serving at port", PORT)
    httpd.serve_forever()

