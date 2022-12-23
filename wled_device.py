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

log = logging.getLogger(__name__)

class WLEDDevice():
    def __init__(self, config):
        self._wled = None
        self._type = None
        self._leds = [(0,255,0)] * 30
        self._config = config
        self._serial_connection = None
        self._baud_rate = 115200
        self._previous_device = config.get('previous_device')
        # Try to get a serial device first.
        d = get_wled_serial_device()
        if d:
            self._type = "serial"
        else:
            d = self.get_wled_zeroconf_device()
            if d:
                self._type = "wled"
            else:
                log.error("Could not find WLED device.")
                exit()

        if self._type == "serial":
            # Load info from serial device
            response = get_serial_info(d)
            print(response)
            try:
                self._wled = json.loads(response)
                self._serial_connection = serial.Serial(d.device, self._baud_rate)
                self._leds = [] * self.led_count
            except Exception:
                log.error("Could not load json from serial.")
        else:
            # Load info from wled json endpoint
            self._wled = json.loads(get_wled_info(d))
            pass
        
        print("Selected:")
        print(f"{self.name} @ {self.ip}")
        print(f"Mac address: {self.mac}")
        print(f"LEDs configured: {self.led_count}")

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
    def led_count(self):
        return self._wled.get("info").get("leds").get("count")

    @property
    def mac(self):
        return self._wled.get("info").get("mac")
    
    @property
    def name(self):
        return self._wled.get("info").get("name")

    @property
    def previous_device(self):
        return self._previous_device
    
    @previous_device.setter
    def previous_device(self, device):
        self._previous_device = device
        self.update_config()

    @property
    def uptime(self):
        return self._wled.get("info").get("uptime")
    
    def save(self):
        filename = "csgo_config.toml"
        with open(filename, "w") as config_file:
            toml.dump(self._config, config_file)
    
    def render(self):
        if self._type == "serial":
            self.send_adalight_packet(self._leds)
        elif self._type == "wled":
            self.send_warls_packet(self._leds)
        else:
            log.error("Unknown device type. Can't update leds.")

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
            if self.previous_device:
                for device in devices:
                    if device.server == self.previous_device:
                        return device
            print("Multiple WLED devices found:")
            for i, device in enumerate(devices):
                wled = json.loads(get_wled_info(device))
                print(f"{i+1}. {wled.get('info').get('name')} {device.server}")
            selection = input("Enter the number of the device you want to use: ")
            self.previous_device = device.server
            return devices[int(selection)-1]
        else:
            return None
    
    def send_adalight_packet(self, data):
        """
        Sends an Adalight data packet over a serial connection.
        """
        # print(data)
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
        # print(packet)
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

        # print(self._leds)


class WLEDListener(ServiceListener):

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        print(f"Service {name} added, service info: {info}")

def ping_device(host):
    '''Makes a request to a WLED device to check for connectivity'''
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

def get_wled_info(device):
    '''Gets WLED state JSON'''
    host = device
    data = None
    if isinstance(device, ServiceInfo):
        host = device.server
    # Make a GET request to the device's /json endpoint.
    with urllib.request.urlopen("http://{}/json".format(host)) as response:
        # If the request is successful (status code 200), return True.
        if response.getcode() == 200:
            data = response.read().decode()
    return data

def get_serial_info(device):
    with serial.Serial(device.device, 115200, timeout=1) as ser:
                # Send a command to the device to get its status.
                ser.write(b"{\"v\":true}\n")
                return ser.readline().decode()

def get_wled_serial_device():
    # Get a list of available serial devices.
    available_devices = list_ports.comports()
    # Iterate over the available devices and send a command to check if they are WLED devices.
    for device in available_devices:
        try:
            response = get_serial_info(device)
            # If the device is a WLED device, return its info.
            if "WLED" in response:
                return device
        except Exception:
            # (Handle any exceptions that may occur.)
            pass
    
    # If no WLED devices were found, return None.
    return None



