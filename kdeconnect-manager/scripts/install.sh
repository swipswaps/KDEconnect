#!/bin/bash
################################################################################
# KDE Connect Manager - Installation Script
# For Fedora 42+ systems
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Fedora
check_fedora() {
    if [ -f /etc/fedora-release ]; then
        local version=$(cat /etc/fedora-release | grep -oP '\d+')
        if [ "$version" -ge 42 ]; then
            log_success "Detected Fedora $version"
            return 0
        else
            log_warning "Fedora version $version detected. This script is designed for Fedora 42+."
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        log_error "This script is designed for Fedora systems."
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Core KDE Connect packages
    sudo dnf install -y \
        kdeconnect \
        kdeconnect-kde \
        kde-connect-indicator \
        || log_warning "Some KDE Connect packages may not be available"
    
    # Development tools and libraries
    sudo dnf install -y \
        python3 \
        python3-pip \
        python3-devel \
        gcc \
        dbus-devel \
        qt5-qtbase-devel
    
    # Network and firewall tools
    sudo dnf install -y \
        firewalld \
        NetworkManager
    
    # Screen sharing tools
    sudo dnf install -y \
        krfb \
        x11vnc \
        pipewire \
        wireplumber \
        xdg-desktop-portal \
        xdg-desktop-portal-kde \
        || log_warning "Some screen sharing packages may not be available"
    
    # SSH and remote management
    sudo dnf install -y \
        openssh-server \
        openssh-clients
    
    log_success "System dependencies installed"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        python3 -m pip install --user -r "$PROJECT_DIR/requirements.txt"
        log_success "Python dependencies installed"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."
    
    # Start and enable firewalld
    sudo systemctl start firewalld
    sudo systemctl enable firewalld
    
    # Add KDE Connect service
    sudo firewall-cmd --zone=public --permanent --add-service=kdeconnect || \
        log_warning "KDE Connect service not available, adding ports manually"
    
    # Add ports manually as backup
    sudo firewall-cmd --zone=public --permanent --add-port=1714-1764/tcp
    sudo firewall-cmd --zone=public --permanent --add-port=1714-1764/udp
    
    # Add port for web interface
    sudo firewall-cmd --zone=public --permanent --add-port=5000/tcp
    
    # Reload firewall
    sudo firewall-cmd --reload
    
    log_success "Firewall configured"
}

# Setup systemd services
setup_systemd() {
    log_info "Setting up systemd services..."
    
    # Create user systemd directory
    mkdir -p ~/.config/systemd/user
    
    # Copy KDE Connect daemon service
    if [ -f "$PROJECT_DIR/systemd/kdeconnect.service" ]; then
        cp "$PROJECT_DIR/systemd/kdeconnect.service" ~/.config/systemd/user/
        systemctl --user daemon-reload
        systemctl --user enable kdeconnect.service
        systemctl --user start kdeconnect.service
        log_success "KDE Connect daemon service enabled"
    fi
    
    # Copy KDE Connect Manager service
    if [ -f "$PROJECT_DIR/systemd/kdeconnect-manager.service" ]; then
        # Update paths in service file
        sed -i "s|/path/to/kdeconnect-manager|$PROJECT_DIR|g" \
            "$PROJECT_DIR/systemd/kdeconnect-manager.service"
        
        cp "$PROJECT_DIR/systemd/kdeconnect-manager.service" ~/.config/systemd/user/
        systemctl --user daemon-reload
        systemctl --user enable kdeconnect-manager.service
        log_success "KDE Connect Manager service configured (not started automatically)"
        log_info "Start with: systemctl --user start kdeconnect-manager.service"
    fi
}

# Install CLI tool
install_cli() {
    log_info "Installing CLI tool..."
    
    # Make CLI executable
    chmod +x "$PROJECT_DIR/cli/kdecm.py"
    
    # Create symlink in user bin
    mkdir -p ~/.local/bin
    ln -sf "$PROJECT_DIR/cli/kdecm.py" ~/.local/bin/kdecm
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        log_info "Added ~/.local/bin to PATH. Restart shell or run: source ~/.bashrc"
    fi
    
    log_success "CLI tool installed. Use 'kdecm' command."
}

# Create logs directory
create_logs_dir() {
    mkdir -p "$PROJECT_DIR/logs"
    log_success "Logs directory created"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    local errors=0
    
    # Check kdeconnectd
    if command -v kdeconnectd &> /dev/null; then
        log_success "kdeconnectd found"
    else
        log_error "kdeconnectd not found"
        ((errors++))
    fi
    
    # Check kdeconnect-cli
    if command -v kdeconnect-cli &> /dev/null; then
        log_success "kdeconnect-cli found"
    else
        log_error "kdeconnect-cli not found"
        ((errors++))
    fi
    
    # Check Python packages
    if python3 -c "import flask" 2>/dev/null; then
        log_success "Flask installed"
    else
        log_error "Flask not installed"
        ((errors++))
    fi
    
    if python3 -c "import dbus" 2>/dev/null; then
        log_success "dbus-python installed"
    else
        log_error "dbus-python not installed"
        ((errors++))
    fi
    
    # Check firewall
    if sudo firewall-cmd --list-services --zone=public | grep -q kdeconnect; then
        log_success "Firewall configured"
    else
        log_warning "KDE Connect service not in firewall, but ports may be open"
    fi
    
    # Check daemon status
    if systemctl --user is-active --quiet kdeconnect.service; then
        log_success "KDE Connect daemon is running"
    else
        log_warning "KDE Connect daemon is not running"
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "Installation verified successfully!"
        return 0
    else
        log_error "Installation verification failed with $errors errors"
        return 1
    fi
}

# Print post-installation instructions
print_instructions() {
    echo ""
    echo "=========================================="
    echo "  KDE Connect Manager - Post-Install"
    echo "=========================================="
    echo ""
    echo "✓ Installation completed!"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Start the web interface:"
    echo "   kdecm server start"
    echo "   or"
    echo "   systemctl --user start kdeconnect-manager.service"
    echo ""
    echo "2. Access web UI:"
    echo "   http://localhost:5000"
    echo ""
    echo "3. Use CLI commands:"
    echo "   kdecm device list          - List devices"
    echo "   kdecm health check         - Check system health"
    echo "   kdecm --help               - See all commands"
    echo ""
    echo "4. Pair your devices:"
    echo "   - Open KDE Connect on your phone/tablet"
    echo "   - Both devices should be on the same network"
    echo "   - They should appear automatically"
    echo ""
    echo "Documentation: $PROJECT_DIR/README.md"
    echo "Logs: $PROJECT_DIR/logs/"
    echo ""
    echo "=========================================="
}

# Main installation flow
main() {
    echo ""
    echo "=========================================="
    echo "  KDE Connect Manager - Installation"
    echo "=========================================="
    echo ""
    
    check_fedora
    
    log_info "Starting installation..."
    echo ""
    
    install_dependencies
    install_python_deps
    configure_firewall
    create_logs_dir
    setup_systemd
    install_cli
    
    echo ""
    verify_installation
    
    echo ""
    print_instructions
}

# Run main function
main "$@"
