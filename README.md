# PyctureStream

> **Demo-architecture for distribute image stream processing using Kafka and PySpark**. <br>
> Result of a two-month project in a two-person team during my Master programme. The lecture was focused on Big Data Architecture. The goal was to come up with a fictional use-case for Big Data, design an architecture, state reasons for the architectural decisions and implement a Proof-of-Concept.<br>
>In this repository, you'll find the code for the PoC, the [slides](slides.pdf) of our final presentation, and the [documentation in german](documentation.pdf).


## Setup Infrastructure
*Prerequisites:* Local computer with enough ressources (8 GB, better 16 GB RAM, 10-15 GB free space) and a current version of [Oracle VirtualBox](https://www.virtualbox.org/).

### Install Cloudera Quickstart in VirtualBox
**1. Install Image**
- Download [Cloudera Quickstart VM - CDH 5.12](https://www.cloudera.com/downloads/quickstart_vms/5-12.html) for Virtual Box
- Import the Applicance in VirtualBox

**2. Change VM-Settings in VirtualBox**
- Give the VM as much ressources as possible! (My Specs: 32GB RAM, i5 QuadCore ~4Ghz, SSD)
- Make sure, "Network" is set to "NAT"
- Add "Port Forwarding" (we'll use `90` as prefix for vm-ports):
    - SSH: Host 127.0.0.1:9022 to Guest 10.0.2.15:22
    - HUE:  Host 127.0.0.1:9033 to Guest 10.0.2.15:8888 *(we want 9088 for jupyter)*
    - JUPYTER:  Host 127.0.0.1:9088 to Guest 10.0.2.15:8889
    - KAFKA:   Host 127.0.0.1:9092 to Guest 10.0.2.15:9092

## Setup Software

### In Cloudera VM
- SSH into Cloudera VM, e.g. via: `ssh cloudera@127.0.0.1 -p 9022` (Default User+PW: cloudera)
- In **VM**, run [setup_cloudera_vm.sh](setup_cloudera_vm.sh) to install additional packages and do various configuration in (no interaction needed):
```bash
wget https://raw.githubusercontent.com/dynobo/PyctureStream/master/setup_cloudera_vm.sh && chmod +x ./setup_cloudera_vm.sh && ./setup_cloudera_vm.sh
```

- When the setup is finished reboot the VM.

### On Local Machine
- You might need Anaconda Distro with Python 3.6+ for the code that runs locally
- The dependencies are listen in [environment.yml](environment.yml). You can use this file to recreate the environment with Anaconda:
```bash
conda env create -f environment.yml
```

## Pipeline
*Run the different components of the pipeline in parallel (e.g. using multiple consoles):*

#### Video Capturing (Client)
Kafka Producer, that captures images from a connected Webcam (make sure, you have one attached!) and sends them together with metadata into the `pycturestream`-Topic in Kafka. It also stores the latest image in `input.jpg`, for monitoring purposes.

Run [client/stream_webcam_to_kafka.py](client/stream_webcam_to_kafka.py) on **Host**.

#### Object Detection (Processing)
Consumes the `pycturestream`-Topic, detects the objects in the pictures, and pushs the results into `resultstream`-Topic. Leverages Tensorflow and Spark.

Run [processing/detect_objects.py](processing/detect_objects.py) in **VM**

#### Output Results (Client)
Kafka Consumer of `resultstream`-Topic, to display the results (detected objects, probabilities) as console-output and store the latest image in `output.jpg`.

Run [client/receive_results_from_kafka.py](client/receive_results_from_kafka.py) on **Host**, open [client/monitor_imagestream.html](client/monitor_imagestream.html) in Browser to monitor input and output images.

#### Dashboard (Reporting)
Kafka Consumer of `resultstream`-Topic to transforms the data and store the detected objects (without images) in `events.json`.

Run [reporting/store_results_from_kafka.py](reporting/store_results_from_kafka.py) on **Host**

The Dashboard itself was build with [Dash](https://plot.ly/products/dash/), and displays the data of the `events.json`. (The dashboard was implemented by Marcus.)

Open [reporting/dashboard.ipynb](reporting/dashboard.ipynb) in Jupyter Notebook on **Host** or run it directly in non-interactive mode: `jupyter nbconvert --to notebook --execute dashboard.ipynb`


## Testing
*A set of test procedures, useful for debugging and identifying problems.*

### Test WebCam
- Make sure, your webcam is connected. Maybe test with other software, if it's generally working.
- Run the test script, which tests the first 4 video devices for certain parameters, e.g.:
```bash
python ./client/test_webcam.py
```
- Interpreting results:
```
VIDEOIO ERROR: V4L: index 1 is not correct!         <--- camera might not be connected
Unable to stop the stream: Device or resource busy  <--- camera in use by other program
```

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

## Links & Ressources
Some of the ressource that helped me in the implementation.
- https://scotch.io/tutorials/build-a-distributed-streaming-system-with-apache-kafka-and-python
- https://databricks.com/blog/2016/01/25/deep-learning-with-apache-spark-and-tensorflow.html
- https://github.com/tensorflow/models/tree/master/official/resnet
- https://github.com/tensorflow/models/tree/master/research/object_detection
- https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb
