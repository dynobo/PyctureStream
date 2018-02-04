#!/bin/bash

# Install Anaconda with Jupyter
wget https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh && chmod +x Anaconda3-5.0.1-Linux-x86_64.sh && ./Anaconda3-5.0.1-Linux-x86_64.sh

# Download Start Script for Jupyter with pySpark
wget https://raw.githubusercontent.com/dynobo/PyctureStream/master/start_jupyter.sh && chmod +x ./start_jupyter.sh

# Add Jupyter Start Script to Cron for reboot
(crontab -l 2>/dev/null; echo "@reboot /home/cloudera/start_jupyer.sh") | crontab -
