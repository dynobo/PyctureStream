"""Kafka-Producer that's sending video frames from a device
or a Video File to an Kafka Endpoint."""

from kafka import KafkaProducer
import cv2
import base64
import json
import time
import datetime as dt
import logging
logging.basicConfig(format='%(levelname)s - %(asctime)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class webcam_producer():
    """Stream WebCam Images to Kafka Endpoint.

    Keyword arguments:
    source -- Index of Video Device or Filename of Video-File
    interval -- Interval for capturing images in seconds (default 5)
    server -- Host + Port of Kafka Endpoint (default '127.0.0.1:9092')
    """

    def __init__(self,
                 interval: int = 5,
                 source=0,
                 camera_id: str = 'camera_generic',
                 topic: str = 'wordcounttopic',
                 server: str = '127.0.0.1:9092'):

        logger.info(f'Initialized camera "{camera_id}" with source {source}.')
        logger.info(f'Send to "{topic}" on "{server}" every {interval} sec.')

        # Class Variables
        self.interval = interval  # Interval for Photos in Seconds
        self.video_source = source
        self.camera_id = camera_id
        self.server = server  # Host + Port of Kafka Endpoint
        self.topic = topic
        self.img_file = './frame.jpg'

        # Connection to Kafka Enpoint
        self.producer = KafkaProducer(bootstrap_servers=self.server,
                                      value_serializer=lambda m: json.dumps(m).encode('utf8'))
        self.producer.send(self.topic, b'data')

        # Start Streaming...
        self.stream_video()

    def stream_video(self):
        """Start streaming video frames to Kafka forever."""
        logger.info(f'Start capturing frames every {self.interval} sec.')
        while True:
            vidcap = cv2.VideoCapture(self.video_source)
            success, image = vidcap.read()
            timestamp = dt.datetime.utcnow().isoformat()
            vidcap.release()
            if success is True:
                # Base64 encode image for transfer in json
                png = cv2.imencode('.png', image)[1]
                png_as_text = base64.b64encode(png).decode('utf-8')
                # Build object and send to Kafka
                result = {
                    'image': png_as_text,
                    'timestamp': timestamp,
                    'camera_id': self.camera_id
                }
                self.send_to_kafka(result)
                self.save_image(image)
            else:
                logger.error(f'Could not read image from source {self.video_source}!')
            # Sleep interval, before next capture
            time.sleep(self.interval)

    def send_to_kafka(self, data):
        """Send JSON payload to topic in Kafka."""
        self.producer.send(self.topic, data)
        logger.info('Sent image to Kafka endpoint.')

    def save_image(self, image):
        """Save frame as JPEG file, for debugging purpose only."""
        cv2.imwrite(self.img_file, image)
        logger.info(f'Saved image file to {self.img_file}.')

if __name__ == '__main__':
    # Set source='demo.mp4' for streaming video file
    webcam_producer(interval=5,
                    source=0,
                    camera_id='holger',
                    server='127.0.0.1:9092',
                    topic='wordcounttopic')
