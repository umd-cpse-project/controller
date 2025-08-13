"""Interface for TMC stepper motor drivers."""

from __future__ import annotations

from tmc_driver.tmc_2209 import *

__all__ = ('TMCStepper',)


class TMCStepper:
    """Interface for a TMC stepper motor.

    Parameters
    ----------
    control_pin: int
        The GPIO pin used to control the stepper motor.
    step_pin: int
        The GPIO pin used to send step signals to the stepper motor.
    dir_pin: int
        The GPIO pin used to set the direction of the stepper motor.
    uart: str
        The UART device to use for communication with the TMC driver.
        Defaults to '/dev/serial0'.
    reverse: bool
        Whether to reverse the direction of the stepper motor.
        Defaults to False (positive is CCW).
    current: int
        The current in mA to draw from the TMC.
        Defaults to 1500 mA.
    steps_per_revolution: int
        The number of full steps per revolution for the stepper motor.
        Defaults to 200 steps (1.8 degrees per step).
    """
    
    __slots__ = ('_tmc', 'pulley_circumference')

    def __init__(
        self,
        control_pin: int,
        step_pin: int,
        dir_pin: int,
        *,
        uart: str = '/dev/serial0',
        reverse: bool = False,
        current: int = 1500,
        steps_per_revolution: int = 200,
    ) -> None:
        self._tmc: Tmc2209 = Tmc2209(
            TmcEnableControlPin(control_pin),
            TmcMotionControlStepDir(step_pin, dir_pin),
            TmcComUart(uart),
        )
        self._tmc.set_direction_reg(reverse)
        self._tmc.set_current(current)
        self._tmc.set_interpolation(True)
        self._tmc.set_spreadcycle(False)
        self._tmc.set_microstepping_resolution(1)
        self._tmc.set_internal_rsense(False)
        self._tmc.acceleration_fullstep = 1000
        self._tmc.max_speed_fullstep = 100
        self._tmc.fullsteps_per_rev = steps_per_revolution
        self.enable()

    def enable(self) -> None:
        """Enables the stepper motor."""
        self._tmc.set_motor_enabled(True)

    def disable(self) -> None:
        """Disables the stepper motor."""
        self._tmc.set_motor_enabled(False)

    def run_to_position(self, position: int) -> None:
        """Moves the stepper motor to an absolute position in steps, blocking the main thread."""
        self._tmc.run_to_position_steps(position)

    def wait(self) -> None:
        """Waits for the stepper motor to finish its current operation."""
        self._motion_control.wait_for_movement_finished_threaded()

    @property
    def _motion_control(self) -> TmcMotionControlStepDir:
        return self._tmc.tmc_mc

    @property
    def position(self) -> int:
        """Gets the current position of the stepper motor in steps."""
        return self._motion_control.current_pos

    @property
    def target(self) -> int:
        """Gets the target position of the stepper motor in steps."""
        return self._motion_control._target_pos

    @target.setter
    def target(self, position: int) -> None:
        """Sets the target position for the stepper motor such that it runs async."""
        self._motion_control.run_to_position_steps_threaded(position, MovementAbsRel.ABSOLUTE)

    @property
    def speed(self) -> int:
        """Returns the speed of the stepper motor, in fullsteps/sec."""
        return self._motion_control.speed_fullstep
    
    @property
    def target_speed(self) -> int:
        """Returns the target speed of the stepper motor, in fullsteps/sec."""
        return self._motion_control.max_speed_fullstep
    
    @target_speed.setter
    def target_speed(self, speed: int) -> None:
        """Sets the target speed of the stepper motor, in fullsteps/sec."""
        self._motion_control.max_speed_fullstep = speed

    @property
    def steps_per_revolution(self) -> int:
        """Returns the number of full steps per revolution."""
        return self._motion_control.fullsteps_per_rev
    
    def stop(self) -> None:
        """Stops motion control of the stepper motor."""
        self._motion_control.stop()

    def __enter__(self) -> TMCStepper:
        self.enable()
        return self

    def __exit__(self, *_) -> None:
        self.disable()
