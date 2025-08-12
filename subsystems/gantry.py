from __future__ import annotations

from devices import TMCStepper

__all__ = ('Gantry',)


class Gantry:
    """Controls the Core-XY based gantry system, moving the end effector in 2D space.
    
    Parameters
    ----------
    left: TMCStepper
        The left stepper motor driver ("motor A")
    right: TMCStepper
        The right stepper motor driver ("motor B")
    position: tuple[float, float]
        The initial position of the gantry in (x, y) coordinates when (a, b) = (0, 0).
        This is used to set the starting/reference point of the gantry.
        Typically, this is the number of inches from the origin (0, 0), the top-left corner ("peg") of the peg board.
        
        Defaults to ``(0.0, 0.0)``.
    """

    __slots__ = ('_left', '_right')
    
    def __init__(
        self, 
        left: TMCStepper, 
        right: TMCStepper,
    ) -> None:
        self._left = left
        self._right = right

    def enable(self) -> None:
        """Enable the gantry motors."""
        self._left.enable()
        self._right.enable()
        
    def disable(self) -> None:
        """Disable the gantry motors."""
        self._left.disable()
        self._right.disable()
        
    def move_to_position(self, x: float, y: float) -> None:
        """Move the gantry to the specified (x, y) position, relative to the initially specified position.
        
        Parameters
        ----------
        x: float
            The target x-coordinate in inches.
        y: float
            The target y-coordinate in inches.
        """
        pass
