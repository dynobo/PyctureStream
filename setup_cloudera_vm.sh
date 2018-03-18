#!/bin/bash

# ------------------------
# Global Varibles
HOME="/home/cloudera"
REPO="$HOME/PyctureStream-master/"
KAFKA_TOPIC_1="pycturestream"
KAFKA_TOPIC_2="resultstream"


# ------------------------
# Add user to VirtualBox Shared Folder Group
sudo usermod -a -G vboxsf cloudera


# ------------------------
# Update & install various packages
#    kafka, kafka-Server  - as Message Queue
sudo yum clean all
sudo yum update -y
sudo yum install -y kafka
sudo yum install -y kafka-server


# -----------------------
# Deactivate Services not needed for demo to save ressources
sudo chkconfig --level 5 hive-metastore off
sudo chkconfig --level 5 hive-server2 off
sudo chkconfig --level 5 impala-catalog off
sudo chkconfig --level 5 impala-server off
sudo chkconfig --level 5 impala-state-store off
sudo chkconfig --level 5 solr-server off
sudo chkconfig --level 5 sqoop2-server off
sudo chkconfig --level 5 sentry-store off
sudo chkconfig --level 5 oozie off


# ------------------------
# Adjust Kafka Configuration in /etc/kafka/conf.dist/server.properties
#    Change Kafka Listener Ports, so Kafka can be reached by
#    Services outside the VM, e.g. our producers

##  Remove existing, conflicting configuration (if it's there)
sudo sed '/^listeners=/ d' /etc/kafka/conf.dist/server.properties
sudo sed '/^advertised.listeners=/ d' /etc/kafka/conf.dist/server.properties
##  Add new configuration
echo "# Settings for PyctureStream Project" | sudo tee -a /etc/kafka/conf.dist/server.properties
echo "listeners=PLAINTEXT://0.0.0.0:9092" | sudo tee -a /etc/kafka/conf.dist/server.properties
echo "advertised.listeners=PLAINTEXT://127.0.0.1:9092" | sudo tee -a /etc/kafka/conf.dist/server.properties


# ------------------------
# Start Kafka Server and create topic

## It will also be automatically started on reboot
sudo service kafka-server start

## For the topic, we use 1 partition and do not replicate, as we have single
## node cluster and only limited ressources
## Retention for image-topic is very low, as we don't need images older than 30 sec
## in our demo-use-case...
kafka-topics --create --zookeeper localhost:2181 --topic $KAFKA_TOPIC_1 --partitions 1 --replication-factor 1 --config retention.ms=30000
kafka-topics --create --zookeeper localhost:2181 --topic $KAFKA_TOPIC_2 --partitions 1 --replication-factor 1


# ------------------------
# Install Anaconda itself plus additional packages.
# We use Python 2, because of compability reasons with the Spark version deliverd
# in the Cloudera image.
# Packages:
#    JupyterLab - We want to this successor of Jupyter Notebook, even in alpha
#    OpenCV - Image Processing Lib
#    nose keras pillow h5py py4j - Machine Learning Libs for use with TensorFlow

## Install Anaconda
if [ ! -d "$HOME/anaconda2" ]; then
    # Download & make executable
    wget https://repo.continuum.io/archive/Anaconda2-5.0.1-Linux-x86_64.sh && chmod +x Anaconda2-5.0.1-Linux-x86_64.sh
    # Run installer in silent mode
    ./Anaconda2-5.0.1-Linux-x86_64.sh -b -p
    # Add conda to path on every reboot
    echo "export PATH=\"$HOME/anaconda2/bin:\$PATH\"" | tee -a $HOME/.bashrc
    # Source our changes in .bashrc
    source "$HOME/.bashrc"
else
    echo "Anaconda3 was already installed."
fi

## Install additional packages
conda install -y -c conda-forge jupyterlab opencv kafka-python
conda install -y -c anaconda tensorflow
conda install -y nose keras pillow h5py py4j


# ------------------------
# Clone PyctureStream Repo (with Notebooks, test images etc.)
cd $HOME
wget https://github.com/dynobo/PyctureStream/archive/master.zip
unzip master.zip
rm master.zip


# ------------------------
# Setup Jupyter

## We need a startup-script to launch jupyter lab/notebook with spark-support.
## Download script from git, make it executable and create notebooks folder
rm -f "$HOME/start_jupyter.sh"
wget https://raw.githubusercontent.com/dynobo/PyctureStream/master/start_jupyter.sh && chmod +x ./start_jupyter.sh

## Put Startup-Script in rc.local for autostart on boot (but only, if not already in there).
CMD='/sbin/runuser cloudera -s /bin/bash -c "/home/cloudera/start_jupyter.sh &"'
grep -q -F "$CMD" /etc/rc.d/rc.local || echo "$CMD" | sudo tee -a /etc/rc.d/rc.local


# ------------------------
# TensorFlow Selected Model & Files

## Download Repo to Home-Directory and extract
cd $HOME
wget https://github.com/tensorflow/models/archive/master.zip
unzip master.zip

## Move Folder for object_detection to python module folder & delete the rest
cp models-master/research/object_detection/data/mscoco_label_map.pbtxt $REPO
mv models-master/research/object_detection ./anaconda2/lib/python2.7/site-packages/
rm -f master.zip
rm -rf models-master

## Protobuf Compilation, see https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/installation.md
cd $HOME/anaconda2/lib/python2.7/site-packages/
protoc object_detection/protos/*.proto --python_out=.

## Download & extract pretrained models
cd $HOME
wget http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v1_coco_2017_11_17.tar.gz
tar -xvzf ssd_mobilenet_v1_coco_2017_11_17.tar.gz
mv ssd_mobilenet_v1_coco_2017_11_17/frozen_inference_graph.pb $REPO
rm -rf ssd_mobilenet_v1_coco_2017_11_17
rm ssd_mobilenet_v1_coco_2017_11_17.tar.gz


# ------------------------
# Set Timezone
#    for easier logging
sudo mv /etc/localtime /etc/localtime.bak
sudo ln -s /usr/share/zoneinfo/Europe/Berlin /etc/localtime


# ------------------------
# DONE, ask for reboot (without reboot)

echo "-------------------------------------------------------------------"
echo "DONE! To finish the setup, a reboot is required."
read -p "Press any key to reboot the machine now... (or CTRL+C to exit)" -n1 -s
sudo shutdown -r now
