"""Mock GPIO devices for simulating controller messages through MQTT without needing a GPIO connection."""

from __future__ import annotations

from threading import Thread

from .stepper import Direction

__all__ = ('Button', 'Device', 'RPiGPIOFactory', 'LCDDisplay', 'Stepper', 'Nema17Stepper', 'Servo')


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
    
    
class OutputDevice:
    def __init__(self, pin: int) -> None:
        self.pin = pin
        self.value = False  # Simulate the output state

    @property
    def value(self) -> bool:
        return self._value

    @value.setter
    def value(self, val: bool) -> None:
        self._value = val
    

class Stepper:
    def __init__(
        self,
        *pins: int,
        seq: list[list[int]] | None = None,
        steps_per_revolution: int = 200,
        delay: float = 0.001,
        accel_steps: int = 100,
        max_delay: float = 0.007,
        direction: Direction = Direction.ccw,
    ) -> None:
        self.pins: list[OutputDevice] = [OutputDevice(pin) for pin in pins]
        self.seq = seq

        self.steps: int = -1
        self.target: int | None = None
        self.direction: Direction = direction

        self.steps_per_revolution = steps_per_revolution
        self.accel_steps: int = max(1, accel_steps)
        self.delay = delay
        self._max_delay = max_delay

        self._worker: Thread | None = None
        self._worker_keepalive: bool = False
        self._worker_busy: bool = False

    @property
    def delay(self) -> int:
        return self._delay

    @delay.setter
    def delay(self, value: float) -> None:
        if value < 0:
            raise ValueError('Delay must be non-negative')
        self._delay = value

    @property
    def is_busy(self) -> bool:
        return (
            self._worker is not None
            and self._worker.is_alive()
            and self._worker_busy
        )

    def wait(self) -> None:
        """Waits for the stepper to finish its current operation."""
        while self.is_busy:
            pass

    def step(self) -> None:
        self.steps += self.direction.value

    def start(self) -> None:
        """Starts the stepper motor update loop in a separate thread."""
        if self._worker is not None and self._worker.is_alive():
            raise RuntimeError('MOCK Stepper motor is already running')

        self._worker_keepalive = True
        self._worker = Thread(target=self.loop, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        if self._worker is None or not self._worker.is_alive():
            raise RuntimeError('MOCK Stepper motor is not running')

        self.target = None
        self._worker_keepalive = False
        self._worker.join()
        self._worker = None
        self.steps = -1

    def loop(self) -> None:
        while self._worker_keepalive:
            pass

    def __enter__(self) -> Stepper:
        return self

    def __exit__(self, *_) -> None:
        pass


class Nema17Stepper(Stepper):
    pass


class Servo:
    def __init__(self, *args, **kwargs) -> None:
        pass
    
    @property
    def angle(self) -> float | None:
        return 0.0
    
    @angle.setter
    def angle(self, value: float) -> None:
        if not (0 <= value <= 270):
            raise ValueError('Angle must be between 0 and 270 degrees')
