#!/bin/bash

# Pace Timer Setup Script
# This script installs the Pace Timer application as a systemd service

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="pace-timer"
SERVICE_FILE="pace-timer.service"
APP_DIR="/home/jonj/pace_timer"
SERVICE_DIR="/etc/systemd/system"

echo -e "${BLUE}Pace Timer Setup Script${NC}"
echo "=========================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root. Please run as a regular user.${NC}"
   echo "The script will use sudo when needed for system operations."
   exit 1
fi

# Check if we're in the right directory
if [[ ! -f "pace_timer.py" ]]; then
    echo -e "${RED}Error: pace_timer.py not found.${NC}"
    echo "Please run this script from the pace_timer project directory."
    exit 1
fi

# Check if systemd is available
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}Error: systemctl not found. This script requires systemd.${NC}"
    exit 1
fi

echo -e "${YELLOW}Installing Pace Timer as a system service...${NC}"

# 1. Set proper permissions on the application directory
echo "Setting permissions on application files..."
sudo chown -R $USER:$USER $APP_DIR
chmod +x $APP_DIR/pace_timer.py
chmod +x $APP_DIR/run.py

# Update service file to use current user
echo "Updating service file for current user ($USER)..."
sed -i "s/User=.*/User=$USER/" $SERVICE_FILE
sed -i "s/Group=.*/Group=$USER/" $SERVICE_FILE

# 2. Install Python dependencies
echo "Installing Python dependencies..."

# Try to install via pip first, fallback to apt if externally managed
if [[ -f "requirements.txt" ]]; then
    echo "Attempting to install dependencies via pip..."
    if pip3 install -r requirements.txt 2>/dev/null; then
        echo "✓ Python dependencies installed via pip"
    else
        echo "Pip installation failed, trying system packages..."
        echo "Installing system packages via apt..."
        
        # Update package list
        sudo apt update
        
        # Install Python packages via apt
        sudo apt install -y python3-pygame python3-flask python3-pip
        
        echo "✓ Python dependencies installed via system packages"
    fi
else
    echo "Installing pygame and flask..."
    if pip3 install pygame flask 2>/dev/null; then
        echo "✓ Python dependencies installed via pip"
    else
        echo "Pip installation failed, trying system packages..."
        echo "Installing system packages via apt..."
        
        # Update package list
        sudo apt update
        
        # Install Python packages via apt
        sudo apt install -y python3-pygame python3-flask python3-pip
        
        echo "✓ Python dependencies installed via system packages"
    fi
fi

# 3. Copy service file to systemd directory
echo "Installing systemd service file..."
sudo cp $SERVICE_FILE $SERVICE_DIR/

# 4. Reload systemd to recognize the new service
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# 5. Enable the service to start at boot
echo "Enabling service to start at boot..."
sudo systemctl enable $SERVICE_NAME

# 6. Start the service
echo "Starting Pace Timer service..."
sudo systemctl start $SERVICE_NAME

# 7. Check service status
echo "Checking service status..."
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✓ Pace Timer service is running successfully!${NC}"
else
    echo -e "${RED}✗ Service failed to start. Checking status...${NC}"
    sudo systemctl status $SERVICE_NAME
    exit 1
fi

echo ""
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================="
echo ""
echo "Service Management Commands:"
echo "  sudo systemctl start $SERVICE_NAME     # Start the service"
echo "  sudo systemctl stop $SERVICE_NAME      # Stop the service"
echo "  sudo systemctl restart $SERVICE_NAME   # Restart the service"
echo "  sudo systemctl status $SERVICE_NAME    # Check service status"
echo "  sudo systemctl enable $SERVICE_NAME    # Enable at boot"
echo "  sudo systemctl disable $SERVICE_NAME   # Disable at boot"
echo ""
echo "Logs:"
echo "  sudo journalctl -u $SERVICE_NAME -f    # Follow logs in real-time"
echo "  sudo journalctl -u $SERVICE_NAME       # View all logs"
echo ""
echo "Web Interface:"
echo "  http://localhost:5000/view             # Timer view"
echo "  http://localhost:5000/configure        # Configuration page"
echo ""
echo -e "${YELLOW}Note: The service will automatically start at boot.${NC}"
