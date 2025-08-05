from __future__ import annotations

from typing import ClassVar

import busio
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685
from board import SCL, SDA

__all__ = ('Servo',)


class Servo:
    """Interface over a single DS3235 270-degree servo motor controlled using PCA9685."""

    I2C: ClassVar[busio.I2C | None] = None
    PCA: ClassVar[PCA9685 | None] = None
    
    def __init__(self, channel: int, *, min_pulse: int = 500, max_pulse: int = 2500) -> None:
        self.channel = channel
        self._min_pulse = min_pulse
        self._max_pulse = max_pulse

        self.prepare()
        self.inner = servo.Servo(self.PCA.channels[channel], min_pulse=min_pulse, max_pulse=max_pulse)

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
        if angle := self.inner.angle:
            return angle / 180 * 270
        return None    
    
    @angle.setter
    def angle(self, value: float) -> None:
        """Set the angle of the servo, normalized between 0 and 270 degrees."""
        if not (0 <= value <= 270):
            raise ValueError('Angle must be between 0 and 270 degrees')
        self.inner.angle = value / 270 * 180

    def __repr__(self) -> str:
        return f'Servo(channel={self.channel}, angle={self.angle})'
