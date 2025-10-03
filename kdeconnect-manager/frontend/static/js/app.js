// KDE Connect Manager JavaScript

let socket = null;
let devices = {};
let logs = [];
let currentDevice = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initWebSocket();
    initEventHandlers();
    loadSettings();
    addLog('info', 'Application started');
});

// Tab Management
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// WebSocket Connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/socket.io/`;
    
    socket = io(window.location.origin, {
        transports: ['websocket', 'polling']
    });
    
    socket.on('connect', () => {
        updateConnectionStatus(true);
        addLog('success', 'Connected to server');
        
        // Subscribe to updates
        socket.emit('subscribe_devices');
        socket.emit('subscribe_health');
        
        // Initial data load
        loadDevices();
        loadHealth();
    });
    
    socket.on('disconnect', () => {
        updateConnectionStatus(false);
        addLog('error', 'Disconnected from server');
    });
    
    socket.on('devices_update', (data) => {
        handleDevicesUpdate(data);
    });
    
    socket.on('health_update', (data) => {
        handleHealthUpdate(data);
    });
    
    socket.on('health_event', (event) => {
        handleHealthEvent(event);
    });
    
    socket.on('error', (data) => {
        addLog('error', data.message);
        showNotification('Error', data.message, 'error');
    });
}

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    if (connected) {
        statusElement.textContent = 'Connected';
        statusElement.className = 'status-badge connected';
    } else {
        statusElement.textContent = 'Disconnected';
        statusElement.className = 'status-badge disconnected';
    }
}

// Device Management
async function loadDevices() {
    try {
        const response = await fetch('/api/devices/available');
        const data = await response.json();
        
        if (data.devices) {
            displayDevices(data.devices);
        }
    } catch (error) {
        addLog('error', `Failed to load devices: ${error.message}`);
    }
}

function handleDevicesUpdate(data) {
    if (data.devices) {
        displayDevices(data.devices);
    }
}

function displayDevices(deviceList) {
    devices = {};
    deviceList.forEach(device => {
        devices[device.id] = device;
    });
    
    const container = document.getElementById('devices-container');
    const loading = document.getElementById('devices-loading');
    const noDevices = document.getElementById('no-devices');
    
    loading.style.display = 'none';
    
    if (deviceList.length === 0) {
        container.innerHTML = '';
        noDevices.style.display = 'block';
        return;
    }
    
    noDevices.style.display = 'none';
    
    container.innerHTML = deviceList.map(device => createDeviceCard(device)).join('');
    
    // Add click handlers
    document.querySelectorAll('.device-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('btn')) {
                const deviceId = card.getAttribute('data-device-id');
                showDeviceModal(deviceId);
            }
        });
    });
}

function createDeviceCard(device) {
    const battery = device.battery || {};
    const batteryLevel = battery.charge || 0;
    const batteryClass = batteryLevel > 50 ? 'high' : batteryLevel > 20 ? 'medium' : 'low';
    const batteryIcon = battery.charging ? '⚡' : '🔋';
    
    return `
        <div class="device-card" data-device-id="${device.id}">
            <div class="device-card-header">
                <div class="device-name">📱 ${device.name}</div>
                <div class="device-status">
                    ${device.paired ? '<span class="device-badge paired">✓ Paired</span>' : ''}
                    ${device.reachable ? '<span class="device-badge reachable">● Online</span>' : ''}
                </div>
            </div>
            
            <div class="device-info">
                <div class="device-info-item">
                    <span>Type:</span>
                    <span>${device.type}</span>
                </div>
                <div class="device-info-item">
                    <span>ID:</span>
                    <span>${device.id.substring(0, 16)}...</span>
                </div>
                ${battery.charge ? `
                <div class="device-info-item">
                    <span>Battery:</span>
                    <span class="device-battery ${batteryClass}">${batteryIcon} ${batteryLevel}%</span>
                </div>
                ` : ''}
                <div class="device-info-item">
                    <span>Plugins:</span>
                    <span>${device.loaded_plugins.length}</span>
                </div>
            </div>
            
            <div class="device-actions">
                <button class="btn btn-primary" onclick="pingDevice('${device.id}'); event.stopPropagation();">📡 Ping</button>
                <button class="btn btn-primary" onclick="ringDevice('${device.id}'); event.stopPropagation();">🔔 Ring</button>
                <button class="btn btn-primary" onclick="showDeviceModal('${device.id}'); event.stopPropagation();">ℹ️ Details</button>
            </div>
        </div>
    `;
}

async function pingDevice(deviceId) {
    try {
        const response = await fetch(`/api/devices/${deviceId}/ping`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: 'Ping from Web UI' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addLog('success', `Ping sent to ${devices[deviceId]?.name || deviceId}`);
            showNotification('Success', 'Ping sent successfully', 'success');
        } else {
            addLog('error', `Failed to ping ${devices[deviceId]?.name || deviceId}`);
            showNotification('Error', 'Failed to send ping', 'error');
        }
    } catch (error) {
        addLog('error', `Error pinging device: ${error.message}`);
    }
}

async function ringDevice(deviceId) {
    try {
        const response = await fetch(`/api/devices/${deviceId}/ring`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            addLog('success', `Ring command sent to ${devices[deviceId]?.name || deviceId}`);
            showNotification('Success', 'Ring command sent', 'success');
        } else {
            addLog('error', `Failed to ring ${devices[deviceId]?.name || deviceId}`);
            showNotification('Error', 'Failed to ring device', 'error');
        }
    } catch (error) {
        addLog('error', `Error ringing device: ${error.message}`);
    }
}

function showDeviceModal(deviceId) {
    const device = devices[deviceId];
    if (!device) return;
    
    currentDevice = deviceId;
    
    const modal = document.getElementById('device-modal');
    const modalName = document.getElementById('modal-device-name');
    const modalDetails = document.getElementById('modal-device-details');
    
    modalName.textContent = device.name;
    
    const battery = device.battery || {};
    
    modalDetails.innerHTML = `
        <div class="device-info">
            <div class="device-info-item">
                <strong>Device ID:</strong> ${device.id}
            </div>
            <div class="device-info-item">
                <strong>Type:</strong> ${device.type}
            </div>
            <div class="device-info-item">
                <strong>Status:</strong> ${device.reachable ? '✓ Online' : '✗ Offline'}
            </div>
            <div class="device-info-item">
                <strong>Paired:</strong> ${device.paired ? '✓ Yes' : '✗ No'}
            </div>
            <div class="device-info-item">
                <strong>Trusted:</strong> ${device.trusted ? '✓ Yes' : '✗ No'}
            </div>
            ${battery.charge ? `
            <div class="device-info-item">
                <strong>Battery:</strong> ${battery.charge}% ${battery.charging ? '⚡ Charging' : ''}
            </div>
            ` : ''}
        </div>
        
        <h3 style="margin-top: 20px; color: var(--primary-color);">Loaded Plugins (${device.loaded_plugins.length})</h3>
        <div style="margin-top: 10px;">
            ${device.loaded_plugins.map(plugin => `<div style="padding: 5px; background: var(--hover-color); margin-bottom: 5px; border-radius: 4px;">• ${plugin}</div>`).join('')}
        </div>
    `;
    
    modal.classList.add('active');
}

// Health Management
async function loadHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        displayHealth(data);
    } catch (error) {
        addLog('error', `Failed to load health status: ${error.message}`);
    }
}

function handleHealthUpdate(data) {
    displayHealth(data);
}

function handleHealthEvent(event) {
    const type = event.type;
    const timestamp = new Date(event.timestamp).toLocaleTimeString();
    
    let logType = 'info';
    let message = `[${type}] ${JSON.stringify(event.data)}`;
    
    if (type.includes('error') || type.includes('failed')) {
        logType = 'error';
    } else if (type.includes('restart') || type.includes('fix')) {
        logType = 'warning';
    } else if (type.includes('success') || type === 'health_check') {
        logType = 'success';
    }
    
    addLog(logType, message);
}

function displayHealth(health) {
    const healthStatus = document.getElementById('health-status');
    const overview = document.getElementById('health-overview');
    
    // Update header status
    if (health.overall_healthy) {
        healthStatus.textContent = '✓ Healthy';
        healthStatus.className = 'status-badge healthy';
    } else {
        healthStatus.textContent = '✗ Unhealthy';
        healthStatus.className = 'status-badge unhealthy';
    }
    
    // Update overview
    overview.innerHTML = `
        <h2 style="color: ${health.overall_healthy ? 'var(--success-color)' : 'var(--danger-color)'}">
            ${health.overall_healthy ? '✓ System Healthy' : '✗ Issues Detected'}
        </h2>
        <p style="color: var(--text-secondary); margin-top: 10px;">
            Last checked: ${new Date(health.timestamp).toLocaleString()}
        </p>
    `;
    
    // Update daemon status
    const daemonStatus = document.getElementById('daemon-status');
    daemonStatus.innerHTML = `
        <div class="health-item">
            <span class="health-label">Running:</span>
            <span class="health-value ${health.daemon_running ? 'ok' : 'error'}">
                ${health.daemon_running ? '✓ Yes' : '✗ No'}
            </span>
        </div>
        <div class="health-item">
            <span class="health-label">Responsive:</span>
            <span class="health-value ${health.daemon_responsive ? 'ok' : 'error'}">
                ${health.daemon_responsive ? '✓ Yes' : '✗ No'}
            </span>
        </div>
        ${health.resources ? `
        <div class="health-item">
            <span class="health-label">CPU:</span>
            <span class="health-value">${health.resources.cpu_percent.toFixed(1)}%</span>
        </div>
        <div class="health-item">
            <span class="health-label">Memory:</span>
            <span class="health-value">${health.resources.memory_mb.toFixed(1)} MB</span>
        </div>
        ` : ''}
    `;
    
    // Update firewall status
    const firewallStatus = document.getElementById('firewall-status');
    const fw = health.firewall;
    firewallStatus.innerHTML = `
        <div class="health-item">
            <span class="health-label">Configured:</span>
            <span class="health-value ${fw.configured ? 'ok' : 'error'}">
                ${fw.configured ? '✓ Yes' : '✗ No'}
            </span>
        </div>
        ${fw.ports_open.length > 0 ? `
        <div class="health-item">
            <span class="health-label">Open Ports:</span>
            <span class="health-value">${fw.ports_open.join(', ')}</span>
        </div>
        ` : ''}
        ${fw.missing_rules.length > 0 ? `
        <div class="health-item">
            <span class="health-label">Missing:</span>
            <span class="health-value error">${fw.missing_rules.join(', ')}</span>
        </div>
        ` : ''}
    `;
    
    // Update network status
    const networkStatus = document.getElementById('network-status');
    const net = health.network;
    networkStatus.innerHTML = `
        <div class="health-item">
            <span class="health-label">Local Network:</span>
            <span class="health-value ${net.local_network ? 'ok' : 'error'}">
                ${net.local_network ? '✓ Active' : '✗ Inactive'}
            </span>
        </div>
    `;
    
    // Update ports status
    const portsStatus = document.getElementById('ports-status');
    const ports = health.ports;
    portsStatus.innerHTML = `
        <div class="health-item">
            <span class="health-label">TCP Listening:</span>
            <span class="health-value ${ports.tcp_listening ? 'ok' : 'error'}">
                ${ports.tcp_listening ? '✓ Yes' : '✗ No'}
            </span>
        </div>
        <div class="health-item">
            <span class="health-label">UDP Listening:</span>
            <span class="health-value ${ports.udp_listening ? 'ok' : 'error'}">
                ${ports.udp_listening ? '✓ Yes' : '✗ No'}
            </span>
        </div>
        ${ports.ports.length > 0 ? `
        <div class="health-item">
            <span class="health-label">Active Ports:</span>
            <span class="health-value">${ports.ports.length}</span>
        </div>
        ` : ''}
    `;
}

async function restartDaemon() {
    if (!confirm('Are you sure you want to restart the KDE Connect daemon?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/health/restart', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            addLog('success', 'Daemon restarted successfully');
            showNotification('Success', 'Daemon restarted', 'success');
            setTimeout(loadHealth, 2000);
        } else {
            addLog('error', 'Failed to restart daemon');
            showNotification('Error', 'Failed to restart daemon', 'error');
        }
    } catch (error) {
        addLog('error', `Error restarting daemon: ${error.message}`);
    }
}

// Logging
function addLog(type, message) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
        timestamp,
        type,
        message
    };
    
    logs.unshift(logEntry);
    if (logs.length > 1000) {
        logs.pop();
    }
    
    updateLogsDisplay();
}

function updateLogsDisplay() {
    const logsContent = document.getElementById('logs-content');
    
    logsContent.innerHTML = logs.map(log => `
        <div class="log-entry ${log.type}">
            <span class="log-timestamp">${log.timestamp}</span>
            <span class="log-type">[${log.type.toUpperCase()}]</span>
            <span>${log.message}</span>
        </div>
    `).join('');
}

function clearLogs() {
    if (confirm('Are you sure you want to clear all logs?')) {
        logs = [];
        updateLogsDisplay();
        addLog('info', 'Logs cleared');
    }
}

function exportLogs() {
    const logsText = logs.map(log => 
        `${log.timestamp} [${log.type.toUpperCase()}] ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logsText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kdeconnect-logs-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    addLog('info', 'Logs exported');
}

// Settings
function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('kdecm-settings') || '{}');
    
    document.getElementById('auto-monitoring').checked = settings.autoMonitoring !== false;
    document.getElementById('check-interval').value = settings.checkInterval || 30;
    document.getElementById('desktop-notifications').checked = settings.desktopNotifications !== false;
    document.getElementById('sound-notifications').checked = settings.soundNotifications || false;
    document.getElementById('show-battery').checked = settings.showBattery !== false;
    document.getElementById('show-plugins').checked = settings.showPlugins !== false;
}

function saveSettings() {
    const settings = {
        autoMonitoring: document.getElementById('auto-monitoring').checked,
        checkInterval: parseInt(document.getElementById('check-interval').value),
        desktopNotifications: document.getElementById('desktop-notifications').checked,
        soundNotifications: document.getElementById('sound-notifications').checked,
        showBattery: document.getElementById('show-battery').checked,
        showPlugins: document.getElementById('show-plugins').checked
    };
    
    localStorage.setItem('kdecm-settings', JSON.stringify(settings));
    addLog('success', 'Settings saved');
    showNotification('Success', 'Settings saved successfully', 'success');
}

// Notifications
function showNotification(title, message, type = 'info') {
    const settings = JSON.parse(localStorage.getItem('kdecm-settings') || '{}');
    
    if (settings.desktopNotifications !== false && 'Notification' in window) {
        if (Notification.permission === 'granted') {
            new Notification(title, { body: message });
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification(title, { body: message });
                }
            });
        }
    }
}

// Event Handlers
function initEventHandlers() {
    // Devices tab
    document.getElementById('refresh-devices').addEventListener('click', loadDevices);
    
    // Health tab
    document.getElementById('refresh-health').addEventListener('click', loadHealth);
    document.getElementById('restart-daemon').addEventListener('click', restartDaemon);
    document.getElementById('fix-health').addEventListener('click', async () => {
        addLog('info', 'Auto-fix not yet implemented in web UI. Use CLI: kdecm health fix');
        showNotification('Info', 'Use CLI for auto-fix: kdecm health fix', 'info');
    });
    
    // Logs tab
    document.getElementById('clear-logs').addEventListener('click', clearLogs);
    document.getElementById('export-logs').addEventListener('click', exportLogs);
    
    // Settings tab
    document.getElementById('save-settings').addEventListener('click', saveSettings);
    
    // Modal
    document.querySelector('.modal-close').addEventListener('click', () => {
        document.getElementById('device-modal').classList.remove('active');
    });
    
    document.getElementById('modal-ping').addEventListener('click', () => {
        if (currentDevice) pingDevice(currentDevice);
    });
    
    document.getElementById('modal-ring').addEventListener('click', () => {
        if (currentDevice) ringDevice(currentDevice);
    });
    
    document.getElementById('modal-unpair').addEventListener('click', async () => {
        if (!currentDevice) return;
        
        if (confirm('Are you sure you want to unpair this device?')) {
            try {
                const response = await fetch(`/api/devices/${currentDevice}/unpair`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    addLog('success', 'Device unpaired');
                    showNotification('Success', 'Device unpaired', 'success');
                    document.getElementById('device-modal').classList.remove('active');
                    loadDevices();
                }
            } catch (error) {
                addLog('error', `Error unpairing device: ${error.message}`);
            }
        }
    });
    
    // Close modal on outside click
    document.getElementById('device-modal').addEventListener('click', (e) => {
        if (e.target.id === 'device-modal') {
            document.getElementById('device-modal').classList.remove('active');
        }
    });
}

// Auto-refresh
setInterval(() => {
    const settings = JSON.parse(localStorage.getItem('kdecm-settings') || '{}');
    if (settings.autoMonitoring !== false) {
        loadDevices();
        loadHealth();
    }
}, 30000); // 30 seconds
