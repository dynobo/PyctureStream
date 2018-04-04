"""Really simple Kafka consumer, that log messages and store jpg."""

# NOTE: Text-To-Speech preconditions depend on your OS!!!
# Pls read docs: https://pyttsx3.readthedocs.io/en/latest/

from kafka import KafkaConsumer
import json
import logging
import base64
import io
import pyttsx3
from PIL import Image
logging.basicConfig(format='%(levelname)s - %(asctime)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# Set the camera id of the client here!
# Has to be the same as in "stream_webcam_to_kafka.py"
CAMERA_ID = 'holger_cam'
SPEAK = True
SPEECH_SPEED = 170

# ==========================================
def generate_sentences(objects):
    """Generate simple sentences out of detected objects. Also aggregate
     multiple same objects in same sector into singe sentence with plural."""
    # Generate sentences and count occurence of same sentences
    sentences = {}
    for obj in objects:
        sentence = f"{obj['label']} at {obj['sector'][0]} {obj['sector'][1]}."
        sentences[sentence] = sentences.get(sentence, 0) + 1

    # Aggregate same sentences by transforming into simple plural.
    result = []
    for s, count in sentences.items():
        if count > 1:
            # Add plural 's and count
            combined = str(count) + ' ' + \
                       s.split(' at ')[0] + 's' + ' at ' + s.split(' at ')[1]
            result.append(combined)
        else:
            result.append(s)
    return result


def speak(objects):
    engine = pyttsx3.init()
    engine.setProperty('rate', SPEECH_SPEED)
    if len(objects) < 1:
        engine.say('No objects detected.')
    else:
        sentences = generate_sentences(objects)
        for s in sentences:
            logger.info(f'[SPEAK] {s}')
            engine.say(s)
    engine.runAndWait()


# Open Kafka Consumer & listen to topic
consumer = KafkaConsumer('resultstream',
                         bootstrap_servers=['127.0.0.1:9092'])


# Process Messages
for message in consumer:
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

        if SPEAK is True:
            speak(results['objects'])

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
