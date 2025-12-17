#!/usr/bin/env python3
"""
Development server for lingo js pages
"""


import socketserver
import threading
import os
import json
import yaml

import http.server

from urllib.parse import unquote

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, 'src')
INDEX_PATH = os.path.join(SRC_DIR, 'index.html')
SPEC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '../../src/mspec/data'))

class DevRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        
		#
        # serve index
        #
        
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            
            with open(INDEX_PATH, 'rb') as f:
                try:
                    self.wfile.write(f.read())
                except BrokenPipeError as e:
                    print(f'Client disconnected before full response was sent: {e}')
                
            return
        
        if self.path.endswith('.js'):
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            
            js_path = os.path.join(SRC_DIR, self.path.lstrip('/'))
            with open(js_path, 'rb') as f:
                self.wfile.write(f.read())
            return
        
        if self.path.startswith('/api/lingo-specs'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()

            pages_dir = os.path.join(SPEC_DIR, 'lingo/pages')
            pages_rel_dir = 'data/lingo/pages/'
            lingo_pages = [os.path.join(pages_rel_dir, f) for f in os.listdir(pages_dir)]

            scripts_dir = os.path.join(SPEC_DIR, 'lingo/scripts')
            scripts_rel_dir = 'data/lingo/scripts/'
            lingo_scripts = [os.path.join(scripts_rel_dir, f) for f in os.listdir(scripts_dir)]
            
            response = {
                'pages': lingo_pages,
                'scripts': lingo_scripts
            }

            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
        
		#
        # serve lingo examples
        #
        
        if self.path.startswith('/data/'):
            rel_path = unquote(self.path[len('/data/'):])
            abs_path = os.path.join(SPEC_DIR, rel_path)
            
            if os.path.commonpath([abs_path, SPEC_DIR]) != SPEC_DIR or not os.path.exists(abs_path):
                self.send_error(404, 'File not found')
                return
            
            if os.path.isdir(abs_path):
                self.send_error(403, 'Directory listing not allowed')
                return
            
            # Check if it's a YAML file and convert to JSON
            if abs_path.endswith('.yaml') or abs_path.endswith('.yml'):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
                self.end_headers()
                
                with open(abs_path, 'r') as f:
                    yaml_data = yaml.safe_load(f)
                    self.wfile.write(json.dumps(yaml_data).encode('utf-8'))
                return
            
            self.send_response(200)
            mime = self.guess_type(abs_path)
            self.send_header('Content-type', mime)
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            
            with open(abs_path, 'rb') as f:
                self.wfile.write(f.read())
            return
        
        else:
            self.send_error(404, 'Not found')
            return

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run a development server for lingo js pages.')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    parser.add_argument('--max-threads', type=int, default=0, help='Maximum number of threads (0 = unlimited, default: 0)')
    args = parser.parse_args()
    port = args.port
    max_threads = args.max_threads

    # Custom thread-limited server if max_threads > 0
    if max_threads > 0:
        class LimitedThreadingTCPServer(socketserver.ThreadingTCPServer):
            def __init__(self, server_address, RequestHandlerClass):
                super().__init__(server_address, RequestHandlerClass)
                self._thread_semaphore = threading.BoundedSemaphore(max_threads)

            def process_request(self, request, client_address):
                self._thread_semaphore.acquire()
                try:
                    super().process_request(request, client_address)
                finally:
                    self._thread_semaphore.release()

        ServerClass = LimitedThreadingTCPServer
    else:
        ServerClass = socketserver.ThreadingTCPServer

    with ServerClass(('', port), DevRequestHandler) as httpd:
        print(f'Dev server running at http://localhost:{port}/ (threads: {"unlimited" if max_threads == 0 else max_threads})')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.server_close()