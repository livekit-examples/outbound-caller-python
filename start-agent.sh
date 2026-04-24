#!/bin/bash
#
# Start LiveKit AI Agent Script
#
# This script properly sets environment variables before starting the agent.
# It attempts to disable the inference executor to avoid IPC timeout issues
# on Windows/MINGW64 systems (though this may not fully work due to platform
# limitations - WSL2 or Linux is recommended).
#
# Usage:
#   ./start-agent.sh dev      # Development mode with hot-reload
#   ./start-agent.sh start    # Production mode
#
# Note: This agent requires a Unix-like environment (Linux/macOS/WSL2) for
# full functionality. Windows/MINGW64 has known compatibility issues.

# Set environment variable to attempt disabling inference executor
# This may not fully work on Windows/MINGW64 due to IPC system limitations
export LIVEKIT_DISABLE_INFERENCE_EXECUTOR=1

# Start the agent with all provided arguments
python agent.py "$@"
