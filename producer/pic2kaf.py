#from __future__ import print_function
from kafka import KafkaProducer
import cv2
import json
import time
import datetime as dt
import logging
logging.basicConfig(format='%(levelname)s - %(asctime)s: %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class webcam_producer():
    """Stream WebCam Images to Kafka Endpoint."""

    def __init__(self, source: int, interval: int = 5, server: str = '127.0.0.1:9092', *args, **kwargs):

        self.video_source = source if source else 'demo.mp4' # Index of Webcam or Demo Video
        self.interval = interval  # Interval for Photos in Seconds
        self.server = server  # Host + Port of Kafka Endpoint

        # TODO: Images are somehow queued up by cv2!
        self.vidcap = cv2.VideoCapture(0)
        logger.info('Initialized.')
        self.start_stream()

    def take_picture(self):

        success, image = self.vidcap.read()
        if success is True:
            return image
        else:
            logger.warn('Video capturing unsuccessful.')
            return False

    def start_stream(self):
        logger.info('Starting Streaming.')
        while True:
            pic = self.take_picture()
            timestamp = dt.datetime.utcnow().isoformat()
            if pic is not False:
                cv2.imwrite('frame.jpg', pic) # Save frame as JPEG file, for debug
                logger.info(f'Toke Picture at {timestamp}.')
            time.sleep(self.interval)

    def send_to_kafka(self):
        producer = KafkaProducer(bootstrap_servers=self.server,
                            value_serializer=lambda m: json.dumps(m).encode('utf8'))
        for _ in range(25):
            print('Sending...')
            producer.send('wordcounttopic', {'foo':'b♥ar'})

if __name__ == '__main__':
    webcam_producer(interval=5, source=1, server='127.0.0.1:9092')
