#!/usr/bin/env python3
"""
KDE Connect Manager CLI
Command-line interface for managing KDE Connect
"""

import click
import sys
import os
import json
import subprocess
from pathlib import Path
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.kdeconnect.dbus_interface import KDEConnectDBusInterface
from backend.monitoring.health_monitor import HealthMonitor


def get_kde_connect():
    """Get KDE Connect interface with error handling"""
    try:
        return KDEConnectDBusInterface()
    except Exception as e:
        click.echo(click.style(f"Error: Failed to connect to KDE Connect daemon: {e}", fg='red'))
        click.echo("Make sure kdeconnectd is running. Try: kdeconnectd")
        sys.exit(1)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """KDE Connect Manager - Comprehensive management tool for KDE Connect"""
    pass


# ============================================
# Device Management Commands
# ============================================

@cli.group()
def device():
    """Manage KDE Connect devices"""
    pass


@device.command('list')
@click.option('--all', '-a', is_flag=True, help='Show all devices (including unreachable)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list_devices(all, output_json):
    """List paired devices"""
    kde = get_kde_connect()
    
    if all:
        device_ids = kde.get_devices()
    else:
        devices = kde.get_available_devices()
        if output_json:
            click.echo(json.dumps(devices, indent=2))
            return
        
        if not devices:
            click.echo("No available devices found")
            return
        
        # Format as table
        table_data = []
        for device in devices:
            battery = device.get('battery', {})
            battery_str = f"{battery.get('charge', 'N/A')}%"
            if battery.get('charging'):
                battery_str += " ⚡"
            
            table_data.append([
                device['name'],
                device['id'][:16] + '...',
                device['type'],
                '✓' if device['paired'] else '✗',
                '✓' if device['reachable'] else '✗',
                battery_str,
                len(device['loaded_plugins'])
            ])
        
        headers = ['Name', 'Device ID', 'Type', 'Paired', 'Reachable', 'Battery', 'Plugins']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        return
    
    # Show all devices with full info
    devices_info = []
    for device_id in device_ids:
        info = kde.get_device_info(device_id)
        if info:
            devices_info.append(info)
    
    if output_json:
        click.echo(json.dumps(devices_info, indent=2))
    else:
        if not devices_info:
            click.echo("No devices found")
            return
        
        table_data = []
        for device in devices_info:
            table_data.append([
                device['name'],
                device['id'][:20] + '...',
                device['type'],
                '✓' if device['paired'] else '✗',
                '✓' if device['reachable'] else '✗',
                ', '.join(device['loaded_plugins'][:3]) + ('...' if len(device['loaded_plugins']) > 3 else '')
            ])
        
        headers = ['Name', 'Device ID', 'Type', 'Paired', 'Reachable', 'Plugins']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))


@device.command('info')
@click.argument('device_id')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def device_info(device_id, output_json):
    """Show detailed device information"""
    kde = get_kde_connect()
    
    # Try to find device by name if not a valid ID
    if not device_id.startswith('_'):
        found_id = kde.get_device_id_by_name(device_id)
        if found_id:
            device_id = found_id
    
    info = kde.get_device_info(device_id)
    
    if not info:
        click.echo(click.style(f"Device not found: {device_id}", fg='red'))
        sys.exit(1)
    
    if output_json:
        click.echo(json.dumps(info, indent=2))
    else:
        click.echo(click.style(f"\n Device: {info['name']}", fg='cyan', bold=True))
        click.echo(f"    ID: {info['id']}")
        click.echo(f"    Type: {info['type']}")
        click.echo(f"    Paired: {click.style('✓', fg='green') if info['paired'] else click.style('✗', fg='red')}")
        click.echo(f"    Reachable: {click.style('✓', fg='green') if info['reachable'] else click.style('✗', fg='red')}")
        click.echo(f"    Trusted: {click.style('✓', fg='green') if info['trusted'] else click.style('✗', fg='red')}")
        
        if 'battery' in info:
            battery = info['battery']
            charge_color = 'green' if battery['charge'] > 50 else 'yellow' if battery['charge'] > 20 else 'red'
            click.echo(f"    Battery: {click.style(str(battery['charge']) + '%', fg=charge_color)} {'⚡ Charging' if battery['charging'] else ''}")
        
        click.echo(f"\n    Available Links: {', '.join(info['available_links'])}")
        click.echo(f"\n    Loaded Plugins ({len(info['loaded_plugins'])}):")
        for plugin in info['loaded_plugins']:
            click.echo(f"      • {plugin}")


@device.command('pair')
@click.argument('device_id')
def pair_device(device_id):
    """Request pairing with a device"""
    kde = get_kde_connect()
    
    # Try to find device by name
    if not device_id.startswith('_'):
        found_id = kde.get_device_id_by_name(device_id)
        if found_id:
            device_id = found_id
    
    click.echo(f"Sending pairing request to {device_id}...")
    success = kde.request_pair(device_id)
    
    if success:
        click.echo(click.style("✓ Pairing request sent. Accept on the device.", fg='green'))
    else:
        click.echo(click.style("✗ Failed to send pairing request", fg='red'))
        sys.exit(1)


@device.command('unpair')
@click.argument('device_id')
@click.confirmation_option(prompt='Are you sure you want to unpair this device?')
def unpair_device(device_id):
    """Unpair a device"""
    kde = get_kde_connect()
    
    # Try to find device by name
    if not device_id.startswith('_'):
        found_id = kde.get_device_id_by_name(device_id)
        if found_id:
            device_id = found_id
    
    click.echo(f"Unpairing device {device_id}...")
    success = kde.unpair(device_id)
    
    if success:
        click.echo(click.style("✓ Device unpaired successfully", fg='green'))
    else:
        click.echo(click.style("✗ Failed to unpair device", fg='red'))
        sys.exit(1)


@device.command('ping')
@click.argument('device_id')
@click.option('--message', '-m', default='Ping from CLI', help='Ping message')
def ping_device(device_id, message):
    """Send ping to device"""
    kde = get_kde_connect()
    
    # Try to find device by name
    if not device_id.startswith('_'):
        found_id = kde.get_device_id_by_name(device_id)
        if found_id:
            device_id = found_id
    
    click.echo(f"Sending ping to {device_id}...")
    success = kde.send_ping(device_id, message)
    
    if success:
        click.echo(click.style("✓ Ping sent successfully", fg='green'))
    else:
        click.echo(click.style("✗ Failed to send ping", fg='red'))
        sys.exit(1)


@device.command('ring')
@click.argument('device_id')
def ring_device(device_id):
    """Ring device to find it"""
    kde = get_kde_connect()
    
    # Try to find device by name
    if not device_id.startswith('_'):
        found_id = kde.get_device_id_by_name(device_id)
        if found_id:
            device_id = found_id
    
    click.echo(f"Ringing device {device_id}...")
    success = kde.ring_device(device_id)
    
    if success:
        click.echo(click.style("✓ Ring command sent. Check the device!", fg='green'))
    else:
        click.echo(click.style("✗ Failed to ring device", fg='red'))
        sys.exit(1)


@device.command('battery')
@click.argument('device_id')
def device_battery(device_id):
    """Get battery status"""
    kde = get_kde_connect()
    
    # Try to find device by name
    if not device_id.startswith('_'):
        found_id = kde.get_device_id_by_name(device_id)
        if found_id:
            device_id = found_id
    
    battery = kde.get_battery_status(device_id)
    
    if battery:
        charge = battery['charge']
        charging = battery['charging']
        
        charge_color = 'green' if charge > 50 else 'yellow' if charge > 20 else 'red'
        charge_str = click.style(f"{charge}%", fg=charge_color, bold=True)
        
        status = "⚡ Charging" if charging else "🔋 On Battery"
        
        click.echo(f"\nBattery Status: {charge_str} {status}\n")
    else:
        click.echo(click.style("✗ Battery plugin not available for this device", fg='red'))
        sys.exit(1)


# ============================================
# Share Commands
# ============================================

@cli.group()
def share():
    """Share files and text with devices"""
    pass


@share.command('file')
@click.argument('device_id')
@click.argument('file_path', type=click.Path(exists=True))
def share_file(device_id, file_path):
    """Share a file with device"""
    kde = get_kde_connect()
    
    # Try to find device by name
    if not device_id.startswith('_'):
        found_id = kde.get_device_id_by_name(device_id)
        if found_id:
            device_id = found_id
    
    file_path = os.path.abspath(file_path)
    click.echo(f"Sharing {file_path} with {device_id}...")
    
    success = kde.share_file(device_id, file_path)
    
    if success:
        click.echo(click.style("✓ File shared successfully", fg='green'))
    else:
        click.echo(click.style("✗ Failed to share file", fg='red'))
        sys.exit(1)


@share.command('text')
@click.argument('device_id')
@click.argument('text')
def share_text(device_id, text):
    """Share text with device"""
    kde = get_kde_connect()
    
    # Try to find device by name
    if not device_id.startswith('_'):
        found_id = kde.get_device_id_by_name(device_id)
        if found_id:
            device_id = found_id
    
    click.echo(f"Sharing text with {device_id}...")
    success = kde.share_text(device_id, text)
    
    if success:
        click.echo(click.style("✓ Text shared successfully", fg='green'))
    else:
        click.echo(click.style("✗ Failed to share text", fg='red'))
        sys.exit(1)


# ============================================
# Health and Monitoring Commands
# ============================================

@cli.group()
def health():
    """Health monitoring and diagnostics"""
    pass


@health.command('check')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def health_check(output_json):
    """Perform health check"""
    monitor = HealthMonitor()
    
    click.echo("Performing health check...\n")
    status = monitor.perform_health_check()
    
    if output_json:
        click.echo(json.dumps(status, indent=2))
        return
    
    # Display formatted results
    overall = status['overall_healthy']
    
    click.echo(click.style(f"Overall Status: {'✓ HEALTHY' if overall else '✗ UNHEALTHY'}", 
                          fg='green' if overall else 'red', bold=True))
    click.echo()
    
    # Daemon status
    click.echo(click.style("Daemon Status:", bold=True))
    click.echo(f"  Running: {click.style('✓', fg='green') if status['daemon_running'] else click.style('✗', fg='red')}")
    click.echo(f"  Responsive: {click.style('✓', fg='green') if status['daemon_responsive'] else click.style('✗', fg='red')}")
    
    if status['resources']:
        res = status['resources']
        click.echo(f"  CPU: {res['cpu_percent']:.1f}%")
        click.echo(f"  Memory: {res['memory_mb']:.1f} MB")
    
    click.echo()
    
    # Firewall status
    click.echo(click.style("Firewall:", bold=True))
    fw = status['firewall']
    click.echo(f"  Configured: {click.style('✓', fg='green') if fw['configured'] else click.style('✗', fg='red')}")
    if fw['ports_open']:
        click.echo(f"  Open: {', '.join(fw['ports_open'])}")
    if fw['missing_rules']:
        click.echo(click.style(f"  Missing: {', '.join(fw['missing_rules'])}", fg='yellow'))
    
    click.echo()
    
    # Network status
    click.echo(click.style("Network:", bold=True))
    net = status['network']
    click.echo(f"  Local Network: {click.style('✓', fg='green') if net['local_network'] else click.style('✗', fg='red')}")
    
    click.echo()
    
    # Ports status
    click.echo(click.style("Listening Ports:", bold=True))
    ports = status['ports']
    click.echo(f"  TCP: {click.style('✓', fg='green') if ports['tcp_listening'] else click.style('✗', fg='red')}")
    click.echo(f"  UDP: {click.style('✓', fg='green') if ports['udp_listening'] else click.style('✗', fg='red')}")
    
    if not overall:
        click.echo()
        click.echo(click.style("Run 'kdecm health fix' to attempt automatic repairs", fg='yellow'))


@health.command('fix')
def health_fix():
    """Attempt to fix detected issues"""
    monitor = HealthMonitor()
    
    click.echo("Checking system health...\n")
    status = monitor.perform_health_check()
    
    if status['overall_healthy']:
        click.echo(click.style("✓ System is healthy, no fixes needed", fg='green'))
        return
    
    click.echo("Attempting to fix issues...\n")
    actions = monitor.self_heal(status)
    
    if actions:
        click.echo(click.style("Actions taken:", fg='green'))
        for action in actions:
            click.echo(f"  • {action}")
        
        # Re-check
        click.echo("\nRe-checking health...")
        new_status = monitor.perform_health_check()
        
        if new_status['overall_healthy']:
            click.echo(click.style("\n✓ System is now healthy!", fg='green', bold=True))
        else:
            click.echo(click.style("\n⚠ Some issues remain. Manual intervention may be needed.", fg='yellow'))
    else:
        click.echo(click.style("No automatic fixes available. Manual intervention required.", fg='yellow'))


@health.command('restart')
def restart_daemon():
    """Restart KDE Connect daemon"""
    monitor = HealthMonitor()
    
    click.echo("Restarting KDE Connect daemon...")
    success = monitor.restart_daemon()
    
    if success:
        click.echo(click.style("✓ Daemon restarted successfully", fg='green'))
    else:
        click.echo(click.style("✗ Failed to restart daemon", fg='red'))
        sys.exit(1)


# ============================================
# Server Commands
# ============================================

@cli.group()
def server():
    """Manage web server"""
    pass


@server.command('start')
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
def start_server(host, port):
    """Start web server"""
    click.echo(f"Starting KDE Connect Manager server on {host}:{port}...")
    click.echo(f"Web interface: http://localhost:{port}")
    click.echo(f"API endpoint: http://localhost:{port}/api")
    click.echo("\nPress Ctrl+C to stop\n")
    
    # Import and run server
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))
    from api.server import main
    main()


# ============================================
# Installation Commands
# ============================================

@cli.group()
def install():
    """Installation and setup commands"""
    pass


@install.command('check')
def install_check():
    """Check installation status"""
    click.echo("Checking KDE Connect installation...\n")
    
    # Check kdeconnectd
    try:
        result = subprocess.run(['which', 'kdeconnectd'], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo(click.style("✓ kdeconnectd found: ", fg='green') + result.stdout.strip())
        else:
            click.echo(click.style("✗ kdeconnectd not found", fg='red'))
    except Exception as e:
        click.echo(click.style(f"✗ Error checking kdeconnectd: {e}", fg='red'))
    
    # Check kdeconnect-cli
    try:
        result = subprocess.run(['which', 'kdeconnect-cli'], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo(click.style("✓ kdeconnect-cli found: ", fg='green') + result.stdout.strip())
        else:
            click.echo(click.style("✗ kdeconnect-cli not found", fg='red'))
    except Exception as e:
        click.echo(click.style(f"✗ Error checking kdeconnect-cli: {e}", fg='red'))
    
    # Check if daemon is running
    monitor = HealthMonitor()
    if monitor.is_daemon_running():
        click.echo(click.style("✓ Daemon is running", fg='green'))
    else:
        click.echo(click.style("✗ Daemon is not running", fg='yellow'))
    
    # Check firewall
    status = monitor.perform_health_check()
    if status['firewall']['configured']:
        click.echo(click.style("✓ Firewall configured", fg='green'))
    else:
        click.echo(click.style("✗ Firewall not configured", fg='yellow'))
    
    click.echo("\nRun 'kdecm install setup' to install dependencies")


@install.command('setup')
def install_setup():
    """Install and configure KDE Connect"""
    click.echo(click.style("KDE Connect Manager Setup", bold=True))
    click.echo("This will install KDE Connect and configure firewall rules.\n")
    
    if not click.confirm("Continue with installation?"):
        return
    
    # Run installation script
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'install.sh')
    
    if not os.path.exists(script_path):
        click.echo(click.style("✗ Installation script not found", fg='red'))
        sys.exit(1)
    
    try:
        subprocess.run(['bash', script_path], check=True)
        click.echo(click.style("\n✓ Installation completed successfully!", fg='green', bold=True))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"\n✗ Installation failed: {e}", fg='red'))
        sys.exit(1)


if __name__ == '__main__':
    cli()
