from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import json
import logging
import time

log = logging.getLogger(__name__)

def flatten_dict(d):
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            value = flatten_dict(value)
            for subkey, subvalue in value.items():
                result[key + '.' + subkey] = subvalue
        else:
            result[key] = value
    return result


class GSIServer(HTTPServer):
    def __init__(self, server_address, auth_token, callback):
        super(GSIServer, self).__init__(server_address, RequestHandler)
        self.auth_token = auth_token
        self.gamestate = None
        self.callback = callback
        self.running = False

    def start_server(self):
        try:
            thread = Thread(target=self.serve_forever)
            thread.start()
            first_time = True
            while self.running == False:
                if first_time == True:
                    log.info("CS:GO GSI Server starting..")
                first_time = False
                # Small sleep to reduce high cpu while waiting on first request to come through.
                time.sleep(.1)
        except:
            log.exception("Could not start server.")

    def compare_game_state(self, new_game_state):
        old_game_state = self.gamestate
        self.gamestate = new_game_state
        changes = []
        # Define a helper function to compare the dictionaries at the specified keys
        def compare_dicts(old_dict, new_dict, keys):
            # Check for new attributes in the new dictionary
            new_keys = set(new_dict.keys()) - set(keys)
            for key in new_keys:
                changes.append({key: new_dict[key]})
            for key in keys:
                # Check if the value at the key is a dictionary
                if isinstance(old_dict.get(key), dict) and isinstance(new_dict.get(key), dict):
                    # Recursively call the helper function to compare the nested dictionaries
                    compare_dicts(old_dict[key], new_dict[key], old_dict[key].keys())
                else:
                    # Compare the values for the key
                    old_value = old_dict.get(key, None)
                    new_value = new_dict.get(key, None)
                    if old_value != new_value and new_value is not None:
                        changes.append({key: new_value})
        compare_dicts(old_game_state, new_game_state, old_game_state.keys())
        if changes:
            return changes


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length).decode("utf-8")

        payload = json.loads(body)
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if not self.authenticate_payload(payload):
            log.warning("auth_token does not match.")
            return False
        else:
            self.server.running = True
        del payload["auth"]
        if self.server.gamestate:
            self.server.callback(old=flatten_dict(self.server.gamestate), new=flatten_dict(payload))
        else:
            self.server.callback(new=flatten_dict(payload))
        self.server.gamestate = (flatten_dict(payload))
        
    def authenticate_payload(self, payload):
        if "auth" in payload and "token" in payload["auth"]:
            return payload["auth"]["token"] == self.server.auth_token
        else:
            return False

    def log_message(self, format, *args):
        """
        Prevents requests from printing into the console
        """
        return
