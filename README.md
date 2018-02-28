# Pycture Stream

> Demo-architecture for distribute image stream processing using Kafka and PySpark



## Setup Infrastructure
*Prerequisites:* Local computer with enough ressources (8 GB, better 16 GB RAM, 10-15 GB free space) and a current version of [Oracle VirtualBox](https://www.virtualbox.org/).

### Install Cloudera Quickstart in VirtualBox
**1. Install Image**
- Download [Cloudera Quickstart VM - CDH 5.12](https://www.cloudera.com/downloads/quickstart_vms/5-12.html) for Virtual Box
- Import the Applicance in VirtualBox

**2. Change VM-Settings in VirtualBox**
- Give the VM as much ressources as possible!
- Make sure, "Network" is set to "NAT"
- Add "Port Forwarding" (we'll use `90` as prefix for vm-ports):
    - SSH: Host 127.0.0.1:9022 to Guest 10.0.2.15:22
    - HUE:  Host 127.0.0.1:9033 to Guest 10.0.2.15:8888 *(we want 9088 for jupyter)*
    - JUPYTER:  Host 127.0.0.1:9088 to Guest 10.0.2.15:8889
    - KAFKA:   Host 127.0.0.1:9092 to Guest 10.0.2.15:9092
- (Optional) Configure a shared folder for the jupyter notebook folder. In running guest VM do: "Devices" -> "Shared Folders" -> "Shared Folders Settings..."
- (Optional) Install Guest Additions for better integration with host system. In running guest VM do: "Devices" -> "Insert Guest Additions..."



## Setup Software Components

### In Cloudera VM
- SSH into Kafka VM: `ssh cloudera@192.168.0.1 -p 9022` (Default User+PW: cloudera)
- Run [setup_cloudera_vm.sh](setup_cloudera_vm.sh) in VM:
```bash
wget https://raw.githubusercontent.com/dynobo/PyctureStream/master/setup_cloudera.sh && chmod +x ./setup_cloudera.sh && ./setup_cloudera.sh
```
- When the setup is finished, accept the input to reboot the VM.

### On Local Machine
- Install Anaconda Env (TODO!)



## Tipps for Operations
**Connect to Hue**
- Useful for browsing HDFS or debugging Spark Jobs
- In host browser: `http://127.0.0.1:9033/`

**Connect to VMs Jupyter**
- The development of the Analytics / Kafka Consumer will be done here
- In host browser: `http://127.0.0.1:9088/`



## Testing
*A set of test procedure, useful for debugging and identifying problems.*

### Test Kafka
1. Create a topic:
```bash
kafka-topics --create --zookeeper localhost:2181 --topic wordcounttopic --partitions 1 --replication-factor 1
```

2. Open console consumer:
```bash
/usr/bin/kafka-console-consumer --zookeeper localhost:2181 --topic wordcounttopic
```

3. Open console producer:
```bash
kafka-console-producer --broker-list localhost:9092 --topic wordcounttopic
```

4. Produce some events, and see, if consumer receives them

### Test Spark Streaming + Kafka

1. Create a topic (if not already done):
```bash
kafka-topics --create --zookeeper localhost:2181 --topic wordcounttopic --partitions 1 --replication-factor 1
```

2. Open [./notebooks/kafka_wordcount.ipynb](./notebooks/kafka_wordcount.ipynb) in Jupyter of VM (as Consumer)

3. Open console producer:
```bash
kafka-console-producer --broker-list localhost:9092 --topic wordcounttopic
```

4. Produce some events, and see, if consumer receives & processes them correctly

5. Check Job-Browser in Hue  (http://127.0.0.1:9033/) for status of Spark

# Links & Ressources
- https://scotch.io/tutorials/build-a-distributed-streaming-system-with-apache-kafka-and-python
- https://databricks.com/blog/2016/01/25/deep-learning-with-apache-spark-and-tensorflow.html
- https://github.com/tensorflow/models/tree/master/official/resnet
- https://github.com/tensorflow/models/tree/master/research/object_detection
- https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb
