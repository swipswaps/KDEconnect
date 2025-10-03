# KDE Connect Manager - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Clone and Navigate
```bash
cd /home/ubuntu/kdeconnect-manager
```

### Step 2: Run Installation
```bash
./scripts/install.sh
```

This will install all dependencies, configure firewall, and set up the system.

### Step 3: Verify Installation
```bash
kdecm install check
```

### Step 4: Start Using!

#### Option A: Web Interface (Recommended)
```bash
# Start the web server
kdecm server start

# Open browser to http://localhost:5000
```

#### Option B: Command Line
```bash
# List devices
kdecm device list

# Pair with a device
kdecm device pair DEVICE_ID

# Send a ping
kdecm device ping DEVICE_ID

# Check system health
kdecm health check
```

## 📱 Pairing Your First Device

1. **Ensure both devices are on the same network**
2. **Open KDE Connect on your phone/tablet**
3. **On your computer:**
   ```bash
   # List available devices
   kdecm device list
   
   # Pair with the device
   kdecm device pair DEVICE_ID_HERE
   ```
4. **Accept the pairing request on your device**
5. **Done! Your devices are now connected**

## 🔧 Common Commands

```bash
# Device management
kdecm device list              # List all devices
kdecm device info DEVICE_ID    # Device details
kdecm device ping DEVICE_ID    # Test connection
kdecm device battery DEVICE_ID # Check battery

# Sharing
kdecm share file DEVICE_ID /path/to/file
kdecm share text DEVICE_ID "Your message"

# Health
kdecm health check             # Check system
kdecm health fix               # Auto-fix issues
kdecm health restart           # Restart daemon

# Server
kdecm server start             # Start web UI
```

## 🌐 Web Interface Features

Access at **http://localhost:5000**

- 📱 **Devices Tab**: View and manage all devices
- ❤️ **Health Tab**: Monitor system health
- 📋 **Logs Tab**: View real-time event logs
- ⚙️ **Settings Tab**: Configure preferences

## ⚡ Advanced Features

### Remote Management via SSH
```bash
# Connect to remote machine and setup KDE Connect
python3 examples/remote_setup.py
```

### Screen Sharing
```bash
# Auto-setup screen sharing
python3 -c "
from backend.screenshare.screen_manager import ScreenShareIntegration
screen = ScreenShareIntegration()
result = screen.setup_screen_sharing()
print(result)
"
```

### Health Monitoring
```bash
# Start continuous monitoring
systemctl --user start kdeconnect-manager.service

# View logs
journalctl --user -u kdeconnect-manager.service -f
```

## 🆘 Troubleshooting

### Devices not showing up?
```bash
# Check firewall
sudo firewall-cmd --list-all

# Restart daemon
kdecm health restart

# Check health
kdecm health check
```

### Pairing failed?
```bash
# Unpair and try again
kdecm device unpair DEVICE_ID

# Clear certificates
rm -rf ~/.config/kdeconnect/

# Restart daemon
kdecm health restart
```

### Web interface not loading?
```bash
# Check if running
systemctl --user status kdeconnect-manager.service

# Restart
systemctl --user restart kdeconnect-manager.service

# Check logs
tail -f logs/api.log
```

## 📚 Learn More

- **Full Documentation**: [README.md](README.md)
- **API Reference**: [README.md#rest-api-endpoints](README.md#rest-api-endpoints)
- **Examples**: `examples/basic_usage.py`
- **Configuration**: `config/config.example.yaml`

## 🎯 Next Steps

1. ✅ Pair your devices
2. ✅ Explore the web interface
3. ✅ Try sending files and notifications
4. ✅ Set up automatic monitoring
5. ✅ Configure screen sharing (optional)
6. ✅ Explore remote management (optional)

---

**Need help?** Check the [README](README.md) or run `kdecm --help`
