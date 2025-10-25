# Pace Timer - Refactored Structure

This is the refactored version of the pace_timer application with improved organization and mobile responsiveness.

## File Structure

```
pace_timer/
├── pace_timer.py          # Main application with Flask API and Pygame UI
├── run.py                 # Simple run script for the application
├── setup.sh               # Service installation script
├── uninstall.sh           # Service removal script
├── service.sh             # Service management script
├── pace-timer.service     # Systemd service file
├── requirements.txt       # Python dependencies
├── templates/
│   ├── view.html          # HTML template for web interface
│   └── configure.html     # HTML template for configuration page
├── static/
│   ├── css/
│   │   └── style.css      # Responsive CSS with mobile controls
│   └── js/
│       ├── app.js         # JavaScript for timer updates and mobile controls
│       └── config.js      # JavaScript for configuration page
└── README.md              # This file
```

## Features

### Mobile Responsive Design
- Responsive layout that adapts to different screen sizes
- Mobile-first design with touch-friendly controls
- Optimized typography and spacing for mobile devices

### Mobile Controls
- **Reset Button**: Resets the timer to 00:00
- **Pause/Resume Button**: Toggles timer pause state
- Controls are only visible on mobile devices (screens < 768px)
- Buttons call the existing API endpoints for timer control

### API Endpoints
- `GET /status` - Get current timer status
- `GET /view` - Web interface (now template-based)
- `GET /configure` - Configuration page
- `GET /config` - Get current configuration settings
- `POST /config` - Update configuration settings
- `POST /reset` - Reset timer
- `POST /pause` - Pause timer
- `POST /resume` - Resume timer
- `POST /add_time` - Add 1 minute to elapsed time
- `POST /subtract_time` - Subtract 1 minute from elapsed time
- `POST /set_remaining?seconds=N` - Set remaining time
- `POST /set_total?seconds=N` - Set total time
- `POST /set_ends?count=N` - Set number of ends

## Installation

### Quick Setup
1. **Clone or Download**: Place the pace_timer folder in your home directory
2. **Install Dependencies**: Run the setup script to install as a system service
3. **Access**: Open your browser to `http://localhost:5000/view`

### Prerequisites
- Python 3.6 or higher
- pygame and flask packages (installed automatically by setup script)
- systemd (for service installation)

## Usage

### Manual Execution
Run the application from the project directory:
```bash
cd pace_timer
python3 pace_timer.py
```

Or use the convenient run script:
```bash
cd pace_timer
python3 run.py
```

### System Service Installation
Install as a systemd service that runs at boot:
```bash
cd pace_timer
./setup.sh
```

### Service Management
Use the service management script for easy control:
```bash
./service.sh start      # Start the service
./service.sh stop       # Stop the service
./service.sh restart    # Restart the service
./service.sh status     # Check service status
./service.sh logs       # View service logs
./service.sh enable     # Enable at boot
./service.sh disable    # Disable at boot
```

### Uninstall Service
Remove the systemd service:
```bash
./uninstall.sh
```

The web interface is now mobile-responsive and includes control buttons for mobile users. The main pygame display remains unchanged for the fullscreen display.

## Mobile Features

- **Responsive Layout**: Adapts to phone, tablet, and desktop screens
- **Touch Controls**: Large, easy-to-tap buttons for timer control
- **Optimized Display**: Text and elements scale appropriately for mobile viewing
- **API Integration**: Mobile buttons directly call the Flask API endpoints

## Configuration Features

- **⚙️ Settings Button**: Cogwheel button on the timer view for easy access to configuration
- **Configuration Page**: Dedicated page for managing app settings
- **Configurable Settings**:
  - Total time duration (in seconds)
  - Number of progress ends/boxes
  - Logo URL for display
- **Real-time Updates**: Configuration changes take effect immediately
- **Form Validation**: Input validation and error handling
- **Mobile Responsive**: Configuration page works on all device sizes
