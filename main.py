from __future__ import annotations

import datetime
import logging
import ssl
import time
from enum import Enum
from os import getenv
from threading import Thread
from typing import Any, NamedTuple, TYPE_CHECKING

import cv2
import msgpack
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from paho.mqtt.client import Client as MQTTClient, MQTTMessage

from config import get_manual_capture_button, get_lcd_display, get_system
from devices import Webcam

if TYPE_CHECKING:
    from typing import Self

load_dotenv()

MQTT_HOST = getenv('MQTT_HOST', 'localhost')
MQTT_PORT = int(getenv('MQTT_PORT', 1883))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Category(NamedTuple):
    id: int
    position: tuple[int, int]  # (x, y) coordinates
    name: str
    context: str = ''  # used to provide additional context
    size: tuple[int, int] = (1, 1)  # (width, height)
    hue: int = 0

    @property
    def x(self) -> int:
        return self.position[0]

    @property
    def y(self) -> int:
        return self.position[1]

    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def height(self) -> int:
        return self.size[1]
    
    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Self:
        return cls(
            id=raw['id'],
            position=(raw['x'], raw['y']),
            name=raw['name'],
            context=raw['context'],
            size=(raw['width'], raw['height']),
            hue=raw['hue'],
        )
    
    def __repr__(self) -> str:
        return f'<Category id={self.id} position={self.position} name={self.name!r}>'


class CategorizationResponse(NamedTuple):
    category: Category
    confidence: float
    
    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Self:
        return cls(
            category=Category.from_dict(raw['category']),
            confidence=raw['confidence'],
        )


class SystemState(Enum):
    idle = 0
    processing = 1
    sorting = 2

    def to_status_name(self) -> str:
        return {
            SystemState.idle: 'online',
            SystemState.processing: 'processing',
            SystemState.sorting: 'sorting',
        }[self]


class WebcamMQTTPublisher:
    """Main class for handling webcam image capture and MQTT communication."""
    
    def __init__(self, *, keepalive: float = 8.0) -> None:
        self.webcam: Webcam = Webcam()
        self.mqtt_client: MQTTClient = None
        self.is_running: bool = False
        self._keepalive: float = keepalive
        self._next_keepalive_due: datetime.datetime = datetime.datetime.now()

        self.state: SystemState = SystemState.idle
        self.last_sort_request: datetime.datetime | None = None
        self.last_sort_target: Category | None = None

        self.display = get_lcd_display()
        self.button = get_manual_capture_button()
        self.button.when_pressed = self.process_image  # Trigger image capture on button press
        self.system = get_system()

    def setup_mqtt(self) -> bool:
        """Initialize MQTT client"""
        try:
            self.mqtt_client = mqtt.Client(client_id='controller', userdata=None, protocol=mqtt.MQTTv5)
            self.mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
            self.mqtt_client.username_pw_set(getenv('MQTT_USERNAME'), getenv('MQTT_PASSWORD'))
            
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_publish = self.on_mqtt_publish

            # Connect to broker
            self.mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            self.mqtt_client.subscribe('/capture')
            self.mqtt_client.subscribe('/categorization')
            self.mqtt_client.subscribe('/error/categorization')
            self.mqtt_client.loop_start()

            logger.info(f"MQTT client setup complete. Connecting to {MQTT_HOST}:{MQTT_PORT}")
            return True
        except Exception as e:
            logger.error(f"Error setting up MQTT client: {e}")
            return False

    def on_mqtt_connect(self, _client, _userdata, _flags, rc, _properties=None):
        """Callback for when MQTT client connects"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def on_mqtt_disconnect(self, *_args):
        """Callback for when MQTT client disconnects"""
        logger.warning("Disconnected from MQTT broker")

    def on_mqtt_message(self, _client, _userdata, msg: MQTTMessage) -> None:
        """Callback for when a message is received"""
        if msg.topic.startswith('/error'):
            error = msgpack.loads(msg.payload)
            try:
                logger.warning(f'Error received in {error["context"]!r}: {error["error"]}')
            except KeyError:
                logger.warning(f'Error received in {msg.topic}: {error}')
            return
        
        elif msg.topic == '/capture':
            logger.info("Received manual capture request")
            self.process_image()
            return
        
        if not msg.topic.startswith('/categorization'):
            logger.debug(f"Received message on topic {msg.topic}, but not handling it")
            return
        
        response = CategorizationResponse.from_dict(msgpack.loads(msg.payload))
        logger.info(f"Received categorization response: {response!r}")
        Thread(target=self.process_sort_request, name='sort-worker', args=(response.category,)).start()

    def on_mqtt_publish(self, _client, _userdata, mid):
        """Callback for when message is published"""
        logger.debug(f"Message {mid} published successfully")

    def publish_image(self, image_data: bytes) -> bool:
        """Publish image to MQTT broker for processing"""
        try:
            result = self.mqtt_client.publish('/webcam', image_data)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.set_processing()
                logger.info(f"Image published successfully ({len(image_data)} bytes)")
                return True
            else:
                logger.error(f"Failed to publish image. Error code: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing image: {e}")
            return False

    def process_image(self) -> None:
        image_data = self.webcam.capture()
        if image_data:
            # Publish to MQTT
            self.publish_image(image_data)
        else:
            logger.warning("No image data captured, skipping publish")

    def process_sort_request(self, target: Category) -> None:
        self.set_sorting(target)
        self.display.clear()
        self.display.write_top('Category:')
        self.display.write_bottom(target.name, offset_left=16 - len(target.name))
        
        # convert from (0, 0) at top left to (0, 0) at bottom center:
        GANTRY_HEIGHT = 18  # inches
        pos = target.x, GANTRY_HEIGHT - target.y

        logger.info(f"Running gantry to position {pos}")
        self.system.process_sort_request(*pos)
        
        self.set_idle()
        self.system.gantry.set_target(0, 0)

    def set_idle(self) -> None:
        self.state = SystemState.idle
        logger.debug("System state set to idle")
        self.update_status()
        
    def set_processing(self) -> None:
        self.state = SystemState.processing
        self.last_sort_request = datetime.datetime.now()
        logger.debug("System state set to processing")
        self.update_status()
        
    def set_sorting(self, target: Category) -> None:
        self.state = SystemState.sorting
        self.last_sort_target = target
        logger.debug(f"System state set to sorting with target {target!r}")
        self.update_status()

    def _status_to_dict(self) -> dict[str, Any] | None:
        return {
            'status': self.state.to_status_name(),
            'last_sort': self.last_sort_request.isoformat() if self.last_sort_request else None,
            'target_id': (
                self.last_sort_target.id
                if self.last_sort_target and self.state is SystemState.sorting else None
            ),
        }
        
    def update_status(self) -> None:
        """Sends a status update through MQTT /status topic"""
        self._next_keepalive_due = datetime.datetime.now() + datetime.timedelta(seconds=self._keepalive)
        status = self._status_to_dict()
        if not status:
            logger.warning("Invalid status to update")
            return

        try:
            result = self.mqtt_client.publish('/status', msgpack.dumps(status))
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Status updated: {status} (mid: {result.mid})")
            else:
                logger.error(f"Failed to publish status. Error code: {result.rc}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")

    def run(self):
        """Main execution loop"""
        logger.info("Starting Webcam to MQTT Publisher")

        # Initialize camera and MQTT
        if not self.webcam.prepare():
            logger.error("Failed to setup camera. Exiting.")
            self.display.write('Failed camera setup, restart!')
            return

        if not self.setup_mqtt():
            logger.error("Failed to setup MQTT client. Exiting.")
            self.display.write('Failed conn to MQTT, restart!')
            return

        self.is_running = True
        self.display.write('Ready...')

        try:
            while self.is_running:
                delta = self._next_keepalive_due - datetime.datetime.now()
                remaining = delta.total_seconds()
                if remaining <= 0.0:
                    self.update_status()
                time.sleep(max(0.5, remaining))
        except KeyboardInterrupt:
            self.display.write('Shutting down...', 'Received SIGINT')
            logger.info("Received keyboard interrupt. Shutting down...")
        except Exception as e:
            self.display.write('Error! Stopping...', str(e))
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")

        self.is_running = False
        self.system.release()

        if self.webcam.is_alive():
            self.webcam.release()

        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")

        cv2.destroyAllWindows()


def main():
    """Main entry point"""
    publisher = WebcamMQTTPublisher()
    publisher.run()


if __name__ == "__main__":
    main()
