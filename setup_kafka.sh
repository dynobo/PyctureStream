#!/bin/bash

# Install some useful packages
sudo apt-get update
sudo apt-get install nano

# Enable SSH Server
# https://docs.bitnami.com/virtual-machine/faq/#how-to-enable-the-ssh-server
sudo rm -f /etc/ssh/sshd_not_to_be_run
sudo systemctl enable ssh
sudo systemctl start ssh
