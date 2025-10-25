#!/bin/bash

# Pace Timer Uninstall Script
# This script removes the Pace Timer systemd service

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="pace-timer"
SERVICE_DIR="/etc/systemd/system"

echo -e "${BLUE}Pace Timer Uninstall Script${NC}"
echo "=============================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root. Please run as a regular user.${NC}"
   exit 1
fi

echo -e "${YELLOW}Removing Pace Timer service...${NC}"

# 1. Stop the service if it's running
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo "Stopping Pace Timer service..."
    sudo systemctl stop $SERVICE_NAME
fi

# 2. Disable the service
echo "Disabling service from starting at boot..."
sudo systemctl disable $SERVICE_NAME

# 3. Remove the service file
echo "Removing systemd service file..."
sudo rm -f $SERVICE_DIR/$SERVICE_NAME.service

# 4. Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# 5. Reset failed state (if any)
sudo systemctl reset-failed $SERVICE_NAME

echo ""
echo -e "${GREEN}Uninstall Complete!${NC}"
echo "======================"
echo ""
echo "The Pace Timer service has been removed from the system."
echo "The application files in $PWD are still available."
echo ""
echo "To completely remove the application:"
echo "  rm -rf /home/jonj/pace_timer"
echo ""
echo -e "${YELLOW}Note: The service will no longer start at boot.${NC}"

