# KDE Connect Manager

A comprehensive management application for KDE Connect on Fedora 42+ machines with both CLI and web interface.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Fedora%2042%2B-red)
![Python](https://img.shields.io/badge/python-3.9%2B-green)

## 🌟 Features

### Core Functionality
- **📱 Device Management**: Discover, pair, and manage all KDE Connect devices
- **🔧 Automatic Setup**: Install and configure KDE Connect, firewalld rules, and dependencies
- **🎯 Manual Device Selection**: User-friendly interface for device discovery and pairing
- **🔌 All Plugins Supported**: File sharing, clipboard sync, notifications, remote input, SMS, media controls, battery status, ping, and more
- **❤️ Health Monitoring**: Real-time monitoring with verbose logging of events, errors, and system messages
- **🌐 WebSocket Server**: Real-time bidirectional communication between backend and web UI
- **🔐 SSH Integration**: Remote machine management and configuration
- **🖥️ Screen Sharing**: Frame mirroring using krfb, x11vnc, and PipeWire
- **🛡️ Self-Healing**: Automatic reconnection, failure recovery, certificate regeneration, and service restart
- **💬 Graceful Failure**: Detailed error reporting and user-friendly error messages
- **🎨 Clean Abstraction**: Simple commands and UI hiding technical complexity

### Interfaces
- **🖥️ Web Interface**: Modern, responsive web UI with real-time updates
- **⌨️ CLI Tool**: Comprehensive command-line interface for all operations
- **🔌 REST API**: Full-featured HTTP API for integration
- **🌐 WebSocket API**: Real-time event streaming

## 📋 Requirements

- **Operating System**: Fedora 42 or later
- **Python**: 3.9 or later
- **Network**: Local network or Bluetooth for device connectivity
- **Permissions**: sudo access for initial setup (firewall, package installation)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd kdeconnect-manager
```

Or if you already have the files:
```bash
cd /home/ubuntu/kdeconnect-manager
```

### 2. Run Installation Script

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

This will:
- Install KDE Connect and all dependencies
- Configure firewall rules
- Set up Python environment
- Install CLI tool
- Configure systemd services
- Verify installation

### 3. Start Using

#### CLI
```bash
# List devices
kdecm device list

# Check system health
kdecm health check

# Start web server
kdecm server start
```

#### Web Interface
```bash
# Start the web server
systemctl --user start kdeconnect-manager.service

# Or manually
python3 backend/api/server.py
```

Then open your browser to: **http://localhost:5000**

## 📖 Detailed Documentation

### Architecture

```
kdeconnect-manager/
├── backend/                 # Backend services
│   ├── api/                # Flask REST & WebSocket API
│   ├── kdeconnect/         # DBus interface to KDE Connect
│   ├── monitoring/         # Health monitoring & self-healing
│   ├── ssh/                # Remote machine management
│   └── screenshare/        # Screen sharing integration
├── cli/                    # Command-line interface
├── frontend/               # Web interface
│   ├── static/            # CSS & JavaScript
│   └── templates/         # HTML templates
├── scripts/               # Installation & utility scripts
├── systemd/               # Systemd service files
├── config/                # Configuration templates
├── logs/                  # Application logs
└── requirements.txt       # Python dependencies
```

### Components

#### 1. DBus Interface (`backend/kdeconnect/dbus_interface.py`)

Provides Python wrapper around KDE Connect's DBus API:

```python
from backend.kdeconnect.dbus_interface import KDEConnectDBusInterface

kde = KDEConnectDBusInterface()

# Get all devices
devices = kde.get_devices()

# Get device info
info = kde.get_device_info(device_id)

# Send ping
kde.send_ping(device_id, "Hello!")

# Share file
kde.share_file(device_id, "/path/to/file")

# Get battery status
battery = kde.get_battery_status(device_id)
```

#### 2. Health Monitor (`backend/monitoring/health_monitor.py`)

Continuous monitoring and self-healing:

```python
from backend.monitoring.health_monitor import HealthMonitor

monitor = HealthMonitor(check_interval=30)

# Add event callback
def on_event(event):
    print(f"Event: {event['type']}")

monitor.add_event_callback(on_event)

# Start monitoring
monitor.start_monitoring()

# Perform health check
status = monitor.perform_health_check()

# Attempt self-healing
actions = monitor.self_heal(status)
```

#### 3. SSH Remote Manager (`backend/ssh/remote_manager.py`)

Manage KDE Connect on remote machines:

```python
from backend.ssh.remote_manager import RemoteKDEConnectManager

# Connect to remote host
remote = RemoteKDEConnectManager(
    hostname="192.168.1.100",
    username="user",
    key_filename="/path/to/key"
)

remote.connect()

# Install KDE Connect
remote.install_kdeconnect()

# Configure firewall
remote.configure_firewall()

# Start daemon
remote.start_daemon()

# Check health
health = remote.run_health_check()
```

#### 4. Screen Sharing (`backend/screenshare/screen_manager.py`)

Integrated screen sharing capabilities:

```python
from backend.screenshare.screen_manager import ScreenShareIntegration

screen = ScreenShareIntegration()

# Auto-detect and setup
result = screen.setup_screen_sharing()

# Get connection info
status = screen.get_status()

# Stop all sharing
screen.stop_all()
```

### CLI Commands

#### Device Management

```bash
# List all devices
kdecm device list

# List with full details
kdecm device list --all

# Get device info
kdecm device info DEVICE_ID

# Pair device
kdecm device pair DEVICE_ID

# Unpair device
kdecm device unpair DEVICE_ID

# Ping device
kdecm device ping DEVICE_ID

# Ring device
kdecm device ring DEVICE_ID

# Get battery status
kdecm device battery DEVICE_ID
```

#### Sharing

```bash
# Share file
kdecm share file DEVICE_ID /path/to/file

# Share text
kdecm share text DEVICE_ID "Hello World"
```

#### Health & Monitoring

```bash
# Check system health
kdecm health check

# Auto-fix issues
kdecm health fix

# Restart daemon
kdecm health restart
```

#### Server Management

```bash
# Start web server
kdecm server start

# With custom host/port
kdecm server start --host 0.0.0.0 --port 8080
```

#### Installation

```bash
# Check installation status
kdecm install check

# Run full setup
kdecm install setup
```

### REST API Endpoints

#### Device Endpoints

```
GET    /api/devices              - List all devices
GET    /api/devices/available    - List available devices
GET    /api/devices/:id          - Get device info
POST   /api/devices/:id/pair     - Request pairing
POST   /api/devices/:id/unpair   - Unpair device
POST   /api/devices/:id/ping     - Send ping
POST   /api/devices/:id/ring     - Ring device
GET    /api/devices/:id/battery  - Get battery status
GET    /api/devices/:id/notifications - Get notifications
POST   /api/devices/:id/share/file - Share file
POST   /api/devices/:id/share/text - Share text
```

#### Health Endpoints

```
GET    /api/health               - Get current health status
GET    /api/health/history       - Get health history
POST   /api/health/restart       - Restart daemon
```

#### Monitoring Endpoints

```
POST   /api/monitoring/start     - Start health monitoring
POST   /api/monitoring/stop      - Stop health monitoring
```

#### Example API Usage

```bash
# Get all devices
curl http://localhost:5000/api/devices

# Send ping
curl -X POST http://localhost:5000/api/devices/DEVICE_ID/ping \
  -H "Content-Type: application/json" \
  -d '{"message": "Test ping"}'

# Get health status
curl http://localhost:5000/api/health
```

### WebSocket Events

#### Client → Server

```javascript
// Connect to WebSocket
const socket = io('http://localhost:5000');

// Subscribe to device updates
socket.emit('subscribe_devices');

// Subscribe to health updates
socket.emit('subscribe_health');

// Request device update
socket.emit('request_device_update', {
    device_id: 'device_id_here'
});
```

#### Server → Client

```javascript
// Connection status
socket.on('connection_status', (data) => {
    console.log('Status:', data.status);
});

// Device updates
socket.on('devices_update', (data) => {
    console.log('Devices:', data.devices);
});

// Health updates
socket.on('health_update', (health) => {
    console.log('Health:', health);
});

// Health events
socket.on('health_event', (event) => {
    console.log('Event:', event.type, event.data);
});

// Errors
socket.on('error', (error) => {
    console.error('Error:', error.message);
});
```

### Configuration

#### Environment Variables

```bash
# Flask configuration
export FLASK_ENV=production
export FLASK_DEBUG=0

# Server configuration
export KDECM_HOST=0.0.0.0
export KDECM_PORT=5000

# Monitoring configuration
export KDECM_CHECK_INTERVAL=30
export KDECM_LOG_LEVEL=INFO
```

#### Systemd Services

##### KDE Connect Daemon

```bash
# Enable and start
systemctl --user enable kdeconnect.service
systemctl --user start kdeconnect.service

# Check status
systemctl --user status kdeconnect.service

# View logs
journalctl --user -u kdeconnect.service -f
```

##### KDE Connect Manager

```bash
# Enable and start
systemctl --user enable kdeconnect-manager.service
systemctl --user start kdeconnect-manager.service

# Check status
systemctl --user status kdeconnect-manager.service

# View logs
journalctl --user -u kdeconnect-manager.service -f
```

### Firewall Configuration

The installation script automatically configures firewalld. Manual configuration:

```bash
# Add KDE Connect service
sudo firewall-cmd --zone=public --permanent --add-service=kdeconnect

# Or add ports manually
sudo firewall-cmd --zone=public --permanent --add-port=1714-1764/tcp
sudo firewall-cmd --zone=public --permanent --add-port=1714-1764/udp

# Add web interface port
sudo firewall-cmd --zone=public --permanent --add-port=5000/tcp

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-all
```

### Troubleshooting

#### Daemon Not Running

```bash
# Check if daemon is running
pgrep -fl kdeconnectd

# Start daemon manually
kdeconnectd &

# Or use systemd
systemctl --user restart kdeconnect.service

# Check logs
journalctl --user -u kdeconnect.service -n 50
```

#### Devices Not Appearing

1. **Check network connectivity**
   ```bash
   # Ensure both devices on same network
   ip addr show
   ```

2. **Check firewall**
   ```bash
   sudo firewall-cmd --list-all
   ```

3. **Restart daemon**
   ```bash
   kdecm health restart
   ```

4. **Enable discovery mode**
   ```bash
   # In DBus
   qdbus org.kde.kdeconnect /modules/kdeconnect \
     org.kde.kdeconnect.daemon.acquireDiscoveryMode "manual"
   ```

#### Pairing Failures

1. **Check certificates**
   ```bash
   ls -la ~/.config/kdeconnect/
   ```

2. **Clear and re-pair**
   ```bash
   # Unpair device
   kdecm device unpair DEVICE_ID
   
   # Clear certificates
   rm -rf ~/.config/kdeconnect/
   
   # Restart daemon
   kdecm health restart
   
   # Try pairing again
   kdecm device pair DEVICE_ID
   ```

#### Web Interface Not Loading

1. **Check if server is running**
   ```bash
   systemctl --user status kdeconnect-manager.service
   ```

2. **Check port availability**
   ```bash
   ss -tunlp | grep 5000
   ```

3. **Check logs**
   ```bash
   tail -f logs/api.log
   ```

4. **Restart server**
   ```bash
   systemctl --user restart kdeconnect-manager.service
   ```

#### SSH Connection Issues

```bash
# Test SSH connection
ssh user@hostname

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa

# Test with verbose output
ssh -v user@hostname
```

### Security Considerations

1. **Firewall**: Only open required ports (1714-1764)
2. **Network**: Use trusted networks only
3. **Certificates**: KDE Connect uses TLS 1.2 with self-signed certificates
4. **Web Interface**: Bind to localhost (127.0.0.1) for local-only access
5. **SSH**: Use key-based authentication, disable password auth
6. **Systemd**: Services run with user privileges, not root

### Performance Tuning

#### Resource Limits

Edit systemd service files to adjust limits:

```ini
[Service]
MemoryMax=500M
CPUQuota=50%
```

#### Check Interval

Adjust health monitoring interval:

```bash
# In code or config
check_interval = 60  # seconds
```

#### Logging Level

```bash
export KDECM_LOG_LEVEL=WARNING  # INFO, DEBUG, WARNING, ERROR
```

### Development

#### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# With coverage
pytest --cov=backend tests/
```

#### Code Formatting

```bash
# Install black
pip install black

# Format code
black backend/ cli/
```

#### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and formatting
5. Submit a pull request

## 📝 Examples

### Example 1: Basic Device Management

```bash
# List all available devices
kdecm device list

# Pair with a device
kdecm device pair phone_id

# Send a test ping
kdecm device ping phone_id --message "Hello!"

# Check battery
kdecm device battery phone_id

# Share a file
kdecm share file phone_id ~/Documents/report.pdf
```

### Example 2: Health Monitoring

```bash
# Check system health
kdecm health check

# If issues found, attempt auto-fix
kdecm health fix

# Restart daemon if needed
kdecm health restart
```

### Example 3: Remote Management

```python
from backend.ssh.remote_manager import RemoteKDEConnectManager

# Connect to remote machine
remote = RemoteKDEConnectManager(
    hostname="192.168.1.50",
    username="john",
    key_filename="~/.ssh/id_rsa"
)

if remote.connect():
    # Install KDE Connect
    remote.install_kdeconnect()
    
    # Configure firewall
    remote.configure_firewall()
    
    # Start daemon
    remote.start_daemon()
    
    # Check health
    health = remote.run_health_check()
    print(f"Remote health: {health}")
    
    remote.disconnect()
```

### Example 4: Screen Sharing

```python
from backend.screenshare.screen_manager import ScreenShareIntegration

screen = ScreenShareIntegration()

# Auto-detect and setup
result = screen.setup_screen_sharing()

if result['success']:
    print(f"Screen sharing started: {result['connection_info']}")
    print(f"Connect with: {result['connection_info']['url']}")
```

### Example 5: Web API Integration

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Get all devices
response = requests.get(f"{BASE_URL}/devices")
devices = response.json()

# Send ping to first device
if devices['devices']:
    device_id = devices['devices'][0]['id']
    response = requests.post(
        f"{BASE_URL}/devices/{device_id}/ping",
        json={"message": "API Test"}
    )
    print(response.json())
```

## 🔧 Advanced Usage

### Custom Health Checks

```python
from backend.monitoring.health_monitor import HealthMonitor

monitor = HealthMonitor()

# Add custom event handler
def custom_handler(event):
    if event['type'] == 'daemon_restart_failed':
        # Send alert email, Slack notification, etc.
        send_alert(event)

monitor.add_event_callback(custom_handler)
monitor.start_monitoring()
```

### Fleet Management

```python
from backend.ssh.remote_manager import RemoteFleet, RemoteKDEConnectManager

# Create fleet
fleet = RemoteFleet()

# Add hosts
fleet.add_host('server1', RemoteKDEConnectManager('192.168.1.10', 'user'))
fleet.add_host('server2', RemoteKDEConnectManager('192.168.1.11', 'user'))
fleet.add_host('server3', RemoteKDEConnectManager('192.168.1.12', 'user'))

# Connect all
fleet.connect_all()

# Run health check on all hosts
health_status = fleet.health_check_all()

# Execute command on all hosts
results = fleet.run_command_on_all('kdeconnect-cli --list-devices')
```

## 📚 Additional Resources

- [KDE Connect Official Documentation](https://userbase.kde.org/KDEConnect)
- [KDE Connect GitHub Repository](https://github.com/KDE/kdeconnect-kde)
- [DBus Specification](https://dbus.freedesktop.org/doc/dbus-specification.html)
- [Fedora Documentation](https://docs.fedoraproject.org/)

## 🐛 Bug Reports & Feature Requests

Please report issues and request features through the issue tracker.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- KDE Connect development team
- Fedora Project
- Flask and SocketIO communities
- All contributors and users

## 📞 Support

For support, please:
1. Check the troubleshooting section
2. Review the logs in `logs/`
3. Check existing issues
4. Create a new issue with details

---

**Made with ❤️ for the KDE Connect community**
