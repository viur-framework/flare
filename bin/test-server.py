#!/usr/bin/env python3
import os
import socketserver
from http.server import SimpleHTTPRequestHandler

class pyodideHttpServer(SimpleHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        self.extensions_map.update({
            '.wasm': 'application/wasm',
        })

        super().__init__(request, client_address, server)

    def end_headers(self):
        #self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

port = 8080
Handler = pyodideHttpServer

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", port), Handler) as httpd:
    print("http://localhost:%d" % port)
    httpd.allow_reuse_address = True
    httpd.serve_forever()
