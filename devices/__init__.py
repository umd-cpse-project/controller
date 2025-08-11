from typing import TYPE_CHECKING

from .stepper import Direction as StepperDirection
from .webcam import Webcam

try:
    import RPi.GPIO
    IS_RPI = True
except ImportError:
    print('Note: running in non-RPi environment!')
    IS_RPI = False

if TYPE_CHECKING or IS_RPI:
    from gpiozero import Button, Device
    from gpiozero.pins.rpigpio import RPiGPIOFactory

    from .lcd_display import LCDDisplay
    from .servo import Servo
    from .stepper import Stepper, Nema17Stepper
else:
    exec('from .mock_gpio import *')

Device.pin_factory = RPiGPIOFactory()

__all__ = (
    'IS_RPI',
    'Button',
    'LCDDisplay',
    'Webcam',
    'Servo',
    'Stepper',
    'Nema17Stepper',
    'StepperDirection',
)
