from __future__ import annotations

from devices import Servo


def interpolate(t: float, lo: int, hi: int) -> float:
    return lo + (hi - lo) * t


class Claw:
    """Controls the claw, which is based off of two servo motors.
    
    Parameters
    ----------
    grip_servo: Servo
        The servo that drives two fingers, which "wrap" around the item being held.
    support_servo: Servo
        The servo that drives one single finger, which "supports" the item being held.
    """
    
    __slots__ = ('_grip_servo', '_grip_range', '_support_range', '_support_servo')
    
    def __init__(
        self,
        *,
        grip_servo: Servo,
        support_servo: Servo,
        grip_open: float = 165.0,
        grip_closed: float = 210.0,
        support_open: float = 100.0,
        support_closed: float = 190.0,
    ) -> None:
        self._grip_servo = grip_servo
        self._grip_range = (grip_open, grip_closed)
        
        self._support_servo = support_servo
        self._support_range = (support_open, support_closed)

    def _set_grip(self, t: float) -> None:
        """Set the grip servo to a position based on a normalized value `t` (0.0 to 1.0)."""
        angle = interpolate(t, *self._grip_range)
        self._grip_servo.angle = angle
        
    def _set_support(self, t: float) -> None:
        """Set the support servo to a position based on a normalized value `t` (0.0 to 1.0)."""
        angle = interpolate(t, *self._support_range)
        self._support_servo.angle = angle

    def set(self, *, grip: float | None = None, support: float | None = None) -> None:
        """Set the grip servo to a position based on a normalized value `t` (0.0 to 1.0)."""
        if grip is not None:
            self._set_grip(grip)
        if support is not None:
            self._set_support(support)

    def open(self) -> None:
        """Sets the claw to the completely open position."""
        self.set(grip=1.0, support=1.0)
        
    def close(self) -> None:
        """Sets the claw to the completely closed position."""
        self.set(grip=0.0, support=0.0)


if __name__ == '__main__':
    grip = Servo(4)
    support = Servo(3)
    
    claw = Claw(grip_servo=grip, support_servo=support)
    claw.open()
