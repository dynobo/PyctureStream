from pyspark import SparkContext
#from operator import add
import sys
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import json

from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers='localhost:9092')

def handler(message):
    records = message.collect()
    for record in records:
        producer.send('resultstream', str(record))
        producer.flush()

def main():
    sc = SparkContext(appName="PythonStreamingDirectKafkaWordCount")
    ssc = StreamingContext(sc, 10)
    log4jLogger = sc._jvm.org.apache.log4j
    LOGGER = log4jLogger.LogManager.getLogger(__name__)

    brokers, topic = sys.argv[1:]
    LOGGER.error('-'*80)
    LOGGER.error(topic)
    kvs = KafkaUtils.createDirectStream(ssc, [topic], {"metadata.broker.list": brokers})
    kvs.foreachRDD(handler)

    ssc.start()
    ssc.awaitTermination()
if __name__ == "__main__":

   main()
