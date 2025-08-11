from __future__ import annotations

from devices import Servo


class Claw:
    """Controls the claw, which is based off of two servo motors.
    
    Parameters
    ----------
    grip_servo: Servo
        The servo that drives two fingers, which "wrap" around the item being held.
    support_servo: Servo
        The servo that drives one single finger, which "supports" the item being held.
    """
    
    __slots__ = ('grip_servo', 'support_servo')
    
    def __init__(self, *, grip_servo: Servo, support_servo: Servo) -> None:
        self.grip_servo = grip_servo
        self.support_servo = support_servo
