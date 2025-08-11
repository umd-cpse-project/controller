from __future__ import annotations

from devices import Servo


class Differential:
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
        pitch = pitch if pitch is not None else self._last_pitch
        roll = roll if pitch is not None else self._last_roll
        
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


class EndEffector:
    """Abstraction over a 3DOF end effector (pitch, roll, and yaw), where pitch and roll are controlled by a 
    differential motor pair, and yaw is controlled by a single servo.
    
    Parameters
    ----------
    differential: Differential
        The differential motor pair that controls the pitch and roll of the end effector.
    yaw_servo: Servo
        The servo that controls the yaw of the end effector.
    """
    
    __slots__ = ('_differential', '_yaw', '_yaw_neutral')

    def __init__(self, differential: Differential, yaw_servo: Servo) -> None:
        self._differential: Differential = differential
        self._yaw: Servo = yaw_servo
        self._yaw_neutral: float = yaw_servo.angle

    def set(self, *, pitch: float | None = None, roll: float | None = None, yaw: float | None = None) -> None:
        """Set the pitch, roll, and yaw of the end effector."""
        if pitch is not None or roll is not None:
            self._differential.set(pitch=pitch, roll=roll)
        if yaw is not None:
            self._yaw.angle = self._yaw_neutral + yaw
            
    def reset(self) -> None:
        """Reset the end effector to its neutral position."""
        self._differential.reset()
        self._yaw.angle = self._yaw_neutral
        
    @property
    def pitch(self) -> float:
        """The current pitch of the end effector."""
        return self._differential.pitch
    
    @pitch.setter
    def pitch(self, value: float) -> None:
        """Set the pitch of the end effector."""
        self._differential.pitch = value
        
    @property
    def roll(self) -> float:
        """The current roll of the end effector."""
        return self._differential.roll
    
    @roll.setter
    def roll(self, value: float) -> None:
        """Set the roll of the end effector."""
        self._differential.roll = value
        
    @property
    def yaw(self) -> float:
        """The current yaw of the end effector."""
        return self._yaw.angle - self._yaw_neutral
    
    @yaw.setter
    def yaw(self, value: float) -> None:
        """Set the yaw of the end effector."""
        self._yaw.angle = self._yaw_neutral + value


if __name__ == '__main__':
    left = Servo(0, angle=135.0)
    right = Servo(1, reverse=True, angle=135.0)
    end_effector = EndEffector(left, right)
    end_effector.set(pitch=10.0)
