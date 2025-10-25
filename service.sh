#!/bin/bash

# Pace Timer Service Management Script
# Easy commands to manage the Pace Timer systemd service

SERVICE_NAME="pace-timer"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${BLUE}Pace Timer Service Manager${NC}"
    echo "========================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     - Start the Pace Timer service"
    echo "  stop      - Stop the Pace Timer service"
    echo "  restart   - Restart the Pace Timer service"
    echo "  status    - Show service status"
    echo "  logs      - Show service logs (follow mode)"
    echo "  enable    - Enable service at boot"
    echo "  disable   - Disable service at boot"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

case "$1" in
    start)
        echo -e "${YELLOW}Starting Pace Timer service...${NC}"
        sudo systemctl start $SERVICE_NAME
        if sudo systemctl is-active --quiet $SERVICE_NAME; then
            echo -e "${GREEN}✓ Service started successfully!${NC}"
        else
            echo -e "${RED}✗ Failed to start service${NC}"
            exit 1
        fi
        ;;
    stop)
        echo -e "${YELLOW}Stopping Pace Timer service...${NC}"
        sudo systemctl stop $SERVICE_NAME
        echo -e "${GREEN}✓ Service stopped${NC}"
        ;;
    restart)
        echo -e "${YELLOW}Restarting Pace Timer service...${NC}"
        sudo systemctl restart $SERVICE_NAME
        if sudo systemctl is-active --quiet $SERVICE_NAME; then
            echo -e "${GREEN}✓ Service restarted successfully!${NC}"
        else
            echo -e "${RED}✗ Failed to restart service${NC}"
            exit 1
        fi
        ;;
    status)
        echo -e "${YELLOW}Pace Timer Service Status:${NC}"
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        echo -e "${YELLOW}Following Pace Timer service logs (Ctrl+C to exit):${NC}"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    enable)
        echo -e "${YELLOW}Enabling Pace Timer service at boot...${NC}"
        sudo systemctl enable $SERVICE_NAME
        echo -e "${GREEN}✓ Service enabled at boot${NC}"
        ;;
    disable)
        echo -e "${YELLOW}Disabling Pace Timer service at boot...${NC}"
        sudo systemctl disable $SERVICE_NAME
        echo -e "${GREEN}✓ Service disabled at boot${NC}"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

