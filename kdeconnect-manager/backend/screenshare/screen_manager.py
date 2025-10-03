"""
Screen Sharing Manager
Integrate screen sharing and frame mirroring capabilities
"""

import subprocess
import logging
import os
import signal
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ScreenShareManager:
    """Manage screen sharing using krfb (VNC) and other tools"""
    
    def __init__(self):
        self.krfb_process = None
        self.vnc_port = 5900
        self.vnc_password = None
    
    def is_krfb_installed(self) -> bool:
        """Check if krfb is installed"""
        try:
            result = subprocess.run(['which', 'krfb'], capture_output=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking krfb: {e}")
            return False
    
    def install_krfb(self) -> bool:
        """Install krfb"""
        logger.info("Installing krfb")
        try:
            result = subprocess.run(
                ['sudo', 'dnf', 'install', '-y', 'krfb'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("krfb installed successfully")
                return True
            else:
                logger.error(f"Failed to install krfb: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing krfb: {e}")
            return False
    
    def start_krfb(self, unattended: bool = False) -> bool:
        """
        Start krfb VNC server
        
        Args:
            unattended: Enable unattended access mode
        """
        if not self.is_krfb_installed():
            logger.error("krfb is not installed")
            return False
        
        try:
            # Start krfb
            env = os.environ.copy()
            env['DISPLAY'] = ':0'
            
            self.krfb_process = subprocess.Popen(
                ['krfb', '--nodialog'] if unattended else ['krfb'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            
            logger.info("krfb started")
            return True
        except Exception as e:
            logger.error(f"Error starting krfb: {e}")
            return False
    
    def stop_krfb(self) -> bool:
        """Stop krfb VNC server"""
        try:
            if self.krfb_process:
                self.krfb_process.terminate()
                self.krfb_process.wait(timeout=5)
                self.krfb_process = None
                logger.info("krfb stopped")
                return True
            else:
                # Try to kill any running krfb processes
                subprocess.run(['killall', 'krfb'], stderr=subprocess.DEVNULL)
                return True
        except Exception as e:
            logger.error(f"Error stopping krfb: {e}")
            return False
    
    def get_krfb_status(self) -> Dict[str, Any]:
        """Get krfb status"""
        status = {
            'running': False,
            'port': self.vnc_port,
            'pid': None
        }
        
        try:
            # Check if krfb is running
            result = subprocess.run(
                ['pgrep', '-f', 'krfb'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                status['running'] = True
                status['pid'] = int(result.stdout.strip().split('\n')[0])
            
        except Exception as e:
            logger.error(f"Error getting krfb status: {e}")
        
        return status
    
    def configure_vnc_password(self, password: str) -> bool:
        """Configure VNC password for krfb"""
        # Note: krfb password configuration is done through its GUI
        # This is a placeholder for future implementation
        logger.warning("VNC password configuration through API not yet implemented")
        self.vnc_password = password
        return False
    
    def get_vnc_connection_string(self) -> str:
        """Get VNC connection string"""
        # Get local IP address
        try:
            result = subprocess.run(
                ['hostname', '-I'],
                capture_output=True,
                text=True
            )
            ip = result.stdout.strip().split()[0]
            return f"vnc://{ip}:{self.vnc_port}"
        except Exception as e:
            logger.error(f"Error getting IP address: {e}")
            return f"vnc://localhost:{self.vnc_port}"


class X11VNCManager:
    """Manage screen sharing using x11vnc (alternative to krfb)"""
    
    def __init__(self, port: int = 5900, password: Optional[str] = None):
        self.port = port
        self.password = password
        self.process = None
    
    def is_installed(self) -> bool:
        """Check if x11vnc is installed"""
        try:
            result = subprocess.run(['which', 'x11vnc'], capture_output=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking x11vnc: {e}")
            return False
    
    def install(self) -> bool:
        """Install x11vnc"""
        logger.info("Installing x11vnc")
        try:
            result = subprocess.run(
                ['sudo', 'dnf', 'install', '-y', 'x11vnc'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("x11vnc installed successfully")
                return True
            else:
                logger.error(f"Failed to install x11vnc: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing x11vnc: {e}")
            return False
    
    def start(self, display: str = ':0', view_only: bool = False) -> bool:
        """
        Start x11vnc server
        
        Args:
            display: X11 display to share
            view_only: Enable view-only mode
        """
        if not self.is_installed():
            logger.error("x11vnc is not installed")
            return False
        
        try:
            cmd = [
                'x11vnc',
                '-display', display,
                '-rfbport', str(self.port),
                '-forever',
                '-shared'
            ]
            
            if self.password:
                cmd.extend(['-passwd', self.password])
            
            if view_only:
                cmd.append('-viewonly')
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info(f"x11vnc started on port {self.port}")
            return True
        except Exception as e:
            logger.error(f"Error starting x11vnc: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop x11vnc server"""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
                logger.info("x11vnc stopped")
                return True
            else:
                subprocess.run(['killall', 'x11vnc'], stderr=subprocess.DEVNULL)
                return True
        except Exception as e:
            logger.error(f"Error stopping x11vnc: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get x11vnc status"""
        status = {
            'running': False,
            'port': self.port,
            'pid': None
        }
        
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'x11vnc'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                status['running'] = True
                status['pid'] = int(result.stdout.strip().split('\n')[0])
            
        except Exception as e:
            logger.error(f"Error getting x11vnc status: {e}")
        
        return status


class PipeWireScreenShare:
    """Manage screen sharing using PipeWire (Wayland)"""
    
    def __init__(self):
        self.pipewire_running = False
    
    def check_pipewire(self) -> Dict[str, Any]:
        """Check PipeWire installation and status"""
        status = {
            'installed': False,
            'running': False,
            'version': None
        }
        
        try:
            # Check if pipewire is installed
            result = subprocess.run(
                ['which', 'pipewire'],
                capture_output=True
            )
            status['installed'] = result.returncode == 0
            
            if status['installed']:
                # Check version
                result = subprocess.run(
                    ['pipewire', '--version'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    status['version'] = result.stdout.strip()
                
                # Check if running
                result = subprocess.run(
                    ['systemctl', '--user', 'is-active', 'pipewire.service'],
                    capture_output=True,
                    text=True
                )
                status['running'] = result.stdout.strip() == 'active'
            
        except Exception as e:
            logger.error(f"Error checking PipeWire: {e}")
        
        return status
    
    def install_pipewire(self) -> bool:
        """Install PipeWire and related packages"""
        logger.info("Installing PipeWire")
        
        packages = [
            'pipewire',
            'wireplumber',
            'xdg-desktop-portal',
            'xdg-desktop-portal-kde'
        ]
        
        try:
            result = subprocess.run(
                ['sudo', 'dnf', 'install', '-y'] + packages,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("PipeWire installed successfully")
                return True
            else:
                logger.error(f"Failed to install PipeWire: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing PipeWire: {e}")
            return False
    
    def start_pipewire(self) -> bool:
        """Start PipeWire services"""
        try:
            services = ['pipewire.service', 'wireplumber.service']
            
            for service in services:
                result = subprocess.run(
                    ['systemctl', '--user', 'start', service],
                    capture_output=True
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to start {service}")
                    return False
            
            logger.info("PipeWire services started")
            return True
        except Exception as e:
            logger.error(f"Error starting PipeWire: {e}")
            return False
    
    def enable_pipewire(self) -> bool:
        """Enable PipeWire services to start on boot"""
        try:
            services = ['pipewire.service', 'wireplumber.service']
            
            for service in services:
                result = subprocess.run(
                    ['systemctl', '--user', 'enable', service],
                    capture_output=True
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to enable {service}")
                    return False
            
            logger.info("PipeWire services enabled")
            return True
        except Exception as e:
            logger.error(f"Error enabling PipeWire: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive PipeWire status"""
        status = self.check_pipewire()
        
        # Check xdg-desktop-portal
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'xdg-desktop-portal'],
                capture_output=True
            )
            status['portal_running'] = result.returncode == 0
        except Exception:
            status['portal_running'] = False
        
        return status


class ScreenShareIntegration:
    """Main screen sharing integration class"""
    
    def __init__(self):
        self.krfb = ScreenShareManager()
        self.x11vnc = X11VNCManager()
        self.pipewire = PipeWireScreenShare()
    
    def detect_display_server(self) -> str:
        """Detect if running X11 or Wayland"""
        session_type = os.environ.get('XDG_SESSION_TYPE', '')
        
        if 'wayland' in session_type.lower():
            return 'wayland'
        elif 'x11' in session_type.lower():
            return 'x11'
        else:
            # Try to detect from other methods
            display = os.environ.get('DISPLAY', '')
            wayland_display = os.environ.get('WAYLAND_DISPLAY', '')
            
            if wayland_display:
                return 'wayland'
            elif display:
                return 'x11'
            else:
                return 'unknown'
    
    def get_recommended_method(self) -> str:
        """Get recommended screen sharing method"""
        display_server = self.detect_display_server()
        
        if display_server == 'wayland':
            if self.pipewire.check_pipewire()['installed']:
                return 'pipewire'
            else:
                return 'krfb'
        else:
            return 'x11vnc'
    
    def setup_screen_sharing(self, method: Optional[str] = None) -> Dict[str, Any]:
        """
        Setup screen sharing with recommended or specified method
        
        Args:
            method: 'krfb', 'x11vnc', or 'pipewire'. Auto-detect if None.
        """
        if not method:
            method = self.get_recommended_method()
        
        result = {
            'method': method,
            'success': False,
            'message': '',
            'connection_info': {}
        }
        
        if method == 'krfb':
            if not self.krfb.is_krfb_installed():
                if not self.krfb.install_krfb():
                    result['message'] = 'Failed to install krfb'
                    return result
            
            if self.krfb.start_krfb():
                result['success'] = True
                result['message'] = 'krfb started successfully'
                result['connection_info'] = {
                    'type': 'vnc',
                    'url': self.krfb.get_vnc_connection_string(),
                    'port': self.krfb.vnc_port
                }
            else:
                result['message'] = 'Failed to start krfb'
        
        elif method == 'x11vnc':
            if not self.x11vnc.is_installed():
                if not self.x11vnc.install():
                    result['message'] = 'Failed to install x11vnc'
                    return result
            
            if self.x11vnc.start():
                result['success'] = True
                result['message'] = 'x11vnc started successfully'
                result['connection_info'] = {
                    'type': 'vnc',
                    'port': self.x11vnc.port,
                    'url': f'vnc://localhost:{self.x11vnc.port}'
                }
            else:
                result['message'] = 'Failed to start x11vnc'
        
        elif method == 'pipewire':
            pipewire_status = self.pipewire.check_pipewire()
            
            if not pipewire_status['installed']:
                if not self.pipewire.install_pipewire():
                    result['message'] = 'Failed to install PipeWire'
                    return result
            
            if not pipewire_status['running']:
                if not self.pipewire.start_pipewire():
                    result['message'] = 'Failed to start PipeWire'
                    return result
            
            result['success'] = True
            result['message'] = 'PipeWire configured for screen sharing'
            result['connection_info'] = {
                'type': 'pipewire',
                'note': 'Use browser-based screen sharing with WebRTC'
            }
        
        return result
    
    def stop_all(self) -> bool:
        """Stop all screen sharing services"""
        success = True
        
        if not self.krfb.stop_krfb():
            success = False
        
        if not self.x11vnc.stop():
            success = False
        
        return success
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all screen sharing methods"""
        return {
            'display_server': self.detect_display_server(),
            'recommended_method': self.get_recommended_method(),
            'krfb': self.krfb.get_krfb_status(),
            'x11vnc': self.x11vnc.get_status(),
            'pipewire': self.pipewire.get_status()
        }
