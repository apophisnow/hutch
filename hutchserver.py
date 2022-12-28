from wled_device import WLEDNetworkDevice
import logging
from server import GSIServer
import toml
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def get_config():
    config = None
    try:
        with open("csgo_config.toml", "r") as config_file:
            config = toml.load(config_file)
    except FileNotFoundError:
        config = {"version": "1.0.0"}
        with open("csgo_config.toml", "w") as config_file:
            toml.dump(config, config_file)
    return config

def main():
    mywled = WLEDNetworkDevice(get_config())
    server = GSIServer(("127.0.0.1", 3000), "MYTOKENHERE", mywled.handle_csgo_payload)
    server.start_server()
    while server.running:
        time.sleep(1)
    server.shutdown()

if __name__ == "__main__":
    main()