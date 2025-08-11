from __future__ import annotations

from enum import Enum
from threading import Thread
from time import sleep

from gpiozero import OutputDevice
from gpiozero.pins.rpigpio import RPiGPIOFactory

__all__ = ('Stepper', 'Direction')

STEPPER_PIN_FACTORY = RPiGPIOFactory()


class Direction(Enum):
    cw = -1  # Clockwise
    ccw = 1  # Counter-clockwise


class Stepper:
    """Interface over a single stepper motor.
    
    Parameters
    ----------
    *pins: int
        The GPIO pins connected to the stepper motor.
    seq: list[list[int]] | None
        The sequence of steps to perform. If None, a default sequence is used.
    steps_per_revolution: int
        The number of steps per revolution for the stepper motor.
    delay: float
        The starting delay between steps, in seconds.
    accel_steps: int
        The number of steps to speed up before reaching full speed.
    max_delay: float
        The base delay to use when speeding up, in seconds.
    direction: Direction
        The direction the stepper motor should turn (for continuous mode).
    """
    
    __slots__ = (
        'pins',
        'seq',
        'steps',
        'target',
        'steps_per_revolution',
        'accel_steps',
        '_delay',
        '_max_delay',
        'direction',
        '_worker',
        '_worker_keepalive',
        '_worker_busy',
    )
    
    _delay: float
    
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
        count = len(pins)
        assert count == 4, 'only 4-pin steppers are supported'
        self.pins: list[OutputDevice] = [
            OutputDevice(pin, pin_factory=STEPPER_PIN_FACTORY) for pin in pins
        ]

        if seq is None:
            seq = [[int(i == j) for j in range(count)] for i in range(count)]
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
        """The delay between steps, in seconds."""
        return self._delay
    
    @delay.setter
    def delay(self, value: float) -> None:
        """Sets the delay between steps."""
        if value < 0:
            raise ValueError('Delay must be non-negative')
        self._delay = value
        
    @property
    def is_busy(self) -> bool:
        """Returns whether the stepper motor is currently busy."""
        return (
            self._worker is not None 
            and self._worker.is_alive() 
            and self._worker_busy
        )

    def wait(self) -> None:
        """Waits for the stepper to finish its current operation."""
        while self.is_busy:
            sleep(0.1)

    def step(self) -> None:
        """Performs one single step."""
        self.steps += self.direction.value
        configuration = self.seq[self.steps % len(self.seq)]
        
        for pin, value in zip(self.pins, configuration):
            pin.value = value
            
    def start(self) -> None:
        """Starts the stepper motor update loop in a separate thread."""
        if self._worker is not None and self._worker.is_alive():
            raise RuntimeError('Stepper motor is already running')
        
        self._worker_keepalive = True
        self._worker = Thread(target=self.loop, daemon=True)
        self._worker.start()
        
    def stop(self) -> None:
        """Gracefully stops the stepper motor update loop."""
        if self._worker is None or not self._worker.is_alive():
            raise RuntimeError('Stepper motor is not running')
        
        self.target = None
        self._worker_keepalive = False
        self._worker.join()
        self._worker = None
        self.steps = -1
            
    def loop(self) -> None:
        """Continuously runs the motor until stopped."""
        current_delay = self._max_delay
        delay_step = (current_delay - self.delay) / self.accel_steps
        
        while self._worker_keepalive:
            if self.target is None:
                self._worker_busy = True
                # Continuous mode
                if current_delay > self.delay:
                    current_delay -= delay_step
                else:
                    current_delay = self.delay
                self.step()
                sleep(current_delay)
                continue
                
            # Target mode
            remaining = self.target - self.steps
            if remaining == 0:
                self._worker_busy = False
                sleep(self.delay)
                continue
            
            self._worker_busy = True
            self.direction = (
                Direction.ccw if remaining > 0 else Direction.cw
            )
            remaining = abs(remaining)
            
            for i in range(remaining):
                if i < self.accel_steps:
                    current_delay -= delay_step
                elif i > remaining - self.accel_steps:
                    current_delay += delay_step
                else:
                    current_delay = self.delay
                    
                current_delay = max(self.delay, current_delay)
                self.step()
                sleep(current_delay)
                
    def __enter__(self) -> Stepper:
        self.start()
        return self
    
    def __exit__(self, *_) -> None:
        self.stop()
        
    def __repr__(self) -> str:
        return f'<Stepper pins={self.pins} steps={self.steps}>'


class Nema17Stepper(Stepper):
    """A specific implementation of Stepper for a Nema 17 stepper motor."""
    
    def __init__(self, *pins: int, **kwargs) -> None:
        super().__init__(
            *pins,
            seq=[
                [1, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 1, 1],
                [1, 0, 0, 1],
            ],
            steps_per_revolution=200,
            **kwargs,
        )


if __name__ == '__main__':
    with Nema17Stepper(23, 24, 25, 12) as stepper:
        stepper.target = 2000
        stepper.wait()
