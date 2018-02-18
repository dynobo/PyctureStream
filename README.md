# Pycture Stream

> Demo-architecture for distribute image stream processing using Kafka and PySpark

## Setup

### Cloudera Quickstart

### VirtualBox
**Install Image**
- [Cloudera Quickstart VM - CDH 5.12](https://www.cloudera.com/downloads/quickstart_vms/5-12.html)

**Change VirtualBox Settings**
- Change Network to "NAT"
- Add port forwarding:
    - SSH: Host 127.0.0.1:2222 to Guest 10.0.2.15:22
    - HUE:  Host 127.0.0.1:8888 to Guest 10.0.2.15:8888
    - JUPYTER:  Host 127.0.0.1:8889 to Guest 10.0.2.15:8889
    - KAFKA:   Host 127.0.0.1:9092 to Guest 10.0.2.15:9092

**Configure Cloudera**
- SSH into Kafka VM: `ssh cloudera@192.168.0.1 -p 2222` (Default PW: cloudera)
- Run [setup_cloudera.sh](setup_cloudera.sh) in VM:

```bash
wget https://raw.githubusercontent.com/dynobo/PyctureStream/master/setup_cloudera.sh && chmod +x ./setup_cloudera.sh && ./setup_cloudera.sh
```

Important: Use default Options for Anaconda Installation,  except for the "Add to Path?", where you should choose "Yes", instead the default.

## Test Kafka:
- Create topic

```bash
kafka-topics --create --zookeeper localhost:2181 --topic wordcounttopic --partitions 1 --replication-factor 1
```

- Open [./notebooks/kafka_wordcount.ipynb](./notebooks/kafka_wordcount.ipynb) in Jupyter and run as Consumer.
- Use console as Producer to and create some stream events:

 ```bash
 kafka-console-producer --broker-list localhost:9092 --topic wordcounttopic
 ```

## Operations
**Connect to Hue**
- In host browser: `http://127.0.0.1:8888/`

**Connect to Jupyter**
- In host browser: `http://127.0.0.1:8889/`

**Kafka Configuration**
- `sudo nano /etc/kafka/conf.dist/server.properties`

```
# Settings for PyctureStream Projecte
listeners=PLAINTEXT://0.0.0.0:9092
advertised.listeners=PLAINTEXT://0.0.0.0:9092
```

**Kafka Consumer in Cloudera VM**
`/usr/bin/kafka-console-consumer --zookeeper localhost:2181 --topic wordcounttopic`

`/usr/bin/kafka-console-producer --broker-list localhost:9092 --topic wordcounttopic`

# LINKS
https://scotch.io/tutorials/build-a-distributed-streaming-system-with-apache-kafka-and-python
