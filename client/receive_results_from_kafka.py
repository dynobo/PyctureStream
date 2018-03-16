"""Really simple Kafka consumer, that log messages and store jpg."""

from kafka import KafkaConsumer
import json
import logging
import base64
import io
from PIL import Image
logging.basicConfig(format='%(levelname)s - %(asctime)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# Set the camera id of the client here!
# Has to be the same as in "stream_webcam_to_kafka.py"
CAMERA_ID = 'holger'

# ==========================================


# Open Kafka Consumer & listen to topic
consumer = KafkaConsumer('resultstream',
                         bootstrap_servers=['127.0.0.1:9092'])

# Process Messages
for message in consumer:
    # e.g., for unicode: `message.value.decode('utf-8')`
    # print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
    #                                       message.offset, message.key,
    #                                       message.value))
    results = json.loads(message.value)
    try:
        # Filter out all messages not from this consumer
        # (Of course this solution is for PoC only!)
        if results['camera_id'] != CAMERA_ID:
            continue

        # Log info
        logger.info('-'*20 + ' NEW MESSAGE ' + '-'*20)
        logger.info('Device ID:')
        logger.info(f"--- {results['camera_id']}")
        logger.info('Image taken at:')
        logger.info(f"--- {results['timestamp']}")
        logger.info(f"{len(results['objects'])} Objects detected:")
        for obj in results['objects']:
            logger.info(f"--- {obj['label']} ({obj['score']}) at {obj['sector']}")

        # Store image
        decoded = base64.b64decode(results['image'])
        stream = io.BytesIO(decoded)
        img = Image.open(stream)
        img.save('./output.jpg', 'JPEG')

    except Exception as e:
        logger.error(e)

# consume earliest available messages, don't commit offsets
KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)

# consume json messages
KafkaConsumer(value_deserializer=lambda m: json.loads(m.decode('ascii')))
