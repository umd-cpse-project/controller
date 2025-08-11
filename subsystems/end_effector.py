from __future__ import annotations

from devices import Servo


class EndEffector:
    """Abstraction over a differential-driven 2DOF end effector (pitch and roll).
    
    Parameters
    ----------
    front_servo: Servo
        The driver for the front-facing servo, in the perspective of the board (the servo facing you).
    back_servo: Servo
        The driver for the back-facing servo, in the perspective of the board (the servo further away from you).
    """

    __slots__ = (
        "_front_servo", "_back_servo",
        "_pitch", "_roll",
        "neutral_a", "neutral_b",
        "invert_pitch", "invert_roll",
        "max_pitch", "max_roll"
    )

    def __init__(
        self,
        front_servo: Servo,
        back_servo: Servo,
        *,
        neutral_a: float = 135.0,
        neutral_b: float = 135.0,
        invert_pitch: bool = False,
        invert_roll: bool = False,
    ) -> None:
        self._front_servo: Servo = front_servo
        self._back_servo: Servo = back_servo
        self.neutral_a = neutral_a
        self.neutral_b = neutral_b
        self.invert_pitch = invert_pitch
        self.invert_roll = invert_roll
        self._pitch = 0.0
        self._roll = 0.0
        self._apply()

    def _clamp_servo(self, angle: float) -> float:
        """Clamp a servo angle to physical limits."""
        return max(0, min(self._front_servo.inner.actuation_range, angle))

    def _clamp_motion(self, pitch: float, roll: float) -> tuple[float, float]:
        """Clamp pitch and roll to mechanical limits."""
        pitch = max(-self.max_pitch, min(self.max_pitch, pitch))
        roll = max(-self.max_roll, min(self.max_roll, roll))
        return pitch, roll

    def _apply(self) -> None:
        """Send the current pitch/roll values to the servos."""
        # Clamp motion to safe mechanical range
        pitch, roll = self._clamp_motion(self._pitch, self._roll)

        # Apply inversion if needed
        pitch = -pitch if self.invert_pitch else pitch
        roll = -roll if self.invert_roll else roll

        # Map to servo angles
        angle_a = self._clamp_servo(self.neutral_a + pitch + roll)
        angle_b = self._clamp_servo(self.neutral_b + pitch - roll)

        self._front_servo.angle = angle_a
        self._back_servo.angle = angle_b

    @property
    def pitch(self) -> float:
        """Pitch in degrees."""
        return self._pitch

    @pitch.setter
    def pitch(self, value: float) -> None:
        self._pitch = value
        self._apply()

    @property
    def roll(self) -> float:
        """Roll in degrees."""
        return self._roll

    @roll.setter
    def roll(self, value: float) -> None:
        self._roll = value
        self._apply()

    def set(self, pitch: float, roll: float) -> None:
        """Set both pitch and roll at once."""
        self._pitch = pitch
        self._roll = roll
        self._apply()
