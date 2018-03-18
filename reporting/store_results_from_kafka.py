"""Really simple Kafka consumer to transform result and store them as json."""

from kafka import KafkaConsumer
import json
import logging
import os.path
logging.basicConfig(format='%(levelname)s - %(asctime)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# Where to store the events
JSON_FILE = './events.json'

# ==========================================


def save_to_file(entries, file_name):
    """Append entries to json file."""
    with open(file_name) as f:
        feeds = json.load(f)
    feeds.extend(entries)
    with open(file_name, mode='w', encoding='utf-8') as f:
        json.dump(feeds, f, indent=4)
    logger.info(f'Appended {len(entries)} entries to event.json.')

def trans_time(str):
    """Transform the timestamp to the format used in Reporting."""
    str = str.replace('T', ' ')
    return str


# Init Data file, if not existing
if not os.path.isfile(JSON_FILE):
    with open(JSON_FILE, mode='w', encoding='utf-8') as f:
        json.dump([], f)


# Open Kafka Consumer & listen to topic
consumer = KafkaConsumer('resultstream',
                         bootstrap_servers=['127.0.0.1:9092'])

# Process Messages
for message in consumer:
    results = json.loads(message.value)
    try:
        entries = []
        # If we get empty object list, we add dummy value with a
        # "Nothing detected" event
        if len(results['objects']) == 0:
            results['objects'] = [{'label': 'Nothing detected'}]

        # Append one entry for every objects
        for obj in results['objects']:
            entries.append({
                "event_type": obj['label'],
                "timestamp": trans_time(results['timestamp']),
                "camera_id": results['camera_id']
            })
        save_to_file(entries, JSON_FILE)

    except Exception as e:
        logger.error(e)

# consume earliest available messages, don't commit offsets
KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)

# consume json messages
KafkaConsumer(value_deserializer=lambda m: json.loads(m.decode('ascii')))
