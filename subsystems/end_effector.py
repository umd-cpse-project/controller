from __future__ import annotations

from devices import Servo


class EndEffector:
    """Abstraction over a differential-driven 2DOF end effector (pitch and roll).
    
    Parameters
    ----------
    left_servo: Servo
        The driver for the servo on the left, in the perspective of the board (the servo facing you).
    right_servo: Servo
        The driver for the servo on the right, in the perspective of the board (the servo further away from you).
    """

    __slots__ = (
        "_left_servo", "_right_servo",
        "_pitch", "_roll",
    )

    def __init__(
        self,
        left_servo: Servo,
        right_servo: Servo,
    ) -> None:
        self._left_servo: Servo = left_servo
        self._right_servo: Servo = right_servo
        
        self._pitch = 0.0
        self._roll = 0.0
        self._apply()

    def _clamp_servo(self, angle: float) -> float:
        """Clamp a servo angle to physical limits."""
        return max(0, min(self._left_servo.inner.actuation_range, angle))

    def _apply(self) -> None:
        """Send the current pitch/roll values to the servos."""
        self._left_servo.angle = self._clamp_servo(self.pitch + self.roll)
        self._right_servo.angle = self._clamp_servo(self.pitch - self.roll)

    @property
    def pitch(self) -> float:
        """Pitch in degrees."""
        return self._pitch

    @pitch.setter
    def pitch(self, value: float) -> None:
        self._pitch = value
        self._apply()

    @property
    def roll(self) -> float:
        """Roll in degrees."""
        return self._roll

    @roll.setter
    def roll(self, value: float) -> None:
        self._roll = value
        self._apply()

    def set(self, pitch: float, roll: float) -> None:
        """Set both pitch and roll at once."""
        self._pitch = pitch
        self._roll = roll
        self._apply()
