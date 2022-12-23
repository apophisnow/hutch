import toml
from wled_device import WLEDDevice
import logging
import time
import threading

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

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

def update_leds_thread(ledupdate, framerate):
    """
    A thread function that sends Adalight packets to update the LED colors at a fixed framerate.
    """
    while True:
        ledupdate()
        time.sleep(1 / framerate)

def flashbang(device, hold_time = 1, fade_duration = 1):
    # Set the LEDs to full white
    device.leds = [(255, 255, 255)] * device.led_count
    
    # Wait for the specified hold time
    time.sleep(hold_time)
    
    # Fade the LEDs to black over the specified duration
    for i in range(255):
        device.leds = [(255 - i, 255 - i, 255 - i)] * device.led_count
        time.sleep(fade_duration / 255)


def main():
    config = get_config()
    # print(config)
    # device, device_type = load_device(config)
    # print(f"Got device: {device} of type: {device_type}")

    mywled = WLEDDevice(config)

    t = threading.Thread(target=update_leds_thread, args=(mywled.render,30))
    t.start()

    while True:
        flashbang(mywled, .5, 3)
        time.sleep(5)
    # server = MyServer(('localhost', 3000), 'MYTOKENHERE', MyRequestHandler)

    # logger.info('{} - CS:GO GSI Quick Start server starting'.format(time.asctime()))

    # try:
    #     server.serve_forever()
    # except (KeyboardInterrupt, SystemExit):
    #     pass

    # server.server_close()
    # logger.info('{} - CS:GO GSI Quick Start server stopped'.format(time.asctime()))


if __name__ == "__main__":
    main()