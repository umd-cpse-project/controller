"""System configuration"""

from os import getenv

from devices import *
from subsystems import *

MANUAL_CAPTURE_BUTTON = Button(17)
LCD_DISPLAY = LCDDisplay(addr=0x27, backlight_enabled=True)
UART = getenv('TMC_UART', '/dev/serial0')

SYSTEM = System(
    claw=Claw(
        grip_servo=Servo(4),
        support_servo=Servo(3),
        grip_open=165.0, grip_closed=210.0,
        support_open=100.0, support_closed=190.0,
    ),
    end_effector=EndEffector(
        differential=Differential(
            left_servo=Servo(0, angle=135.0),
            right_servo=Servo(1, reverse=True, angle=135.0),
        ),
        yaw_servo=Servo(2, angle=135.0)  # Yaw servo
    ),
    gantry=Gantry(
        left=TMCStepper(
            control_pin=21, step_pin=16, dir_pin=20, 
            uart=UART,
            current=1600,  # in mA
        ),
        right=TMCStepper(
            control_pin=5, step_pin=6, dir_pin=13,
            uart=UART,
            current=1400,
        ),
    ),
)
