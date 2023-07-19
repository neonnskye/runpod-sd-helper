#!/bin/bash

apt update
yes | apt-get install python3.10-tk
git clone https://github.com/bmaltais/kohya_ss.git
cd kohya_ss
python -m venv venv
source venv/bin/activate
chmod +x ./setup.sh
./setup.sh