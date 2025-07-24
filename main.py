from __future__ import annotations

from threading import Thread

import msgpack
import time
import logging
import ssl
from os import getenv
from typing import Any, NamedTuple, TYPE_CHECKING

import cv2
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from gpiozero import Button, Device
from gpiozero.pins.rpigpio import RPiGPIOFactory
from paho.mqtt.client import Client as MQTTClient, MQTTMessage

from lcd_display import LCDDisplay

if TYPE_CHECKING:
    from typing import Self

load_dotenv()

MQTT_HOST = getenv('MQTT_HOST', 'localhost')
MQTT_PORT = int(getenv('MQTT_PORT', 1883))

WEBCAM_INDEX = 0  # Usually 0 for the first camera
CAPTURE_INTERVAL = 5  # Seconds between captures
IMAGE_QUALITY = 85  # JPEG quality (1-100)
RESIZE_WIDTH = 360  # Resize image width (None to keep original)
RESIZE_HEIGHT = 270  # Resize image height (None to keep original)
CAP_WEBCAM_FPS = 5  # Frames per second for webcam capture
CAP_BUFFER_SIZE = 10  # Buffer size for webcam capture

Device.pin_factory = RPiGPIOFactory()

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


class Webcam(Thread):
    def __init__(self, camera, *, thread_name='webcam-thread'):
        self._camera = camera
        self._last_frame = None
        super(Webcam, self).__init__(name=thread_name)
        self.start()

    def run(self):
        while True:
            ret, self._last_frame = self._camera.read()
            time.sleep(1 / CAP_WEBCAM_FPS)
            
    def read(self) -> tuple[bool, cv2.Mat]:
        if self._last_frame is None:
            return self._camera.read()
        return True, self._last_frame
    
    def release(self) -> None:
        """Release the camera resources"""
        if self._camera:
            self._camera.release()
            logger.info("Webcam released")
        else:
            logger.warning("No webcam to release")


class WebcamMQTTPublisher:
    def __init__(self) -> None:
        self.webcam: Webcam = None
        self.mqtt_client: MQTTClient = None
        self.is_running: bool = False

        self.display = LCDDisplay(addr=0x27, backlight_enabled=True)
        self.button = Button(17)
        self.button.when_pressed = self.process_image  # Trigger image capture on button press

    def setup_camera(self) -> bool:
        """Initialize the webcam"""
        try:
            camera = cv2.VideoCapture(WEBCAM_INDEX)
            if not camera.isOpened():
                logger.error(f"Failed to open camera at index {WEBCAM_INDEX}")
                return False

            # Set camera properties for better performance
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, RESIZE_WIDTH)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, RESIZE_WIDTH)
            camera.set(cv2.CAP_PROP_FPS, CAP_WEBCAM_FPS)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, CAP_BUFFER_SIZE)
            self.webcam = Webcam(camera)

            logger.info("Camera initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up camera: {e}")
            return False

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
        
        if not msg.topic.startswith('/categorization'):
            logger.debug(f"Received message on topic {msg.topic}, but not handling it")
            return
        
        response = CategorizationResponse.from_dict(msgpack.loads(msg.payload))
        logger.info(f"Received categorization response: {response!r}")
        
        self.display.clear()
        self.display.write_top('Category:')
        self.display.write_bottom(response.category.name, offset_left=16 - len(response.category.name))

    def on_mqtt_publish(self, _client, _userdata, mid):
        """Callback for when message is published"""
        logger.debug(f"Message {mid} published successfully")

    def capture_image(self) -> bytes | None:
        """Capture an image from the webcam"""
        try:
            ret, frame = self.webcam.read()
            if not ret:
                logger.error("Failed to capture image from camera")
                return None

            height, width, _ = frame.shape
            # Resize image if specified
            if RESIZE_WIDTH and RESIZE_HEIGHT and RESIZE_WIDTH != width and RESIZE_HEIGHT != height:
                frame = cv2.resize(frame, (RESIZE_WIDTH, RESIZE_HEIGHT))

            # Encode image as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, IMAGE_QUALITY]
            _, buffer = cv2.imencode('.jpg', frame, encode_params)

            return buffer.tobytes()

        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return None

    def publish_image(self, image_data: bytes) -> bool:
        """Publish image to MQTT broker"""
        try:
            result = self.mqtt_client.publish('/webcam', image_data, qos=1)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Image published successfully ({len(image_data)} bytes)")
                return True
            else:
                logger.error(f"Failed to publish image. Error code: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing image: {e}")
            return False

    def process_image(self) -> None:
        image_data = self.capture_image()
        if image_data:
            # Publish to MQTT
            self.publish_image(image_data)
            self.display.write('Processing image...')
        else:
            logger.warning("No image data captured, skipping publish")

    def run(self):
        """Main execution loop"""
        logger.info("Starting Webcam to MQTT Publisher")

        # Initialize camera and MQTT
        if not self.setup_camera():
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
                # # Capture image
                # image_data = self.capture_image()
                # if image_data:
                #     # Publish to MQTT
                #     self.publish_image(image_data)
                #     self.display.write('Processing image...')
                # else:
                #     logger.warning("No image data captured, skipping publish")
                # 
                # # Wait for next capture
                # time.sleep(CAPTURE_INTERVAL)
                pass
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

        if self.webcam:
            self.webcam.release()
            logger.info("Camera released")

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
