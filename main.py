import json
import socket
import threading
import datetime
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes

UDP_IP = 'localhost'
UDP_PORT = 5000
HTTP_PORT = 3000
STORAGE_DIR = pathlib.Path('./storage')
STORAGE_FILE = STORAGE_DIR / 'data.json'


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        
        # send data_dict to UDP sever
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            print(json.dumps(data_dict).encode())
            sock.sendto(json.dumps(data_dict).encode(), (UDP_IP, UDP_PORT))

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('0.0.0.0', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_udp_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)

    try:
        while True:
            data, address = sock.recvfrom(1024)
            data_dict = json.loads(data.decode())
            
            # Write data into file
            if not STORAGE_DIR.exists():
                STORAGE_DIR.mkdir(parents=True)
            if not STORAGE_FILE.exists():
                STORAGE_FILE.write_text('{}')
            
            with STORAGE_FILE.open('r+') as f:
                content = json.load(f)
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                content[timestamp] = data_dict
                f.seek(0)
                json.dump(content, f, indent=4)
                f.truncate()
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()


if __name__ == '__main__':
    threading.Thread(target=run_http_server).start()
    threading.Thread(target=run_udp_server, args=(UDP_IP, UDP_PORT)).start()