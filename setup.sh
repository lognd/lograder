#!/usr/bin/env bash
set -e  # exit on first error

cd /autograder/source

# Update system packages
apt-get update
apt-get install -y python3 python3-pip

# Install Python dependencies
pip3 install -r requirements.txt