#!/usr/bin/env python3
"""
KDE Connect Manager - Basic Usage Examples
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.kdeconnect.dbus_interface import KDEConnectDBusInterface
from backend.monitoring.health_monitor import HealthMonitor


def example_device_management():
    """Example: Device management operations"""
    print("\n=== Device Management Example ===\n")
    
    try:
        kde = KDEConnectDBusInterface()
        
        # List all devices
        print("📱 Available devices:")
        devices = kde.get_available_devices()
        
        for device in devices:
            print(f"\n  Name: {device['name']}")
            print(f"  ID: {device['id']}")
            print(f"  Type: {device['type']}")
            print(f"  Paired: {'✓' if device['paired'] else '✗'}")
            print(f"  Reachable: {'✓' if device['reachable'] else '✗'}")
            
            if 'battery' in device:
                battery = device['battery']
                print(f"  Battery: {battery['charge']}% {'⚡' if battery['charging'] else '🔋'}")
        
        if not devices:
            print("  No devices found")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_health_monitoring():
    """Example: Health monitoring"""
    print("\n=== Health Monitoring Example ===\n")
    
    try:
        monitor = HealthMonitor()
        
        # Perform health check
        print("🔍 Performing health check...")
        status = monitor.perform_health_check()
        
        print(f"\n✓ Overall Health: {'HEALTHY' if status['overall_healthy'] else 'UNHEALTHY'}")
        print(f"  Daemon Running: {'✓' if status['daemon_running'] else '✗'}")
        print(f"  Daemon Responsive: {'✓' if status['daemon_responsive'] else '✗'}")
        print(f"  Firewall Configured: {'✓' if status['firewall']['configured'] else '✗'}")
        print(f"  Network Active: {'✓' if status['network']['local_network'] else '✗'}")
        
        if status['resources']:
            print(f"\n📊 Resource Usage:")
            print(f"  CPU: {status['resources']['cpu_percent']:.1f}%")
            print(f"  Memory: {status['resources']['memory_mb']:.1f} MB")
        
        # Attempt self-healing if needed
        if not status['overall_healthy']:
            print("\n🔧 Attempting self-healing...")
            actions = monitor.self_heal(status)
            if actions:
                print(f"  Actions taken: {', '.join(actions)}")
            else:
                print("  No automatic fixes available")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_send_notification():
    """Example: Send notification to first available device"""
    print("\n=== Send Notification Example ===\n")
    
    try:
        kde = KDEConnectDBusInterface()
        devices = kde.get_available_devices()
        
        if not devices:
            print("❌ No devices available")
            return
        
        device = devices[0]
        print(f"📱 Sending ping to: {device['name']}")
        
        success = kde.send_ping(device['id'], "Hello from KDE Connect Manager!")
        
        if success:
            print("✓ Ping sent successfully")
        else:
            print("✗ Failed to send ping")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_share_file():
    """Example: Share a file with device"""
    print("\n=== Share File Example ===\n")
    
    try:
        kde = KDEConnectDBusInterface()
        devices = kde.get_available_devices()
        
        if not devices:
            print("❌ No devices available")
            return
        
        device = devices[0]
        
        # Create a test file
        test_file = "/tmp/kde_connect_test.txt"
        with open(test_file, 'w') as f:
            f.write("Hello from KDE Connect Manager!\n")
            f.write("This is a test file.\n")
        
        print(f"📁 Sharing {test_file} with: {device['name']}")
        
        success = kde.share_file(device['id'], test_file)
        
        if success:
            print("✓ File shared successfully")
        else:
            print("✗ Failed to share file")
        
        # Cleanup
        os.remove(test_file)
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_battery_monitoring():
    """Example: Monitor battery status of all devices"""
    print("\n=== Battery Monitoring Example ===\n")
    
    try:
        kde = KDEConnectDBusInterface()
        devices = kde.get_available_devices()
        
        if not devices:
            print("❌ No devices available")
            return
        
        for device in devices:
            battery = kde.get_battery_status(device['id'])
            
            if battery:
                charge = battery['charge']
                charging = battery['charging']
                
                # Determine status emoji
                if charging:
                    status = "⚡ Charging"
                elif charge > 80:
                    status = "🔋 Full"
                elif charge > 20:
                    status = "🔋 Good"
                else:
                    status = "🪫 Low"
                
                print(f"📱 {device['name']}: {charge}% {status}")
            else:
                print(f"📱 {device['name']}: Battery status not available")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("  KDE Connect Manager - Usage Examples")
    print("="*60)
    
    example_device_management()
    example_health_monitoring()
    example_send_notification()
    example_share_file()
    example_battery_monitoring()
    
    print("\n" + "="*60)
    print("  Examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
