from .claw import Claw
from .end_effector import Differential, EndEffector
from .gantry import Gantry

__all__ = ('System', 'Claw', 'Differential', 'EndEffector', 'Gantry')


class System:
    """Abstracts over all subsystems of the gantry system."""
    
    __slots__ = ('claw', 'end_effector', 'gantry', '_grab_position')
    
    def __init__(
        self,
        *,
        claw: Claw,
        end_effector: EndEffector,
        gantry: Gantry,
        grab_position: tuple[float, tuple] = (6.0, 0.5),
    ) -> None:
        self.claw = claw
        self.end_effector = end_effector
        self.gantry = gantry
        self._grab_position = grab_position

    def reset(self) -> None:
        """Reset all subsystems to their neutral positions."""
        self.claw.open()
        self.end_effector.reset()
        self.gantry.reset()

    def release(self) -> None:
        """Prepares the system for graceful shutdown."""
        self.gantry.stop()
        self.gantry.disable()

    def process_sort_request(self, position: tuple[float, float]) -> None:
        """Process a sort request by moving the gantry to the specified position."""
        self.claw.open()
        self.end_effector.reset()
        self.gantry.run_to_position(*self._grab_position)  # move to grab
        self.claw.close()
        self.gantry.run_to_position(*position)
