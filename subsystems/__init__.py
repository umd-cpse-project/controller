from .claw import Claw
from .end_effector import Differential, EndEffector
from .gantry import Gantry

__all__ = ('System', 'Claw', 'Differential', 'EndEffector', 'Gantry')


class System:
    """Abstracts over all subsystems of the gantry system."""
    
    def __init__(self, *, claw: Claw, end_effector: EndEffector, gantry: Gantry) -> None:
        self.claw = claw
        self.end_effector = end_effector
        self.gantry = gantry

    def reset(self) -> None:
        """Reset all subsystems to their neutral positions."""
        self.claw.open()
        self.end_effector.reset()

    def release(self) -> None:
        """Prepares the system for graceful shutdown."""
        self.gantry.disable()
