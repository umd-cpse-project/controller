from __future__ import annotations

from math import pi

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
    revolutions_per_inch: float
        The number of revolutions of the stepper motor needed to achieve one inch of movement in the end-effector.
    position: tuple[float, float]
        The initial position of the gantry in (x, y) coordinates when (a, b) = (0, 0).
        This is used to set the starting/reference point of the gantry.
        Typically, this is the number of inches from the origin (0, 0), the top-left corner ("peg") of the peg board.
        
        Defaults to ``(0.0, 0.0)``.
    """

    __slots__ = ('_left', '_right', '_zero_position', '_steps_per_inch')
    
    def __init__(
        self, 
        left: TMCStepper, 
        right: TMCStepper,
        *,
        revolutions_per_inch: float = 2.54 / 2.4 / pi,  # 1 / (24mm diameter pulley -> inches of circumference / revolution)
        position: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self._left = left
        self._right = right
        self._zero_position = self._cartesian_to_steps(*position)
        self._steps_per_inch = (
            revolutions_per_inch * left.steps_per_revolution,
            revolutions_per_inch * right.steps_per_revolution,
        )

    @property
    def left(self) -> TMCStepper:
        """The left stepper motor driver."""
        return self._left
    
    @property
    def right(self) -> TMCStepper:
        """The right stepper motor driver."""
        return self._right

    def enable(self) -> None:
        """Enable the gantry motors."""
        self._left.enable()
        self._right.enable()
        
    def disable(self) -> None:
        """Disable the gantry motors."""
        self._left.disable()
        self._right.disable()
    
    def stop(self) -> None:
        """Immediately stops the gantry motors."""
        self._left.stop()
        self._right.stop()

    def _cartesian_to_steps(self, x: float, y: float) -> tuple[int, int]:
        ox, oy = self._zero_position
        x, y = x - ox, y - oy
        l, r = self._steps_per_inch
        return round(l * (y - x)), round(r * (y + x))
    
    def _steps_to_cartesian(self, left: int, right: int) -> tuple[float, float]:
        ox, oy = self._zero_position
        l, r = self._steps_per_inch
        x, y = (right - left) / 2, (left + right) / 2
        return x / l + ox, y / r + oy
        
    def wait(self) -> None:
        """Wait for the gantry motors to finish moving to their targets."""
        self._left.wait()
        self._right.wait()
        
    def set_target(self, x: float, y: float) -> None:
        """Move the gantry to the specified (x, y) position, relative to the initially specified position.
        
        Parameters
        ----------
        x: float
            The target x-coordinate in inches.
        y: float
            The target y-coordinate in inches.
        """
        left, right = self._cartesian_to_steps(x, y)
        self._left.target = left
        self._right.target = right
        
    def run_to_position(self, x: float, y: float) -> None:
        """Move the gantry to the specified (x, y) position, blocking the main thread.
        
        Parameters
        ----------
        x: float
            The target x-coordinate in inches.
        y: float
            The target y-coordinate in inches.
        """
        left, right = self._cartesian_to_steps(x, y)
        self._left.run_to_position(left)
        self._right.run_to_position(right)

    def reset(self) -> None:
        """Reset the gantry to the initial position (0, 0)."""
        self.run_to_position(0.0, 0.0)
