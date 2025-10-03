"""
Health Monitoring System for KDE Connect
Provides continuous monitoring, logging, and self-healing capabilities
"""

import subprocess
import time
import logging
import psutil
import dbus
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from threading import Thread, Event
import json

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors KDE Connect daemon health and performs self-healing"""
    
    def __init__(self, check_interval: int = 30):
        """
        Initialize health monitor
        
        Args:
            check_interval: Interval in seconds between health checks
        """
        self.check_interval = check_interval
        self.monitoring = False
        self.stop_event = Event()
        self.monitor_thread = None
        self.event_callbacks: List[Callable] = []
        self.health_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
    def add_event_callback(self, callback: Callable):
        """Add callback to be notified of health events"""
        self.event_callbacks.append(callback)
    
    def _notify_event(self, event_type: str, data: Dict[str, Any]):
        """Notify all callbacks of an event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        
        # Store in history
        self.health_history.append(event)
        if len(self.health_history) > self.max_history_size:
            self.health_history.pop(0)
        
        # Notify callbacks
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def is_daemon_running(self) -> bool:
        """Check if kdeconnectd process is running"""
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                if 'kdeconnectd' in proc.info['name']:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking daemon status: {e}")
            return False
    
    def is_daemon_responsive(self) -> bool:
        """Check if daemon responds to DBus calls"""
        try:
            bus = dbus.SessionBus()
            kdeconnect = bus.get_object('org.kde.kdeconnect', '/modules/kdeconnect')
            interface = dbus.Interface(kdeconnect, 'org.kde.kdeconnect.daemon')
            interface.devices()
            return True
        except dbus.exceptions.DBusException:
            return False
    
    def get_daemon_pid(self) -> Optional[int]:
        """Get PID of kdeconnectd process"""
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if 'kdeconnectd' in proc.info['name']:
                    return proc.info['pid']
            return None
        except Exception as e:
            logger.error(f"Error getting daemon PID: {e}")
            return None
    
    def get_daemon_resource_usage(self) -> Optional[Dict[str, Any]]:
        """Get resource usage of daemon process"""
        try:
            pid = self.get_daemon_pid()
            if not pid:
                return None
            
            proc = psutil.Process(pid)
            return {
                'cpu_percent': proc.cpu_percent(interval=0.1),
                'memory_mb': proc.memory_info().rss / 1024 / 1024,
                'num_threads': proc.num_threads(),
                'num_fds': proc.num_fds() if hasattr(proc, 'num_fds') else None,
            }
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return None
    
    def check_firewall_rules(self) -> Dict[str, Any]:
        """Check if firewall rules are configured correctly"""
        result = {
            'configured': False,
            'ports_open': [],
            'missing_rules': []
        }
        
        try:
            # Check firewalld
            output = subprocess.check_output(
                ['firewall-cmd', '--list-services', '--zone=public'],
                stderr=subprocess.STDOUT,
                text=True
            )
            
            if 'kdeconnect' in output.lower():
                result['configured'] = True
                result['ports_open'].append('kdeconnect service')
            
            # Check specific ports
            ports_output = subprocess.check_output(
                ['firewall-cmd', '--list-ports', '--zone=public'],
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Check for required ports
            required_tcp = False
            required_udp = False
            
            for port_range in ['1714-1764/tcp', '1714/tcp']:
                if port_range in ports_output:
                    required_tcp = True
                    result['ports_open'].append(port_range)
            
            for port_range in ['1714-1764/udp', '1714/udp']:
                if port_range in ports_output:
                    required_udp = True
                    result['ports_open'].append(port_range)
            
            if not required_tcp:
                result['missing_rules'].append('TCP ports 1714-1764')
            if not required_udp:
                result['missing_rules'].append('UDP ports 1714-1764')
            
            if required_tcp and required_udp:
                result['configured'] = True
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking firewall rules: {e}")
            result['error'] = str(e)
        except FileNotFoundError:
            logger.warning("firewalld not found, assuming firewall is disabled")
            result['configured'] = True  # Assume no firewall blocking
        
        return result
    
    def check_network_connectivity(self, device_ip: Optional[str] = None) -> Dict[str, Any]:
        """Check network connectivity"""
        result = {
            'local_network': False,
            'device_reachable': False
        }
        
        try:
            # Check if any network interface is up
            for interface, addrs in psutil.net_if_addrs().items():
                if interface != 'lo':  # Skip loopback
                    for addr in addrs:
                        if addr.family == 2:  # IPv4
                            result['local_network'] = True
                            break
            
            # If device IP provided, try to ping it
            if device_ip:
                try:
                    subprocess.check_output(
                        ['ping', '-c', '1', '-W', '2', device_ip],
                        stderr=subprocess.STDOUT
                    )
                    result['device_reachable'] = True
                except subprocess.CalledProcessError:
                    result['device_reachable'] = False
                    
        except Exception as e:
            logger.error(f"Error checking network connectivity: {e}")
            result['error'] = str(e)
        
        return result
    
    def check_listening_ports(self) -> Dict[str, Any]:
        """Check if KDE Connect ports are listening"""
        result = {
            'tcp_listening': False,
            'udp_listening': False,
            'ports': []
        }
        
        try:
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                if conn.laddr.port >= 1714 and conn.laddr.port <= 1764:
                    result['ports'].append({
                        'port': conn.laddr.port,
                        'type': 'tcp' if conn.type == 1 else 'udp',
                        'status': conn.status if hasattr(conn, 'status') else 'N/A'
                    })
                    
                    if conn.type == 1:  # SOCK_STREAM (TCP)
                        result['tcp_listening'] = True
                    elif conn.type == 2:  # SOCK_DGRAM (UDP)
                        result['udp_listening'] = True
                        
        except Exception as e:
            logger.error(f"Error checking listening ports: {e}")
            result['error'] = str(e)
        
        return result
    
    def restart_daemon(self) -> bool:
        """Restart KDE Connect daemon"""
        try:
            logger.info("Attempting to restart KDE Connect daemon")
            
            # Try to stop existing daemon
            subprocess.run(['killall', 'kdeconnectd'], stderr=subprocess.DEVNULL)
            time.sleep(2)
            
            # Start daemon
            subprocess.Popen(
                ['kdeconnectd'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Wait and verify
            time.sleep(3)
            if self.is_daemon_running():
                logger.info("Daemon restarted successfully")
                self._notify_event('daemon_restarted', {'success': True})
                return True
            else:
                logger.error("Failed to restart daemon")
                self._notify_event('daemon_restart_failed', {'success': False})
                return False
                
        except Exception as e:
            logger.error(f"Error restarting daemon: {e}")
            self._notify_event('daemon_restart_error', {'error': str(e)})
            return False
    
    def configure_firewall(self) -> bool:
        """Automatically configure firewall rules"""
        try:
            logger.info("Configuring firewall rules")
            
            # Add KDE Connect service
            subprocess.run(
                ['sudo', 'firewall-cmd', '--zone=public', '--permanent', '--add-service=kdeconnect'],
                check=True,
                capture_output=True
            )
            
            # Add ports as backup
            subprocess.run(
                ['sudo', 'firewall-cmd', '--zone=public', '--permanent', '--add-port=1714-1764/tcp'],
                check=True,
                capture_output=True
            )
            
            subprocess.run(
                ['sudo', 'firewall-cmd', '--zone=public', '--permanent', '--add-port=1714-1764/udp'],
                check=True,
                capture_output=True
            )
            
            # Reload firewall
            subprocess.run(
                ['sudo', 'firewall-cmd', '--reload'],
                check=True,
                capture_output=True
            )
            
            logger.info("Firewall configured successfully")
            self._notify_event('firewall_configured', {'success': True})
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error configuring firewall: {e}")
            self._notify_event('firewall_config_failed', {'error': str(e)})
            return False
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        check_time = datetime.now().isoformat()
        
        health_status = {
            'timestamp': check_time,
            'daemon_running': self.is_daemon_running(),
            'daemon_responsive': False,
            'firewall': self.check_firewall_rules(),
            'network': self.check_network_connectivity(),
            'ports': self.check_listening_ports(),
            'resources': None,
            'overall_healthy': False
        }
        
        if health_status['daemon_running']:
            health_status['daemon_responsive'] = self.is_daemon_responsive()
            health_status['resources'] = self.get_daemon_resource_usage()
        
        # Determine overall health
        health_status['overall_healthy'] = (
            health_status['daemon_running'] and
            health_status['daemon_responsive'] and
            health_status['firewall']['configured'] and
            health_status['network']['local_network'] and
            (health_status['ports']['tcp_listening'] or health_status['ports']['udp_listening'])
        )
        
        return health_status
    
    def self_heal(self, health_status: Dict[str, Any]) -> List[str]:
        """Attempt to fix detected issues"""
        actions_taken = []
        
        # If daemon not running, restart it
        if not health_status['daemon_running']:
            logger.warning("Daemon not running, attempting restart")
            if self.restart_daemon():
                actions_taken.append("Restarted daemon")
        
        # If daemon running but not responsive, restart it
        elif not health_status['daemon_responsive']:
            logger.warning("Daemon not responsive, attempting restart")
            if self.restart_daemon():
                actions_taken.append("Restarted unresponsive daemon")
        
        # If firewall not configured, configure it
        if not health_status['firewall']['configured']:
            logger.warning("Firewall not configured properly")
            actions_taken.append("Firewall configuration needed (requires manual sudo)")
        
        # Log actions taken
        if actions_taken:
            self._notify_event('self_heal', {'actions': actions_taken})
        
        return actions_taken
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting health monitoring loop")
        
        while not self.stop_event.is_set():
            try:
                # Perform health check
                health_status = self.perform_health_check()
                
                # Log status
                if not health_status['overall_healthy']:
                    logger.warning(f"Health check failed: {json.dumps(health_status, indent=2)}")
                    
                    # Attempt self-healing
                    actions = self.self_heal(health_status)
                    if actions:
                        logger.info(f"Self-healing actions taken: {actions}")
                else:
                    logger.debug("Health check passed")
                
                # Notify event callbacks
                self._notify_event('health_check', health_status)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self._notify_event('monitor_error', {'error': str(e)})
            
            # Wait for next check
            self.stop_event.wait(self.check_interval)
        
        logger.info("Health monitoring loop stopped")
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        if self.monitoring:
            logger.warning("Monitoring already running")
            return
        
        self.monitoring = True
        self.stop_event.clear()
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        if not self.monitoring:
            return
        
        logger.info("Stopping health monitoring")
        self.monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Health monitoring stopped")
    
    def get_health_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent health check history"""
        return self.health_history[-limit:]
