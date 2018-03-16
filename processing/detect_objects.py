"""Object Detection on Spark using TensorFlow.

Consumes video frames from an Kafka Endpoint, process it on spark, produces
a result containing annotate video frame and sends it to another topic of the
same Kafka Endpoint.

Run with: /usr/bin/spark-submit detect_objects.py

Build on information from:
- https://stackoverflow.com/questions/37337086/how-to-properly-use-pyspark-to-send-data-to-kafka-broker
- https://scotch.io/tutorials/build-a-distributed-streaming-system-with-apache-kafka-and-python
- https://databricks.com/blog/2016/01/25/deep-learning-with-apache-spark-and-tensorflow.html
- https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb
"""

# Utility imports
from __future__ import print_function
import base64
import json
import numpy as np
from StringIO import StringIO
from PIL import Image

# Streaming imports
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from kafka import KafkaProducer

# Object detection imports
import tensorflow as tf
from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util


class Spark_Object_Detector():
    """Stream WebCam Images to Kafka Endpoint.

    Keyword arguments:
    source -- Index of Video Device or Filename of Video-File
    interval -- Interval for capturing images in seconds (default 5)
    server -- Host + Port of Kafka Endpoint (default '127.0.0.1:9092')
    """

    def __init__(self,
                 interval=5,
                 model_file='',
                 labels_file='',
                 number_classes=90,
                 detect_treshold=.5,
                 topic_to_consume='pycturestream',
                 topic_for_produce='resultstream',
                 kafka_endpoint='127.0.0.1:9092'):
        """Initialize Spark & TensorFlow environment."""
        self.interval = interval
        self.topic_to_consume = topic_to_consume
        self.topic_for_produce = topic_for_produce
        self.kafka_endpoint = kafka_endpoint
        self.treshold = detect_treshold
        self.v_sectors = ['top', 'middle', 'bottom']
        self.h_sectors = ['left', 'center', 'right']

        # Create Kafka Producer for sending results
        self.producer = KafkaProducer(bootstrap_servers=kafka_endpoint)

        # Load Labels & Categories
        label_map = label_map_util.load_labelmap(labels_file)
        categories = label_map_util.convert_label_map_to_categories(label_map,
                                                                    max_num_classes=number_classes,
                                                                    use_display_name=True
                                                                    )
        self.category_index = label_map_util.create_category_index(categories)

        # Load Spark Context & Logging
        sc = SparkContext(appName='PyctureStream')
        self.ssc = StreamingContext(sc, 3)
        log4jLogger = sc._jvm.org.apache.log4j
        self.logger = log4jLogger.LogManager.getLogger(__name__)

        # Load Frozen Network Model & Broadcast to Worker Nodes
        with tf.gfile.FastGFile(model_file, 'rb') as f:
            model_data = f.read()
        self.model_data_bc = sc.broadcast(model_data)

    def start_processing(self):
        """Start consuming from Kafka endpoint and detect objects."""
        kvs = KafkaUtils.createDirectStream(self.ssc,
                                            [self.topic_to_consume],
                                            {'metadata.broker.list': self.kafka_endpoint}
                                            )
        kvs.foreachRDD(self.handler)
        self.ssc.start()
        self.ssc.awaitTermination()

    def load_image_into_numpy_array(self, image):
        """Convert PIL image to numpy array."""
        (im_width, im_height) = image.size
        return np.array(image.getdata()).reshape(
            (im_height, im_width, 3)).astype(np.uint8)

    def box_to_sector(self, box):
        """Transform object box in image into sector description."""
        width = box[3] - box[1]
        h_pos = box[1] + width / 2.0
        height = box[2] - box[0]
        v_pos = box[0] + height / 2.0
        h_sector = min(int(h_pos * 3), 2)  # 0: left, 1: center, 2: right
        v_sector = min(int(v_pos * 3), 2)  # 0: top, 1: middle, 2: bottom
        return (self.v_sectors[v_sector], self.h_sectors[h_sector])

    def get_annotated_image_as_text(self, image_np, output):
        """Paint the annotations on the image and serialize it into text."""
        vis_util.visualize_boxes_and_labels_on_image_array(
            image_np,
            output['detection_boxes'],
            output['detection_classes'],
            output['detection_scores'],
            self.category_index,
            instance_masks=output.get('detection_masks'),
            use_normalized_coordinates=True,
            line_thickness=3)

        # Serialize into text, so it can be send as json
        img = Image.fromarray(image_np)
        text_stream = StringIO()
        img.save(text_stream, 'JPEG')
        contents = text_stream.getvalue()
        text_stream.close()
        img_as_text = base64.b64encode(contents).decode('utf-8')
        return img_as_text

    def format_object_desc(self, output):
        """Transform object detection output into nice list of dicts."""
        objs = []
        for i in range(len(output['detection_classes'])):
            # just for for nice output
            score = round(output['detection_scores'][i], 2)
            if score > self.treshold:  # Only keep objects over treshold
                # Get label for category id
                cat_id = output['detection_classes'][i]
                label = self.category_index[cat_id]['name']

                # Get position of object box as [ymin, xmin, ymax, xmax]
                box = output['detection_boxes'][i]

                objs.append({
                    'label': label,
                    'score': score,
                    'sector': self.box_to_sector(box)
                })
        return objs

    def detect_objects(self, payload):
        """Use TensorFlow Model to detect objects."""
        event = json.loads(payload[1])

        # Load the image data from the json into PIL image & numpy array
        decoded = base64.b64decode(event['image'])
        stream = StringIO(decoded)
        image = Image.open(stream)
        image_np = self.load_image_into_numpy_array(image)

        # Load Network Graph
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(self.model_data_bc.value)
        tf.import_graph_def(graph_def, name='')

        # Runs a tensor flow session
        with tf.Session() as sess:
            # Get handles to input and output tensors
            ops = tf.get_default_graph().get_operations()
            all_tensor_names = {
                output.name for op in ops for output in op.outputs
            }
            tensor_dict = {}
            for key in ['num_detections',
                        'detection_boxes',
                        'detection_scores',
                        'detection_classes',
                        'detection_masks'
                        ]:
                tensor_name = key + ':0'
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = (tf.get_default_graph()
                                          .get_tensor_by_name(tensor_name)
                                        )
            if 'detection_masks' in tensor_dict:
                # The following processing is only for single image
                detection_boxes = tf.squeeze(
                    tensor_dict['detection_boxes'], [0]
                )
                detection_masks = tf.squeeze(
                    tensor_dict['detection_masks'], [0]
                )
                # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
                real_num_detection = tf.cast(
                    tensor_dict['num_detections'][0], tf.int32
                )
                detection_boxes = tf.slice(
                    detection_boxes,
                    [0, 0],
                    [real_num_detection, -1]
                )
                detection_masks = tf.slice(
                    detection_masks,
                    [0, 0, 0],
                    [real_num_detection, -1, -1]
                )
                detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                    detection_masks,
                    detection_boxes,
                    image.shape[0],
                    image.shape[1]
                )
                detection_masks_reframed = tf.cast(
                    tf.greater(detection_masks_reframed, 0.5),
                    tf.uint8
                )
                # Follow the convention by adding back the batch dimension
                tensor_dict['detection_masks'] = tf.expand_dims(
                    detection_masks_reframed,
                    0
                )

            image_tensor = (tf.get_default_graph()
                            .get_tensor_by_name('image_tensor:0')
                            )
            # Run inference
            output = sess.run(
                tensor_dict,
                feed_dict={image_tensor: np.expand_dims(image, 0)}
            )
            # all outputs are float32 numpy arrays, so convert types as appropriate
            output['num_detections'] = int(output['num_detections'][0])
            output['detection_classes'] = output['detection_classes'][0].astype(
                np.uint8)
            output['detection_boxes'] = output['detection_boxes'][0]
            output['detection_scores'] = output['detection_scores'][0]

            # tf.session ends here

        # Prepare object for sending to endpoint
        result = {'timestamp': event['timestamp'],
                  'camera_id': event['camera_id'],
                  'objects': self.format_object_desc(output),
                  'image': self.get_annotated_image_as_text(image_np, output)
                  }

        return json.dumps(result)

    def handler(self, timestamp, message):
        """Collect messages, detect object and send to kafka endpoint."""
        records = message.collect()
        for record in records:
            self.producer.send(self.topic_for_produce,
                               self.detect_objects(record))
            self.producer.flush()


if __name__ == '__main__':
    sod = Spark_Object_Detector(
        interval=5,
        model_file='/home/cloudera/PyctureStream-master/frozen_inference_graph.pb',
        labels_file='/home/cloudera/PyctureStream-master/mscoco_label_map.pbtxt',
        number_classes=90,
        detect_treshold=.5,  # .5 This is default treshold for annotations in image
        topic_to_consume='pycturestream',
        topic_for_produce='resultstream',
        kafka_endpoint='127.0.0.1:9092')
    sod.start_processing()
