# controller
Controller implementation for the Raspberry Pi.

## Prerequisites

- Python 3.11+
- `pigpio` (i.e., run `sudo pigpiod`).
- enable the I2C interface on the Raspberry Pi.
- enable the serial interface on the Raspberry Pi.
  - `sudo raspi-config` -> `Interface Options` -> `Serial Port` -> `No` for login shell, `Yes` for serial port hardware.

## Configuration

Ensure the following environment variables are set:

- `MQTT_HOST` (default: `localhost`)
- `MQTT_PORT` (default: `1883`)
- `MQTT_USERNAME` (default: no username/password)
- `MQTT_PASSWORD` (default: no username/password)
- `AUTHORIZATION_TOKEN`
- `GPIOZERO_PIN_FACTORY`
- `UART_PORT` (default: `/dev/serial0`)
  - if using RPi 5, set this to `/dev/ttyAMA0` instead

Then go to `config.py` and configure settings such as pin numberings, I2C addresses, etc.
