from __future__ import annotations

import logging
from threading import Thread

import cv2

logger = logging.getLogger(__name__)


class WebcamKeepAlive(Thread):
    def __init__(self, camera: cv2.VideoCapture, *, thread_name='webcam-thread') -> None:
        self._camera: cv2.VideoCapture = camera
        self._last_frame = None
        self._run: bool = True
        super(WebcamKeepAlive, self).__init__(name=thread_name)
        self.start()

    def run(self):
        while self._run:
            ret, self._last_frame = self._camera.read()

    def read(self) -> tuple[bool, cv2.Mat]:
        if self._last_frame is None:
            return self._camera.read()
        return True, self._last_frame

    def release(self) -> None:
        """Release the camera resources"""
        self._run = False
        if not self._camera:
            logger.warning("No webcam to release")

        self._camera.release()
        self._camera = None
        logger.info("Webcam released")


class Webcam:
    """Handles webcam operations for capturing images.

    Parameters
    ----------
    webcam_index: int
        The index of the webcam to use (default is 0).
    image_quality: int
        The JPEG quality of the captured image (1-100, default is 85).
    resize_width: int | None
        The width to resize the captured image to (None to keep original, default is 360).
        Must be specified with `resize_height` to be taken into account.
    resize_height: int | None
        The height to resize the captured image to (None to keep original, default is 270).
        Must be specified with `resize_width` to be taken into account.
    fps: int
        The frames per second for webcam stream (default is 5).
        This is the rate at which the webcam streams in frames, but not necessarily the rate at which images are
        captured then processed.
    """
    
    _capture: cv2.VideoCapture

    def __init__(
        self,
        webcam_index: int = 0,
        *,
        image_quality: int = 85,
        resize_width: int | None = 360,
        resize_height: int | None = 270,
        fps: int = 5,
    ) -> None:
        self.webcam_index: int = webcam_index
        self.image_quality: int = image_quality
        self.resize_width: int | None = resize_width
        self.resize_height: int | None = resize_height
        self.fps: int = fps
        
        self._keepalive: WebcamKeepAlive | None = None
        self._capture: cv2.VideoCapture | None = None

    def prepare(self) -> bool:
        """Initialize the webcam"""
        try:
            camera = cv2.VideoCapture(self.webcam_index)
            if not camera.isOpened():
                logger.error(f"Failed to open camera at index {self.webcam_index}")
                return False
    
            # Set camera properties for better performance
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resize_width)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resize_height)
            camera.set(cv2.CAP_PROP_FPS, self.fps)
            self._keepalive = WebcamKeepAlive(camera)
            self._capture = camera
    
            logger.info("Camera initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up camera: {e}")
            return False

    def capture(self) -> bytes | None:
        """Capture an image from the webcam"""
        if self._keepalive is None or not self._keepalive.is_alive():
            logger.error("Webcam is not initialized or has been released")
            return None
        
        try:
            ret, frame = self._keepalive.read()
            if not ret:
                logger.error("Failed to capture image from camera")
                return None

            height, width, _ = frame.shape
            # Resize image if specified
            if (
                self.resize_width and self.resize_height
                and self.resize_width != width and self.resize_height != height
            ):
                frame = cv2.resize(frame, (self.resize_width, self.resize_height))

            # Encode image as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.image_quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_params)

            return buffer.tobytes()

        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return None

    def release(self) -> None:
        """Release the webcam resources"""
        if self._keepalive:
            self._keepalive.release()
            self._keepalive = None
            self._capture = None
        else:
            logger.warning("No webcam to release")
            
    def is_alive(self) -> bool:
        """Check if the webcam keepalive thread is running"""
        return self._keepalive is not None and self._keepalive.is_alive()
