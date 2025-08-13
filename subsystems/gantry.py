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
    
    def stop(self) -> None:
        """Immediately stops the gantry motors."""
        self._left.stop()
        self._right.stop()

    def _cartesian_to_steps(self, x: float, y: float) -> tuple[int, int]:
        return y - x, y + x
    
    def _steps_to_cartesian(self, left: int, right: int) -> tuple[float, float]:
        return (right - left) / 2, (left + right) / 2
        
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
