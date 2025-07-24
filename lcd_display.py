import threading
import time
from logging import getLogger
from textwrap import wrap

import smbus2 as smbus

log = getLogger(__name__)


class LCDDisplay:
    """A class to control a 16x2 LCD display using I2C protocol."""
    
    def __init__(self, addr: int = 0x27, *, backlight_enabled: bool = True):
        self.addr: int = addr
        self.backlight_enabled: bool = backlight_enabled
        self.bus: smbus.SMBus = smbus.SMBus(1)
        self._tlock = threading.Lock()
        self._block = threading.Lock()
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
        
    def write_word(self, data: int) -> None:
        if self.backlight_enabled:
            data |= 0x08
        else:
            data &= 0xF7
        self.bus.write_byte(self.addr, data)

    def send_command(self, cmd: int) -> None:
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

    def send_data(self, data: int) -> None:
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

    def _write(self, text: str, x: int, y: int) -> None:
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

    def write_top(self, text: str, *, offset_left: int = 0) -> None:
        with self._tlock:
            self._write(text, offset_left, 0)
        
    def write_bottom(self, text: str, *, offset_left: int = 0) -> None:
        with self._block:
            self._write(text, offset_left, 1)
        
    def write(self, text: str, bottom_text: str | None = None, *, offset_left: int = 0) -> None:
        """Write text to the LCD display, wrapping if necessary."""
        self.clear()
        width = 16 - offset_left
        lines = wrap(text, width)
        if len(lines) > 2:
            lines = lines[:2]
        elif len(lines) == 1:
            if bottom_text is None:
                self.write_top(lines[0], offset_left=offset_left)
                return
            else:
                lines.append(bottom_text)

        top, bottom = lines
        self.write_top(top, offset_left=offset_left)
        self.write_bottom(bottom, offset_left=offset_left)


if __name__ == '__main__':
    display = LCDDisplay(0x27)
    display.write('Hello, world')
