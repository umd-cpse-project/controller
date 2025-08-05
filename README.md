# controller
Controller implementation for the Raspberry Pi.

## Prerequisites

- Python 3.11+
- `pigpio` (i.e., run `sudo pigpiod`).

## Configuration

Ensure the following environment variables are set:

- `MQTT_HOST` (default: `localhost`)
- `MQTT_PORT` (default: `1883`)
- `MQTT_USERNAME` (default: no username/password)
- `MQTT_PASSWORD` (default: no username/password)
- `AUTHORIZATION_TOKEN`
- `GPIOZERO_PIN_FACTORY`
- `MANUAL_CAPTURE_BUTTON_PIN` (default: `17`)
