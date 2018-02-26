#!/bin/bash

# ------------------------
# Global Varibles

HOME="/home/cloudera"
KAFKA_TOPIC="pycturestream"


# ------------------------
# Install Kafka

sudo yum clean all
sudo yum install -y kafka
sudo yum install -y kafka-server


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
kafka-topics --create --zookeeper localhost:2181 --topic $KAFKA_TOPIC --partitions 1 --replication-factor 1


# ------------------------
# Install Anaconda itself plus additional packages
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

## Install packages
conda install -y -c conda-forge jupyterlab opencv
conda install -y nose keras pillow h5py py4j


# ------------------------
# Setup Jupyter

## We need a startup-script to launch jupyter lab/notebook with spark-support.
## Download script from git, make it executable and create notebooks folder
rm -f "$HOME/start_jupyter.sh"
wget https://raw.githubusercontent.com/dynobo/PyctureStream/master/start_jupyter.sh && chmod +x ./start_jupyter.sh

## Create folder for storing the notebooks
if [ ! -d "$HOME/notebooks" ]; then
    mkdir "$HOME/notebooks"
fi

## Put Startup-Script in rc.local for autostart on boot (but only, if not already in there).
CMD='/sbin/runuser cloudera -s /bin/bash -c "/home/cloudera/start_jupyter.sh &"'
grep -q -F "$CMD" /etc/rc.d/rc.local || echo "$CMD" | sudo tee -a /etc/rc.d/rc.local


# ------------------------
# DONE, ask for reboot (without reboot)

echo "-------------------------------------------------------------------"
echo "DONE! To finish the setup, a reboot is required."
read -p "Press any key to reboot the machine now... (or CTRL+C to exit)" -n1 -s
sudo shutdown -r now
