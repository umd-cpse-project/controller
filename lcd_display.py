import time
from logging import getLogger

import smbus2 as smbus

log = getLogger(__name__)


class LCDDisplay:
    """A class to control a 16x2 LCD display using I2C protocol."""
    
    def __init__(self, addr: int = 0x27, *, backlight_enabled: bool = True):
        self.addr: int = addr
        self.backlight_enabled: bool = backlight_enabled
        self.bus: smbus.SMBus = smbus.SMBus(1)
        try:
            self.setup()
        except Exception as exc:
            log.error(f"Failed to initialize LCD display at address {addr}: {exc}")
            raise RuntimeError(f"LCD initialization failed: {exc}") from exc
        else:
            log.info(
                f"LCD display initialized at address {addr} "
                f"with backlight {'on' if self.backlight_enabled else 'off'}"
            )

    def setup(self) -> None:      
        self.send_command(0x33)  # Must initialize to 8-line mode at first
        time.sleep(0.005)
        self.send_command(0x32)  # Then initialize to 4-line mode
        time.sleep(0.005)
        self.send_command(0x28)  # 2 lines & 5*7 dots
        time.sleep(0.005)
        self.send_command(0x0C)  # Enable display without cursor
        time.sleep(0.005)
        self.send_command(0x01)  # Clear sreen
        self.bus.write_byte(self.addr, 0x08)
        
    def write_word(self, data):
        temp = data
        if self.backlight_enabled:
            temp |= 0x08
        else:
            temp &= 0xF7
        self.bus.write_byte(self.addr, temp)

    def send_command(self, cmd: int):
        # Send bit7-4 firstly
        buf = cmd & 0xF0
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.write_word(buf)
    
        # Send bit3-0 secondly
        buf = (cmd & 0x0F) << 4
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.write_word(buf)
    
    
    def send_data(self, data):
        # Send bit7-4 firstly
        buf = data & 0xF0
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.write_word(buf)
    
        # Send bit3-0 secondly
        buf = (data & 0x0F) << 4
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.write_word(buf)

    def clear(self) -> None:
        self.send_command(0x01)  # Clear Screen
    
    def openlight(self) -> None:  # Enable the backlight
        self.bus.write_byte(0x27, 0x08)
        self.bus.close()

    def write(self, x: int, y: int, text: str) -> None:
        if x < 0:
            x = 0
        if x > 15:
            x = 15
        if y < 0:
            y = 0
        if y > 1:
            y = 1
    
        # Move cursor
        addr = 0x80 + 0x40 * y + x
        self.send_command(addr)
    
        for char in text:
            self.send_data(ord(char))


if __name__ == '__main__':
    display = LCDDisplay(0x27)
    display.write(4, 0, 'Hello')
    display.write(7, 1, 'world!')
