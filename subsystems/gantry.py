from __future__ import annotations

from devices import Nema17Stepper, StepperDirection

__all__ = ('Gantry',)


class Gantry:
    """Controls the Core-XY based gantry system, moving the end effector in 2D space.
    
    Parameters
    ----------
    left: Nema17Stepper
        The left stepper motor driver ("motor A")
    right: Nema17Stepper
        The right stepper motor driver ("motor B")
    position: tuple[float, float]
        The initial position of the gantry in (x, y) coordinates when (a, b) = (0, 0).
        This is used to set the starting/reference point of the gantry.
        Typically, this is the number of inches from the origin (0, 0), the top-left corner ("peg") of the peg board.
        
        Defaults to ``(0.0, 0.0)``.
    """

    __slots__ = ('_left_motor', '_right_motor')
    
    def __init__(
        self, 
        left: Nema17Stepper, 
        right: Nema17Stepper, 
        *, 
        position: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self._left_motor = left
        self._right_motor = right
