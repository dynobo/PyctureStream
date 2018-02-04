#!/bin/bash

HOME = "/home/cloudera"

# Install Anaconda with Jupyter
if [ ! -d "$HOME/anaconda3" ]; then
    wget https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh && chmod +x Anaconda3-5.0.1-Linux-x86_64.sh && ./Anaconda3-5.0.1-Linux-x86_64.sh
else
    echo "Anaconda3 was already installed."
fi

# Download Start Script for Jupyter with pySpark
rm -f "$HOME/start_jupyter.sh"
wget https://raw.githubusercontent.com/dynobo/PyctureStream/master/start_jupyter.sh && chmod +x ./start_jupyter.sh
mkdir "$HOME/notebooks"

# Enable Cron
sudo rm -f "/etc/init.d/start_jupyter.sh"
wget https://raw.githubusercontent.com/dynobo/PyctureStream/master/jupyter_service && chmod +x ./jupyter_service
sudo mv jupyter_service /etc/init.d/
sudo update-rc.d jupyter_service defaults
