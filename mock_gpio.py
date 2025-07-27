from __future__ import annotations

__all__ = ('Button', 'Device', 'RPiGPIOFactory', 'LCDDisplay')


class Button:
    when_pressed = None
    when_released = None
    on_press = None
    on_release = None
    
    def __init__(self, pin: int, pull_up: bool = True) -> None:
        self.pin = pin
        self.pull_up = pull_up


class Device:
    pin_factory = None
    
    
class RPiGPIOFactory:
    pass


class LCDDisplay:
    def __init__(self, addr: int = 0x27, *, backlight_enabled: bool = True):
        self.addr: int = addr
        self.backlight_enabled: bool = backlight_enabled

    def clear(self) -> None:
        pass
    
    def openlight(self) -> None:  # Enable the backlight
        pass

    def write_top(self, text: str, *, offset_left: int = 0) -> None:
        pass

    def write_bottom(self, text: str, *, offset_left: int = 0) -> None:
        pass

    def write(self, text: str, bottom_text: str | None = None, *, offset_left: int = 0) -> None:
        pass
