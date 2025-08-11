from __future__ import annotations

from typing import ClassVar

import busio
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685
from board import SCL, SDA

__all__ = ('Servo',)


class Servo:
    """Interface over a single DS3235 270-degree servo motor controlled using PCA9685.
    
    Parameters
    ----------
    channel: int
        The channel number of the servo on the PCA9685 board (0-15).
    actuation_range: int
        The range of motion for the servo in degrees. Default is 270 degrees.
    min_pulse: int
        The minimum pulse width in microseconds for the PWM-controlled servo. Default is 500 us.
    max_pulse: int
        The maximum pulse width in microseconds for the PWM-controlled servo. Default is 2500 us.
    """

    __slots__ = ('channel', 'inner')

    I2C: ClassVar[busio.I2C | None] = None
    PCA: ClassVar[PCA9685 | None] = None
    
    def __init__(
        self,
        channel: int,
        *,
        actuation_range: int = 270,
        min_pulse: int = 500,
        max_pulse: int = 2500,
    ) -> None:
        self.prepare()
        self.channel = channel
        self.inner = servo.Servo(
            self.PCA.channels[channel],
            actuation_range=actuation_range,
            min_pulse=min_pulse, max_pulse=max_pulse,
        )

    @classmethod
    def prepare(cls) -> None:
        """Prepare the I2C interface and PCA9685 instance."""
        if cls.I2C is None:
            cls.I2C = busio.I2C(SCL, SDA)
        if cls.PCA is None:
            cls.PCA = PCA9685(cls.I2C)
            cls.PCA.frequency = 50  # 20 ms period for servo control

    @property
    def angle(self) -> float | None:
        """Get the current angle of the servo, normalized between 0 and 270 degrees."""
        return self.inner.angle
    
    @angle.setter
    def angle(self, value: float) -> None:
        """Set the angle of the servo, normalized between 0 and 270 degrees."""
        self.inner.angle = value

    def __repr__(self) -> str:
        return f'Servo(channel={self.channel}, angle={self.angle})'


if __name__ == '__main__':
    servo_motor = Servo(0)
    servo_motor.angle = 90
    print(servo_motor.angle)
