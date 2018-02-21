#!/bin/bash
HOME="/home/cloudera"

# Install Kafka
sudo yum clean all
sudo yum install -y kafka
sudo yum install -y kafka-server

# Change Kafka Listener Ports
sudo sed '/^listeners=/ d' /etc/kafka/conf.dist/server.properties
sudo sed '/^advertised.listeners=/ d' /etc/kafka/conf.dist/server.properties
echo "# Settings for PyctureStream Project" | sudo tee -a /etc/kafka/conf.dist/server.properties
echo "listeners=PLAINTEXT://127.0.0.1:9092" | sudo tee -a /etc/kafka/conf.dist/server.properties
echo "advertised.listeners=PLAINTEXT://127.0.0.1:9092" | sudo tee -a /etc/kafka/conf.dist/server.properties

# Start Kafka Server
sudo service kafka-server start

# Install Anaconda with Jupyter + additional packages
if [ ! -d "$HOME/anaconda2" ]; then
    wget https://repo.continuum.io/archive/Anaconda2-5.0.1-Linux-x86_64.sh && chmod +x Anaconda2-5.0.1-Linux-x86_64.sh && ./Anaconda2-5.0.1-Linux-x86_64.sh
    conda install -c conda-forge jupyterlab opencv
    conda install nose keras pillow h5py py4j
else
    echo "Anaconda3 was already installed."
fi

# Download Start Script for Jupyter with pySpark
rm -f "$HOME/start_jupyter.sh"
wget https://raw.githubusercontent.com/dynobo/PyctureStream/master/start_jupyter.sh && chmod +x ./start_jupyter.sh
if [ ! -d "$HOME/notebooks" ]; then
    mkdir "$HOME/notebooks"
fi

# Enable Cron
CMD='/sbin/runuser cloudera -s /bin/bash -c "/home/cloudera/start_jupyter.sh &"'
grep -q -F "$CMD" /etc/rc.d/rc.local || echo "$CMD" | sudo tee -a /etc/rc.d/rc.local
