#!/bin/bash

# ==============================================
# Script: installer.sh
# Description: Automated installer for Autoguess
# Author: Hosein Hadipour
# ==============================================

set -e  # Exit on error
TOOLS_DIR="/home/tools"

echo "==> Creating tools directory at $TOOLS_DIR..."
mkdir -p "$TOOLS_DIR"
cd "$TOOLS_DIR"

# Clone Autoguess
echo "==> Cloning Autoguess repository..."
if [ ! -d "autoguess" ]; then
    git clone https://github.com/hadipourh/autoguess
else
    echo "Autoguess already cloned."
fi

# Install system prerequisites
echo "==> Installing system packages..."
apt-get update
apt-get install -y python3-dev python3-full curl graphviz

# Install Python packages
echo "==> Setting up Python environment and installing packages..."
apt-get install -y python3-pip
apt-get install -y python3-venv
python3 -m venv autoguess_env
source autoguess_env/bin/activate
pip install --upgrade pip setuptools wheel

pip install cython python-sat[pblib,aiger] pysmt z3-solver graphviz dot2tex minizinc

# Install pySMT solvers
echo "==> Installing Boolector via pySMT..."
pysmt-install --btor

deactivate

# Install MiniZinc
echo "==> Installing MiniZinc..."
cd "$TOOLS_DIR"
if [ ! -d "MiniZinc" ]; then
    LATEST_MINIZINC_VERSION=$(curl -s https://api.github.com/repos/MiniZinc/MiniZincIDE/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
    wget "https://github.com/MiniZinc/MiniZincIDE/releases/download/$LATEST_MINIZINC_VERSION/MiniZincIDE-$LATEST_MINIZINC_VERSION-bundle-linux-x86_64.tgz"
    mkdir MiniZinc
    tar -xvzf "MiniZincIDE-$LATEST_MINIZINC_VERSION-bundle-linux-x86_64.tgz" -C MiniZinc --strip-components=1
    rm "MiniZincIDE-$LATEST_MINIZINC_VERSION-bundle-linux-x86_64.tgz"
    ln -sf "$TOOLS_DIR/MiniZinc/bin/minizinc" /usr/local/bin/minizinc
else
    echo "MiniZinc already installed."
fi

# Install SageMath
echo "==> Installing SageMath..."
apt-get install -y sagemath

echo "==> Installation completed successfully."

echo
echo "📌 Reminder:"
echo "- If SageMath is already installed, update its path in config.py if needed."