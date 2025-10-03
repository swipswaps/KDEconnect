"""
SSH Remote Manager
Manage KDE Connect on remote machines via SSH
"""

import paramiko
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RemoteKDEConnectManager:
    """Manage KDE Connect on remote machines via SSH"""
    
    def __init__(self, hostname: str, username: str, password: Optional[str] = None, 
                 key_filename: Optional[str] = None, port: int = 22):
        """
        Initialize SSH connection to remote host
        
        Args:
            hostname: Remote host address
            username: SSH username
            password: SSH password (optional if using key)
            key_filename: Path to SSH private key
            port: SSH port (default 22)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.client = None
        self.connected = False
    
    def connect(self) -> bool:
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_params = {
                'hostname': self.hostname,
                'username': self.username,
                'port': self.port,
                'timeout': 10
            }
            
            if self.password:
                connect_params['password'] = self.password
            elif self.key_filename:
                connect_params['key_filename'] = self.key_filename
            
            self.client.connect(**connect_params)
            self.connected = True
            logger.info(f"Connected to {self.hostname}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.hostname}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info(f"Disconnected from {self.hostname}")
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute command on remote host
        
        Returns:
            Dict with stdout, stderr, exit_code
        """
        if not self.connected:
            return {'error': 'Not connected', 'exit_code': -1}
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            exit_code = stdout.channel.recv_exit_status()
            
            return {
                'stdout': stdout.read().decode('utf-8'),
                'stderr': stderr.read().decode('utf-8'),
                'exit_code': exit_code
            }
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {'error': str(e), 'exit_code': -1}
    
    def check_kdeconnect_installed(self) -> bool:
        """Check if KDE Connect is installed"""
        result = self.execute_command('which kdeconnectd')
        return result.get('exit_code') == 0
    
    def install_kdeconnect(self) -> bool:
        """Install KDE Connect on remote machine"""
        logger.info(f"Installing KDE Connect on {self.hostname}")
        
        # Try Fedora/RHEL package manager
        result = self.execute_command('sudo dnf install -y kdeconnect')
        
        if result.get('exit_code') == 0:
            logger.info("KDE Connect installed successfully")
            return True
        
        # Try Debian/Ubuntu package manager
        result = self.execute_command('sudo apt-get update && sudo apt-get install -y kdeconnect')
        
        if result.get('exit_code') == 0:
            logger.info("KDE Connect installed successfully")
            return True
        
        logger.error("Failed to install KDE Connect")
        return False
    
    def start_daemon(self) -> bool:
        """Start KDE Connect daemon"""
        result = self.execute_command('kdeconnectd &')
        return result.get('exit_code') == 0
    
    def stop_daemon(self) -> bool:
        """Stop KDE Connect daemon"""
        result = self.execute_command('killall kdeconnectd')
        return result.get('exit_code') == 0
    
    def restart_daemon(self) -> bool:
        """Restart KDE Connect daemon"""
        self.stop_daemon()
        import time
        time.sleep(2)
        return self.start_daemon()
    
    def get_daemon_status(self) -> Dict[str, Any]:
        """Get daemon status"""
        result = self.execute_command('pgrep -fl kdeconnectd')
        
        return {
            'running': result.get('exit_code') == 0,
            'output': result.get('stdout', '').strip()
        }
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """List paired devices"""
        result = self.execute_command('kdeconnect-cli --list-devices')
        
        if result.get('exit_code') != 0:
            return []
        
        # Parse output
        devices = []
        for line in result.get('stdout', '').split('\n'):
            if line.strip():
                # Basic parsing - format: "- DeviceName: device_id (paired and reachable)"
                parts = line.split(':')
                if len(parts) >= 2:
                    devices.append({
                        'name': parts[0].strip('- '),
                        'info': ':'.join(parts[1:]).strip()
                    })
        
        return devices
    
    def configure_firewall(self) -> bool:
        """Configure firewall for KDE Connect"""
        logger.info(f"Configuring firewall on {self.hostname}")
        
        commands = [
            'sudo firewall-cmd --zone=public --permanent --add-service=kdeconnect',
            'sudo firewall-cmd --zone=public --permanent --add-port=1714-1764/tcp',
            'sudo firewall-cmd --zone=public --permanent --add-port=1714-1764/udp',
            'sudo firewall-cmd --reload'
        ]
        
        for cmd in commands:
            result = self.execute_command(cmd)
            if result.get('exit_code') != 0:
                logger.error(f"Command failed: {cmd}")
                return False
        
        logger.info("Firewall configured successfully")
        return True
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        info = {}
        
        # OS info
        result = self.execute_command('cat /etc/os-release')
        if result.get('exit_code') == 0:
            info['os_release'] = result.get('stdout', '')
        
        # Hostname
        result = self.execute_command('hostname')
        if result.get('exit_code') == 0:
            info['hostname'] = result.get('stdout', '').strip()
        
        # Uptime
        result = self.execute_command('uptime')
        if result.get('exit_code') == 0:
            info['uptime'] = result.get('stdout', '').strip()
        
        # Memory
        result = self.execute_command('free -h')
        if result.get('exit_code') == 0:
            info['memory'] = result.get('stdout', '')
        
        return info
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to remote host"""
        try:
            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            logger.info(f"Uploaded {local_path} to {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from remote host"""
        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            logger.info(f"Downloaded {remote_path} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def deploy_config(self, config_content: str, remote_path: str) -> bool:
        """Deploy configuration file to remote host"""
        try:
            sftp = self.client.open_sftp()
            with sftp.open(remote_path, 'w') as f:
                f.write(config_content)
            sftp.close()
            logger.info(f"Deployed config to {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to deploy config: {e}")
            return False
    
    def setup_systemd_service(self) -> bool:
        """Setup systemd user service for KDE Connect"""
        service_content = """[Unit]
Description=KDE Connect Daemon
Documentation=https://userbase.kde.org/KDEConnect

[Service]
Type=simple
ExecStart=/usr/bin/kdeconnectd
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
"""
        
        # Deploy service file
        service_path = '/tmp/kdeconnect.service'
        if not self.deploy_config(service_content, service_path):
            return False
        
        # Move to systemd directory and enable
        commands = [
            'mkdir -p ~/.config/systemd/user',
            f'mv {service_path} ~/.config/systemd/user/kdeconnect.service',
            'systemctl --user daemon-reload',
            'systemctl --user enable kdeconnect.service',
            'systemctl --user start kdeconnect.service'
        ]
        
        for cmd in commands:
            result = self.execute_command(cmd)
            if result.get('exit_code') != 0:
                logger.error(f"Failed: {cmd}")
                return False
        
        logger.info("Systemd service configured successfully")
        return True
    
    def get_logs(self, lines: int = 100) -> str:
        """Get KDE Connect logs"""
        result = self.execute_command(f'journalctl --user -u kdeconnect.service -n {lines}')
        return result.get('stdout', '')
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'hostname': self.hostname,
            'connected': self.connected
        }
        
        if not self.connected:
            return health
        
        # Check installation
        health['installed'] = self.check_kdeconnect_installed()
        
        # Check daemon
        daemon_status = self.get_daemon_status()
        health['daemon_running'] = daemon_status['running']
        
        # Check firewall
        result = self.execute_command('sudo firewall-cmd --list-services --zone=public')
        health['firewall_configured'] = 'kdeconnect' in result.get('stdout', '')
        
        # List devices
        health['devices'] = self.list_devices()
        
        return health


class RemoteFleet:
    """Manage multiple remote KDE Connect instances"""
    
    def __init__(self):
        self.hosts: Dict[str, RemoteKDEConnectManager] = {}
    
    def add_host(self, name: str, manager: RemoteKDEConnectManager):
        """Add a remote host to the fleet"""
        self.hosts[name] = manager
    
    def remove_host(self, name: str):
        """Remove a remote host from the fleet"""
        if name in self.hosts:
            self.hosts[name].disconnect()
            del self.hosts[name]
    
    def connect_all(self) -> Dict[str, bool]:
        """Connect to all hosts"""
        results = {}
        for name, manager in self.hosts.items():
            results[name] = manager.connect()
        return results
    
    def disconnect_all(self):
        """Disconnect from all hosts"""
        for manager in self.hosts.values():
            manager.disconnect()
    
    def run_command_on_all(self, command: str) -> Dict[str, Dict[str, Any]]:
        """Run command on all hosts"""
        results = {}
        for name, manager in self.hosts.items():
            if manager.connected:
                results[name] = manager.execute_command(command)
            else:
                results[name] = {'error': 'Not connected', 'exit_code': -1}
        return results
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Run health check on all hosts"""
        results = {}
        for name, manager in self.hosts.items():
            results[name] = manager.run_health_check()
        return results
    
    def get_fleet_status(self) -> Dict[str, Any]:
        """Get overall fleet status"""
        status = {
            'total_hosts': len(self.hosts),
            'connected': sum(1 for m in self.hosts.values() if m.connected),
            'hosts': {}
        }
        
        for name, manager in self.hosts.items():
            status['hosts'][name] = {
                'connected': manager.connected,
                'hostname': manager.hostname,
                'username': manager.username
            }
        
        return status
