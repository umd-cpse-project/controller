from __future__ import annotations

from threading import Thread
from time import sleep

from gpiozero import OutputDevice

__all__ = ('Stepper',)

_IN1, _IN2, _IN3, _IN4 = 12, 16, 8, 10


class Stepper:
    def __init__(self, *pins: int, seq: list[list[int]] | None = None, steps_per_revolution: int = 2048) -> None:
        if not pins:
            pins = _IN1, _IN3, _IN2, _IN4
            
        count = len(pins)
        assert count == 4, 'only 4-pin steppers are supported'
        self.pins: list[OutputDevice] = [OutputDevice(pin) for pin in pins]

        if seq is None:
            seq = [[int(i == j) for j in range(count)] for i in range(count)]
        self.seq = seq
        
        self.steps: int = 0
        self.steps_per_revolution = steps_per_revolution

    def step(self, *, cw: bool = False) -> None:
        """Performs one single step."""
        self.steps += -1 if cw else 1
        configuration = self.seq[self.steps % len(self.seq)]
        
        for pin, value in zip(self.pins, configuration):
            pin.value = value
            
    def step_n(self, n: int, *, cw: bool = False, step_delay: float = 0.001) -> None:
        """Performs n steps in the specified direction with the specified step delay."""
        for _ in range(n):
            self.step(cw=cw)
            sleep(step_delay)
            

if __name__ == '__main__':
    # Example usage
    stepper = Stepper(_IN1, _IN2, _IN3, _IN4)
    
    stepper.step_n(1000, cw=True)
