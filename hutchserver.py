from wled_device import WLEDNetworkDevice
import logging
from server import GSIServer
import toml
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
framerate = 30

def get_config():
    config = None
    try:
        with open("csgo_config.toml", "r") as config_file:
            config = toml.load(config_file)
    except FileNotFoundError:
        config = {
            "fps": 30,
            "wled_devices": {}
        }
        with open("csgo_config.toml", "w") as config_file:
            toml.dump(config, config_file)
    return config


class Animation():
    def __init__(self, device):
        self.device = device
    
    def send(self, payload):
        self.device.send_json(payload)

    def idle(self):
        a = {
            "bri": 40,
            "seg": [
                {
                    "fx": "0",
                    "sx": "100",
                    "col":[[0,200,200]]
                }
            ]
        }
        self.send(a)


def handle_changes(changes, old_state, device):
    a = Animation(device)
    print(changes)
    if changes.get('player',{}).get('state', {}).get('flashed', 0) > 0:
        print("hmm")
        if not old_state['player']['state']['flashed']:
            a.flashbang(changes.get('player').get('state').get('flashed'))
        a.flashbang(changes.get('player').get('state').get('flashed'))

def main():
    mywled = WLEDNetworkDevice(get_config())
    server = GSIServer(("127.0.0.1", 3000), "MYTOKENHERE", mywled.handle_csgo_payload)
    server.start_server()
    while server.running:
        time.sleep(1)

if __name__ == "__main__":
    main()