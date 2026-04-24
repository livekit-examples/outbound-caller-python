#!/bin/bash
#
# WSL2 Setup Script for LiveKit Agent
#
# This script sets up the Python environment in WSL2 and installs
# all required dependencies for running the LiveKit outbound caller agent.
#
# Usage:
#   1. Open WSL2 terminal (Ubuntu)
#   2. cd /mnt/d/Coding-Projects/outbound-caller-python
#   3. chmod +x wsl-setup.sh
#   4. ./wsl-setup.sh

echo "========================================="
echo "LiveKit Agent - WSL2 Setup"
echo "========================================="
echo ""

# Check if running in WSL
if ! grep -q microsoft /proc/version; then
    echo "❌ ERROR: This script must be run in WSL2, not Windows!"
    echo "Please open a WSL2 terminal and try again."
    exit 1
fi

echo "✓ Running in WSL2"
echo ""

# Update package lists
echo "📦 Updating package lists..."
sudo apt-get update

# Install Python 3.11 if not present
if ! command -v python3.11 &> /dev/null; then
    echo "📦 Installing Python 3.11..."
    sudo apt-get install -y python3.11 python3.11-venv python3-pip
else
    echo "✓ Python 3.11 already installed"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3.11 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "To run the agent:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Start the agent:"
echo "     python agent.py start"
echo ""
echo "  Or use the convenience script:"
echo "     ./start-agent.sh start"
echo ""
