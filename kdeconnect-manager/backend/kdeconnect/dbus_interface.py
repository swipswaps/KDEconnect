"""
DBus Interface for KDE Connect
Provides Python wrapper around KDE Connect DBus API
"""

import dbus
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class KDEConnectDBusInterface:
    """Main interface to KDE Connect daemon via DBus"""
    
    def __init__(self):
        """Initialize DBus connection"""
        try:
            self.bus = dbus.SessionBus()
            self.kdeconnect = self.bus.get_object(
                'org.kde.kdeconnect',
                '/modules/kdeconnect'
            )
            self.daemon_interface = dbus.Interface(
                self.kdeconnect,
                'org.kde.kdeconnect.daemon'
            )
            logger.info("Successfully connected to KDE Connect daemon")
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to connect to KDE Connect daemon: {e}")
            raise
    
    def is_daemon_running(self) -> bool:
        """Check if KDE Connect daemon is running"""
        try:
            self.daemon_interface.devices()
            return True
        except dbus.exceptions.DBusException:
            return False
    
    def get_devices(self) -> List[str]:
        """Get list of all device IDs"""
        try:
            return list(self.daemon_interface.devices())
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to get devices: {e}")
            return []
    
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get list of available (reachable) devices with details"""
        devices = []
        for device_id in self.get_devices():
            device_info = self.get_device_info(device_id)
            if device_info and device_info.get('reachable'):
                devices.append(device_info)
        return devices
    
    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a device"""
        try:
            device_path = f'/modules/kdeconnect/devices/{device_id}'
            device_obj = self.bus.get_object('org.kde.kdeconnect', device_path)
            device_interface = dbus.Interface(device_obj, 'org.kde.kdeconnect.device')
            
            info = {
                'id': device_id,
                'name': str(device_interface.name()),
                'type': str(device_interface.type()),
                'reachable': bool(device_interface.isReachable()),
                'trusted': bool(device_interface.isTrusted()),
                'paired': bool(device_interface.isPaired()),
                'available_links': list(device_interface.availableLinks()),
                'loaded_plugins': list(device_interface.loadedPlugins()),
            }
            
            # Try to get battery info if plugin is loaded
            if 'kdeconnect_battery' in info['loaded_plugins']:
                battery_info = self.get_battery_status(device_id)
                if battery_info:
                    info['battery'] = battery_info
            
            return info
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to get device info for {device_id}: {e}")
            return None
    
    def get_battery_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get battery status for a device"""
        try:
            battery_path = f'/modules/kdeconnect/devices/{device_id}/battery'
            battery_obj = self.bus.get_object('org.kde.kdeconnect', battery_path)
            battery_interface = dbus.Interface(
                battery_obj,
                'org.kde.kdeconnect.device.battery'
            )
            
            return {
                'charge': int(battery_interface.charge()),
                'charging': bool(battery_interface.isCharging())
            }
        except dbus.exceptions.DBusException as e:
            logger.debug(f"Battery plugin not available for {device_id}: {e}")
            return None
    
    def request_pair(self, device_id: str) -> bool:
        """Request pairing with a device"""
        try:
            device_path = f'/modules/kdeconnect/devices/{device_id}'
            device_obj = self.bus.get_object('org.kde.kdeconnect', device_path)
            device_interface = dbus.Interface(device_obj, 'org.kde.kdeconnect.device')
            device_interface.requestPair()
            logger.info(f"Pairing request sent to device {device_id}")
            return True
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to request pairing with {device_id}: {e}")
            return False
    
    def unpair(self, device_id: str) -> bool:
        """Unpair a device"""
        try:
            device_path = f'/modules/kdeconnect/devices/{device_id}'
            device_obj = self.bus.get_object('org.kde.kdeconnect', device_path)
            device_interface = dbus.Interface(device_obj, 'org.kde.kdeconnect.device')
            device_interface.unpair()
            logger.info(f"Device {device_id} unpaired")
            return True
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to unpair device {device_id}: {e}")
            return False
    
    def send_ping(self, device_id: str, message: str = "Ping") -> bool:
        """Send ping to device"""
        try:
            ping_path = f'/modules/kdeconnect/devices/{device_id}/ping'
            ping_obj = self.bus.get_object('org.kde.kdeconnect', ping_path)
            ping_interface = dbus.Interface(ping_obj, 'org.kde.kdeconnect.device.ping')
            ping_interface.sendPing(message)
            logger.info(f"Ping sent to device {device_id}")
            return True
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to send ping to {device_id}: {e}")
            return False
    
    def share_file(self, device_id: str, file_path: str) -> bool:
        """Share a file with device"""
        try:
            share_path = f'/modules/kdeconnect/devices/{device_id}/share'
            share_obj = self.bus.get_object('org.kde.kdeconnect', share_path)
            share_interface = dbus.Interface(
                share_obj,
                'org.kde.kdeconnect.device.share'
            )
            share_interface.shareUrl(f'file://{file_path}')
            logger.info(f"File {file_path} shared with device {device_id}")
            return True
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to share file with {device_id}: {e}")
            return False
    
    def share_text(self, device_id: str, text: str) -> bool:
        """Share text with device"""
        try:
            share_path = f'/modules/kdeconnect/devices/{device_id}/share'
            share_obj = self.bus.get_object('org.kde.kdeconnect', share_path)
            share_interface = dbus.Interface(
                share_obj,
                'org.kde.kdeconnect.device.share'
            )
            share_interface.shareText(text)
            logger.info(f"Text shared with device {device_id}")
            return True
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to share text with {device_id}: {e}")
            return False
    
    def get_notifications(self, device_id: str) -> List[Dict[str, Any]]:
        """Get active notifications from device"""
        try:
            notif_path = f'/modules/kdeconnect/devices/{device_id}/notifications'
            notif_obj = self.bus.get_object('org.kde.kdeconnect', notif_path)
            notif_interface = dbus.Interface(
                notif_obj,
                'org.kde.kdeconnect.device.notifications'
            )
            notification_ids = notif_interface.activeNotifications()
            
            notifications = []
            for notif_id in notification_ids:
                notif_detail_path = f'/modules/kdeconnect/devices/{device_id}/notifications/{notif_id}'
                notif_detail_obj = self.bus.get_object('org.kde.kdeconnect', notif_detail_path)
                notif_detail_interface = dbus.Interface(
                    notif_detail_obj,
                    'org.kde.kdeconnect.device.notifications.notification'
                )
                
                notifications.append({
                    'id': notif_id,
                    'title': str(notif_detail_interface.title()),
                    'text': str(notif_detail_interface.text()),
                    'appName': str(notif_detail_interface.appName()),
                })
            
            return notifications
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to get notifications from {device_id}: {e}")
            return []
    
    def ring_device(self, device_id: str) -> bool:
        """Ring the device to find it"""
        try:
            ring_path = f'/modules/kdeconnect/devices/{device_id}/findmyphone'
            ring_obj = self.bus.get_object('org.kde.kdeconnect', ring_path)
            ring_interface = dbus.Interface(
                ring_obj,
                'org.kde.kdeconnect.device.findmyphone'
            )
            ring_interface.ring()
            logger.info(f"Ring command sent to device {device_id}")
            return True
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to ring device {device_id}: {e}")
            return False
    
    def acquire_discovery_mode(self, mode_id: str) -> bool:
        """Enable device discovery mode"""
        try:
            self.daemon_interface.acquireDiscoveryMode(mode_id)
            logger.info(f"Discovery mode acquired: {mode_id}")
            return True
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to acquire discovery mode: {e}")
            return False
    
    def release_discovery_mode(self, mode_id: str) -> bool:
        """Disable device discovery mode"""
        try:
            self.daemon_interface.releaseDiscoveryMode(mode_id)
            logger.info(f"Discovery mode released: {mode_id}")
            return True
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to release discovery mode: {e}")
            return False
    
    def get_device_id_by_name(self, name: str) -> Optional[str]:
        """Get device ID by device name"""
        try:
            return str(self.daemon_interface.deviceIdByName(name))
        except dbus.exceptions.DBusException as e:
            logger.error(f"Failed to get device ID for name {name}: {e}")
            return None
    
    def get_plugin_config(self, device_id: str, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific plugin"""
        try:
            plugin_path = f'/modules/kdeconnect/devices/{device_id}/{plugin_name}'
            plugin_obj = self.bus.get_object('org.kde.kdeconnect', plugin_path)
            
            # Get all properties
            props_interface = dbus.Interface(
                plugin_obj,
                'org.freedesktop.DBus.Properties'
            )
            
            # This will vary by plugin, so we return a generic dict
            return {
                'plugin': plugin_name,
                'device_id': device_id,
                'available': True
            }
        except dbus.exceptions.DBusException as e:
            logger.debug(f"Plugin {plugin_name} not available for {device_id}: {e}")
            return None
