import logging
import serial
from serial.tools import list_ports
import time
import socket
from zeroconf import ServiceBrowser, ServiceListener, ServiceStateChange, ServiceInfo, Zeroconf
import json
import urllib.request
import struct
import toml
from threading import Thread

log = logging.getLogger(__name__)


class DeviceNotFound(Exception):
    def __str__(self):
        return "Could not find WLED device"
class WLEDDevice():
    def __init__(self, config):
        self._wled = {}
        self._device = None
        self._leds = [[0,0,255]]
        self._config = config
        self._previous_device = config.get('previous_device')
        
        # print("Selected:")
        # print(f"{self._wled.get('info').get('name')} @ {self.ip}")
        # print(f"Mac address: {self.mac}")
        # print(f"LEDs configured: {self.led_count}")

    @property
    def config(self):
        return self._config
    
    @config.setter
    def config(self, value):
        self._config = value
        self.save()

    @property
    def ip(self):
        return self._wled.get("info").get("ip")

    @property
    def leds(self):
        return self._leds
    
    @leds.setter
    def leds(self, data):
        self._leds = data

    @property
    def previous_device(self):
        return self._previous_device
    
    @previous_device.setter
    def previous_device(self, device):
        self._previous_device = device
        self.update_config()

    @property
    def uptime(self):
        self.refresh_info()
        return self._wled.get("info").get("uptime")

    def refresh_info(self):
        pass
    
    def save(self):
        filename = "csgo_config.toml"
        with open(filename, "w") as config_file:
            toml.dump(self._config, config_file)
    
    def render(self):
        pass

    
    def send_adalight_packet(self, data):
        """
        Sends an Adalight data packet over a serial connection.
        """
        # print(data)
        if data:
            if len(data) != self.led_count:
                log.warning("Number of leds does not match the data being sent.")
                log.info(f"data: {len(data)}, leds: {self.led_count}")
            payload = bytearray()
            for color in data:
                payload += bytearray(color)
            # print(payload)
            checksum = (len(data) >> 8) ^ (len(data) & 0xff) ^ 0x55
            header = b'Ada' + len(data).to_bytes(2, 'big') + checksum.to_bytes(1, 'big')
            packet = header + payload
            print(packet)
            self._serial_connection.write(packet)

    def send_e131_packet(self, data):
        """
        Sends a packet of data to a WLED device using the E1.31 protocol.
        """
        # Create the E1.31 packet header
        header = bytearray([
            0x41, 0x53, 0x43, 0x2d, 0x45, 0x31, 0x2e, 0x31, # "ASC-E1.31"
            0x00, 0x00, 0x00, 0x01, # Universe (4 bytes, big endian)
            0x00, # Sequence number
            0x00, # Options flags
            0x00, 0x00 # Length (2 bytes, big endian)
        ])
        # Set the length of the packet
        length = len(data) * 3
        header[14] = (length >> 8) & 0xff
        header[15] = length & 0xff
        # Create the packet payload
        payload = bytearray()
        for color in data:
            payload += bytearray(color)
        # Create the packet
        packet = header + payload
        # Send the packet to the WLED device
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(packet, (self.ip, 5568))
        sock.close()

    def send_warls_packet(self, data):
        """
        Sends a packet of data to a WLED device using the WARLS protocol.
        """
        if data:
            # Create the WARLS packet header
            header = bytearray([
                0x02, # "1 - WARLS, 2 - DRGB"
                0x01, # Revert afer X seconds of no data
            ])
            # Create the packet payload
            payload = bytearray()
            for color in data:
                payload += bytearray(color)
            # Create the packet
            packet = header + payload
            # Send the packet to the WLED device
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(packet, (self.ip, 21324))
            sock.close()

    def update_wled_info(self):
        '''Gets WLED state JSON'''
        if self._type == "serial":
            data = json.loads(self.get_serial_info())
        elif self._type == "wled":
            data = json.loads(self.get_wled_info())
        self._wled = data
        

    def get_serial_info(self, device = None):
        device = device or self._device
        with serial.Serial(device.device, self._baud_rate, timeout=1) as ser:
                    # Send a command to the device to get its status.
                    ser.write(b"{\"v\":true}\n")
                    return ser.readline().decode()

    

    def get_wled_serial_device(self):
        # Get a list of available serial devices.
        available_devices = list_ports.comports()
        print(available_devices)
        # Iterate over the available devices and send a command to check if they are WLED devices.
        for device in available_devices:
            try:
                response = self.get_serial_info(device)
                # If the device is a WLED device, return its info.
                print(response)
                if "WLED" in response:
                    return device
            except Exception:
                # (Handle any exceptions that may occur.)
                pass
        
        # If no WLED devices were found, return None.
        raise DeviceNotFound

    def ping_device(self, host = None):
        '''Makes a request to a WLED device to check for connectivity'''
        host = host or self._device.server
        try:
            # Make a GET request to the device's /json endpoint.
            with urllib.request.urlopen("http://{}/json".format(host)) as response:
                # If the request is successful (status code 200), return True.
                if response.getcode() == 200:
                    return True
                else:
                    return False
        except Exception:
            # If the request fails, return False.
            return False


class WLEDListener(ServiceListener):

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        print(f"Service {name} added, service info: {info}")


class WLEDSerialDevice(WLEDDevice):
    def __init__(self, config):
        super().__init__(config)
        self._serial_connection = None
        self._baud_rate = 1500000
        self._device = self.get_wled_serial_device()

        response = self.get_serial_info()
        print(response)
        try:
            self._wled = json.loads(response)
            self._serial_connection = serial.Serial(self._device.device, self._baud_rate)
            self._leds = [] * self.led_count
        except Exception:
            log.error("Could not load json from serial.")

    def render(self):
        self.send_adalight_packet(self._leds)

    def refresh_info(self):
        '''Gets WLED state JSON'''
        self._wled = json.loads(self.get_serial_info())

class WLEDNetworkDevice(WLEDDevice):
    def __init__(self, config):
        super().__init__(config)
        self._host = self.get_device()
        self._wled = json.loads(self.get_wled_info(self._host))
        self.led_count = self._wled.get("info").get("leds").get("count")
        self.stop_flag = True
        self.a_blink(3,30,[0,50,0])
        self.initilize_wled()

    def get_device(self):
        if self.previous_device:
            if self.ping_device(self.previous_device):
                log.info(f'Connected to previously used device: {self.previous_device}')
                return self.previous_device
            else:
                self.get_wled_zeroconf_device()

    def render(self):
        while not self.stop_flag:
            self.send_warls_packet(self._leds)

    def refresh_info(self):
        '''Gets WLED state JSON'''
        self._wled = json.loads(self.get_wled_info())

    def get_wled_zeroconf_device(self, timeout=5):
        devices = []
        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                info = zeroconf.get_service_info(service_type, name)
                devices.append(info)

        zc = Zeroconf()
        ServiceBrowser(zc, "_wled._tcp.local.", handlers=[on_service_state_change])

        try:
            # Wait for the specified timeout to allow the ServiceBrowser to discover devices
            socket.setdefaulttimeout(timeout)
            # start = time.perf_counter()
            end = time.perf_counter() + timeout
            log.info(f"Scanning for wled devices for {timeout} seconds...")
            while time.perf_counter() < end:
                pass
        finally:
            zc.close()

        if devices:
            for device in devices:
                log.info(f"Found: {device.server}")

        if len(devices) == 1:
            return devices[0]
        elif len(devices) > 1:
            print("Multiple WLED devices found:")
            for i, device in enumerate(devices):
                wled = json.loads(self.get_wled_info(device.server))
                print(f"{i+1}. {wled.get('info').get('name')} {device.server}")
            selection = input("Enter the number of the device you want to use: ")
            self.previous_device = device.server
            return devices[int(selection)-1].server
        else:
            raise DeviceNotFound

    def get_wled_info(self, host):
        with urllib.request.urlopen("http://{}/json".format(host)) as response:
            # If the request is successful (status code 200), return True.
            if response.getcode() == 200:
                data = response.read().decode()
        return data
    
    def send_json(self, data):
        try:
            # Set the request headers
            headers = {'Content-Type': 'application/json'}

            # Set the request data as a dictionary
            # data = {'key': 'value'}

            # Encode the data as JSON and set it as the request body
            req = urllib.request.Request("http://{}/json/state".format(self._host), data=json.dumps(data).encode('utf-8'), headers=headers)

            # Send the request and print the response
            response = urllib.request.urlopen(req)
        except Exception:
            print("Problem sending json data")

    def handle_csgo_payload(self, old={}, new=None):
        for i in new:
            if i == "player.state.flashed":
                if old.get(i) == 0 or old.get(i) is None and new.get(i) > 0:
                    self.a_flashbang(new.get(i))
                elif old.get(i) is not None and new.get(i) > old.get(i):
                    self.a_flashbang(new.get(i))

    def initilize_wled(self):
        a = {
            "bri": 40,
            "on": "true",
            #maybe transition 0? we'll see... Can also use tt instead for a single call.
            "transition": 7,
            "seg": [
                {
                    "bri": 255,
                    "fx": "0",
                    "sx": "100",
                    "on": "true",
                    "col":[[0,0,0]]
                }
            ]
        }
        self.send_json(a)

    def a_idle(self):
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
        self.send_json(a)

    def a_ct_idle(sefl):
        pass
    
    def a_t_idle(self):
        pass
    
    def a_round_start(self):
        pass

    def a_round_end(self):
        pass
    
    def a_bomb_planted(self):
        pass

    def a_fire(self):
        pass

    def a_kill(self):
        pass

    def a_ace(self):
        pass

    def a_mvp(self):
        pass

    def a_win(self):
        pass

    def a_lose(self):
        pass

    def a_blink(self, times, speed, color):
        '''Blinks a given number of times'''
        self.stop_flag = False
        sleep_time = 10/speed
        thread = Thread(target=self.render)
        thread.start()
        while times != 0:
            times -= 1
            self._leds = [[0,0,0]] * self.led_count
            time.sleep(sleep_time)
            self._leds = [color] * self.led_count
            time.sleep(sleep_time)
        self.stop_flag = True
        thread.join()
    
    def a_flashbang(self, start_intensity, duration=.5):
        '''Start a simulated flashbang at the intensity given that lasts for duration.'''
        # Could not find a good way to do flashbang with built-in WLED animations
        # so this drives the leds manually.
        value = start_intensity
        tick = duration / value
        self._leds = [[value,value,value]] * self.led_count
        self.stop_flag = False
        thread = Thread(target=self.render)
        thread.start()
        while value > 0:
            value -= 1
            self._leds = [[value,value,value]] * self.led_count
            time.sleep(tick)
        self.stop_flag = True
        thread.join()