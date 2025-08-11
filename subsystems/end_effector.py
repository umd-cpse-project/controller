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
        '_left_servo', '_right_servo', '_neutral',
        '_last_pitch', '_last_roll',
    )

    def __init__(
        self, left_servo: Servo, right_servo: Servo,
    ) -> None:
        self._left_servo: Servo = left_servo
        self._right_servo: Servo = right_servo

        self._neutral = self._left_servo.angle, self._right_servo.angle
        self._last_pitch: float = 0.0
        self._last_roll: float = 0.0
        
    def set(self, *, pitch: float | None = None, roll: float | None = None) -> None:
        l, r = self._neutral
        pitch = pitch or self._last_pitch
        roll = roll or self._last_roll
        
        self._left_servo.angle = l + pitch - roll
        self._right_servo.angle = r + pitch - roll
        self._last_pitch = pitch
        self._last_roll = roll
        
    def reset(self) -> None:
        """Reset the end effector to its neutral position."""
        self._left_servo.angle, self._right_servo.angle = self._neutral
        self._last_pitch = 0.0
        self._last_roll = 0.0

    @property
    def pitch(self) -> float:
        """The current pitch of the end effector."""
        return self._last_pitch
    
    @pitch.setter
    def pitch(self, value: float) -> None:
        """Set the pitch of the end effector."""
        self.set(pitch=value)
    
    @property
    def roll(self) -> float:
        """The current roll of the end effector."""
        return self._last_roll

    @roll.setter
    def roll(self, value: float) -> None:
        """Set the roll of the end effector."""
        self.set(roll=value)


if __name__ == '__main__':
    left = Servo(0, angle=135.0)
    right = Servo(1, reverse=True, angle=135.0)
    end_effector = EndEffector(left, right)
    end_effector.set(pitch=10.0)
