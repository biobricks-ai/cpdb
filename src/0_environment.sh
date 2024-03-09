#!/bin/bash

# Specify Python version
PYTHON_VERSION="3.10.9"

# Create a virtual environment
python3 -m venv venv --prompt "$(basename "$PWD")"

# Activate the virtual environment
source venv/bin/activate

# Ensure you have the desired Python version
python -m pip install python==$PYTHON_VERSION

# Install dependencies from requirements.txt
python -m pip install -r requirements.txt

echo "Virtual environment created and dependencies installed."
