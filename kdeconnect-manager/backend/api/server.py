"""
Flask API Server with WebSocket Support
Provides REST API and WebSocket for real-time updates
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kdeconnect.dbus_interface import KDEConnectDBusInterface
from monitoring.health_monitor import HealthMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/home/ubuntu/kdeconnect-manager/logs/api.log')
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__,
            template_folder='../../frontend/templates',
            static_folder='../../frontend/static')
app.config['SECRET_KEY'] = 'kdeconnect-manager-secret-key-change-in-production'
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize KDE Connect interface
try:
    kde_connect = KDEConnectDBusInterface()
    logger.info("KDE Connect interface initialized")
except Exception as e:
    logger.error(f"Failed to initialize KDE Connect interface: {e}")
    kde_connect = None

# Initialize Health Monitor
health_monitor = HealthMonitor(check_interval=30)

# Health monitor event callback
def health_event_callback(event: Dict[str, Any]):
    """Forward health events to WebSocket clients"""
    socketio.emit('health_event', event, namespace='/')
    logger.debug(f"Health event emitted: {event['type']}")

health_monitor.add_event_callback(health_event_callback)


# ============================================
# REST API Endpoints
# ============================================

@app.route('/')
def index():
    """Serve main web interface"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get API status"""
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'kde_connect_available': kde_connect is not None and kde_connect.is_daemon_running(),
        'monitoring_active': health_monitor.monitoring,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/devices')
def get_devices():
    """Get list of all devices"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        device_ids = kde_connect.get_devices()
        devices = []
        
        for device_id in device_ids:
            device_info = kde_connect.get_device_info(device_id)
            if device_info:
                devices.append(device_info)
        
        return jsonify({
            'devices': devices,
            'count': len(devices)
        })
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/available')
def get_available_devices():
    """Get list of available (reachable) devices"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        devices = kde_connect.get_available_devices()
        return jsonify({
            'devices': devices,
            'count': len(devices)
        })
    except Exception as e:
        logger.error(f"Error getting available devices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>')
def get_device(device_id):
    """Get detailed device information"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        device_info = kde_connect.get_device_info(device_id)
        if device_info:
            return jsonify(device_info)
        else:
            return jsonify({'error': 'Device not found'}), 404
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/pair', methods=['POST'])
def pair_device(device_id):
    """Request pairing with device"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        success = kde_connect.request_pair(device_id)
        return jsonify({
            'success': success,
            'device_id': device_id,
            'message': 'Pairing request sent' if success else 'Failed to send pairing request'
        })
    except Exception as e:
        logger.error(f"Error pairing device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/unpair', methods=['POST'])
def unpair_device(device_id):
    """Unpair device"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        success = kde_connect.unpair(device_id)
        return jsonify({
            'success': success,
            'device_id': device_id,
            'message': 'Device unpaired' if success else 'Failed to unpair device'
        })
    except Exception as e:
        logger.error(f"Error unpairing device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/ping', methods=['POST'])
def ping_device(device_id):
    """Send ping to device"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        data = request.get_json() or {}
        message = data.get('message', 'Ping from KDE Connect Manager')
        
        success = kde_connect.send_ping(device_id, message)
        return jsonify({
            'success': success,
            'device_id': device_id,
            'message': 'Ping sent' if success else 'Failed to send ping'
        })
    except Exception as e:
        logger.error(f"Error pinging device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/ring', methods=['POST'])
def ring_device(device_id):
    """Ring device to find it"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        success = kde_connect.ring_device(device_id)
        return jsonify({
            'success': success,
            'device_id': device_id,
            'message': 'Ring command sent' if success else 'Failed to ring device'
        })
    except Exception as e:
        logger.error(f"Error ringing device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/share/file', methods=['POST'])
def share_file(device_id):
    """Share file with device"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({'error': 'file_path required'}), 400
        
        file_path = data['file_path']
        success = kde_connect.share_file(device_id, file_path)
        
        return jsonify({
            'success': success,
            'device_id': device_id,
            'file_path': file_path,
            'message': 'File shared' if success else 'Failed to share file'
        })
    except Exception as e:
        logger.error(f"Error sharing file with device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/share/text', methods=['POST'])
def share_text(device_id):
    """Share text with device"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'text required'}), 400
        
        text = data['text']
        success = kde_connect.share_text(device_id, text)
        
        return jsonify({
            'success': success,
            'device_id': device_id,
            'message': 'Text shared' if success else 'Failed to share text'
        })
    except Exception as e:
        logger.error(f"Error sharing text with device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/battery')
def get_battery(device_id):
    """Get battery status"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        battery_info = kde_connect.get_battery_status(device_id)
        if battery_info:
            return jsonify(battery_info)
        else:
            return jsonify({'error': 'Battery plugin not available'}), 404
    except Exception as e:
        logger.error(f"Error getting battery for device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_id>/notifications')
def get_notifications(device_id):
    """Get device notifications"""
    if not kde_connect:
        return jsonify({'error': 'KDE Connect not available'}), 503
    
    try:
        notifications = kde_connect.get_notifications(device_id)
        return jsonify({
            'notifications': notifications,
            'count': len(notifications)
        })
    except Exception as e:
        logger.error(f"Error getting notifications for device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def get_health():
    """Get current health status"""
    try:
        health_status = health_monitor.perform_health_check()
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health/history')
def get_health_history():
    """Get health check history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        history = health_monitor.get_health_history(limit)
        return jsonify({
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"Error getting health history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health/restart', methods=['POST'])
def restart_daemon():
    """Restart KDE Connect daemon"""
    try:
        success = health_monitor.restart_daemon()
        return jsonify({
            'success': success,
            'message': 'Daemon restarted' if success else 'Failed to restart daemon'
        })
    except Exception as e:
        logger.error(f"Error restarting daemon: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start health monitoring"""
    try:
        health_monitor.start_monitoring()
        return jsonify({
            'success': True,
            'message': 'Monitoring started'
        })
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop health monitoring"""
    try:
        health_monitor.stop_monitoring()
        return jsonify({
            'success': True,
            'message': 'Monitoring stopped'
        })
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================
# WebSocket Endpoints
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_status', {
        'status': 'connected',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe_devices')
def handle_subscribe_devices():
    """Subscribe to device updates"""
    logger.info(f"Client subscribed to device updates: {request.sid}")
    
    # Send initial device list
    if kde_connect:
        try:
            devices = kde_connect.get_available_devices()
            emit('devices_update', {
                'devices': devices,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending device updates: {e}")
            emit('error', {'message': str(e)})

@socketio.on('subscribe_health')
def handle_subscribe_health():
    """Subscribe to health updates"""
    logger.info(f"Client subscribed to health updates: {request.sid}")
    
    # Send initial health status
    try:
        health_status = health_monitor.perform_health_check()
        emit('health_update', health_status)
    except Exception as e:
        logger.error(f"Error sending health update: {e}")
        emit('error', {'message': str(e)})

@socketio.on('request_device_update')
def handle_device_update_request(data):
    """Handle request for device update"""
    try:
        device_id = data.get('device_id')
        if not device_id:
            emit('error', {'message': 'device_id required'})
            return
        
        if kde_connect:
            device_info = kde_connect.get_device_info(device_id)
            emit('device_update', {
                'device': device_info,
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Error handling device update request: {e}")
        emit('error', {'message': str(e)})


# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================
# Main Entry Point
# ============================================

def main():
    """Start the API server"""
    logger.info("Starting KDE Connect Manager API Server")
    
    # Start health monitoring
    health_monitor.start_monitoring()
    logger.info("Health monitoring started")
    
    # Start server
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        health_monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"Server error: {e}")
        health_monitor.stop_monitoring()
        raise


if __name__ == '__main__':
    main()
