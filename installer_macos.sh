#!/bin/bash

# ==============================================
# Script: installer_macos.sh
# Description: Automated installer for Autoguess on macOS
# Author: Hosein Hadipour
# ==============================================

set -e  # Exit on error

# Detect architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    HOMEBREW_PREFIX="/opt/homebrew"
else
    HOMEBREW_PREFIX="/usr/local"
fi

TOOLS_DIR="$HOME/tools"

echo "==> Detected architecture: $ARCH"
echo "==> Homebrew prefix: $HOMEBREW_PREFIX"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "==> Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for this session
    if [[ "$ARCH" == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "==> Homebrew is already installed."
fi

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
echo "==> Installing system packages via Homebrew..."
brew update
brew install python@3.11 curl graphviz wget cmake

# Install OR-Tools first (required for MiniZinc)
echo "==> Installing OR-Tools..."
if ! command -v ortools &> /dev/null && ! brew list or-tools &> /dev/null; then
    brew install or-tools
else
    echo "OR-Tools is already installed."
fi

# Install MiniZinc
echo "==> Installing MiniZinc..."
if ! command -v minizinc &> /dev/null && ! brew list minizinc &> /dev/null; then
    brew install minizinc
else
    echo "MiniZinc is already installed."
fi

# Install Python packages
echo "==> Setting up Python environment and installing packages..."
python3 -m venv autoguess_env
source autoguess_env/bin/activate
pip install --upgrade pip setuptools wheel

pip install cython graphviz dot2tex minizinc

# Install pysat, pysmt, and z3-solver
echo "==> Installing pysat, pysmt, and z3-solver..."
pip install python-sat[pblib,aiger] pysmt z3-solver gurobipy

deactivate

# Install SageMath
echo "==> Installing SageMath..."
if ! command -v sage &> /dev/null; then
    echo "==> Installing SageMath via Homebrew..."
    brew install --cask sage
    
    # Check various possible installation paths
    SAGE_PATHS=(
        "/Applications/SageMath.app/Contents/MacOS/sage"
        "$HOMEBREW_PREFIX/bin/sage"
        "/usr/local/bin/sage"
    )
    
    SAGE_PATH=""
    for path in "${SAGE_PATHS[@]}"; do
        if [ -f "$path" ]; then
            SAGE_PATH="$path"
            break
        fi
    done
    
    if [ -n "$SAGE_PATH" ]; then
        echo "==> SageMath installed at: $SAGE_PATH"
        # Create symlink if not in standard location
        if [ "$SAGE_PATH" != "$HOMEBREW_PREFIX/bin/sage" ] && [ "$SAGE_PATH" != "/usr/local/bin/sage" ]; then
            sudo ln -sf "$SAGE_PATH" "$HOMEBREW_PREFIX/bin/sage"
        fi
    else
        echo "⚠️  SageMath installation completed, but executable not found in expected locations."
        echo "   Please manually update the PATH_SAGE variable in config.py"
    fi
else
    EXISTING_SAGE=$(which sage)
    echo "SageMath is already installed at: $EXISTING_SAGE"
fi

echo "==> Installation completed successfully."

echo
echo "📌 Reminder:"
echo "- SageMath path will be automatically updated in config.py"
echo "- To use Autoguess, activate the Python virtual environment by running:"
echo "  source $TOOLS_DIR/autoguess_env/bin/activate"
echo "- If you're using Apple Silicon (M1/M2), make sure to restart your terminal"
echo "  or run: source ~/.zshrc"
