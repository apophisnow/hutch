from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
import time
import json
import os
import logging
import serial
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

arduino = serial.Serial('COM5', 9600, timeout=.1)
time.sleep(5)
arduino.write(b'A3\n')

class MyServer(HTTPServer):
    def __init__(self, server_address, token, RequestHandler):
        self.auth_token = token

        super(MyServer, self).__init__(server_address, RequestHandler)

        # You can store states over multiple requests in the server 
        self.previous_payload = None


class MyRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length).decode('utf-8')
        #print(self.headers)
        #print(body)
        self.parse_payload(json.loads(body))

        self.send_header('Content-type', 'text/html')
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_header('Content-type', 'text/html')
        self.send_response(200)
        self.end_headers()

    def valid_payload(self, payload):
        if 'auth' in payload and 'token' in payload['auth']:
            return payload['auth']['token'] == server.auth_token
        else:
            return False

    def parse_payload(self, payload):
        # Ignore unauthenticated payloads
        if not self.valid_payload(payload):
            return None
            
        if self.server.previous_payload:
            changed_state = { key:val for key, val in payload.items() if val != self.server.previous_payload.get(key) }
            if changed_state:
                logger.info(changed_state)
                # Need to make better organized functions for various animations/states
                if changed_state.get('player',{}).get('state', {}).get('flashed', 0) > 0:
                    print(f'Flashed!!! = ', changed_state['player']['state']['flashed'])
                    flash = changed_state['player']['state']['flashed']
                    cmd = bytes(f'A2 {flash}\n','utf-8')
                    arduino.write(cmd)
        self.server.previous_payload = payload

    def log_message(self, format, *args):
        """
        Prevents requests from logger.infoing into the console
        """
        return


server = MyServer(('localhost', 3000), 'MYTOKENHERE', MyRequestHandler)

logger.info('{} - CS:GO GSI Quick Start server starting'.format(time.asctime()))

try:
    server.serve_forever()
except (KeyboardInterrupt, SystemExit):
    pass

server.server_close()
logger.info('{} - CS:GO GSI Quick Start server stopped'.format(time.asctime()))
