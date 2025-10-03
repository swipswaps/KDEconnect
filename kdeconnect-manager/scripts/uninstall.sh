#!/bin/bash
################################################################################
# KDE Connect Manager - Uninstallation Script
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

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo ""
echo "=========================================="
echo "  KDE Connect Manager - Uninstall"
echo "=========================================="
echo ""

read -p "Are you sure you want to uninstall KDE Connect Manager? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

log_info "Uninstalling KDE Connect Manager..."

# Stop services
log_info "Stopping services..."
systemctl --user stop kdeconnect-manager.service 2>/dev/null || true
systemctl --user stop kdeconnect.service 2>/dev/null || true

# Disable services
log_info "Disabling services..."
systemctl --user disable kdeconnect-manager.service 2>/dev/null || true
systemctl --user disable kdeconnect.service 2>/dev/null || true

# Remove service files
log_info "Removing service files..."
rm -f ~/.config/systemd/user/kdeconnect.service
rm -f ~/.config/systemd/user/kdeconnect-manager.service
systemctl --user daemon-reload

# Remove CLI symlink
log_info "Removing CLI tool..."
rm -f ~/.local/bin/kdecm

# Remove firewall rules (optional)
read -p "Remove KDE Connect firewall rules? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Removing firewall rules..."
    sudo firewall-cmd --zone=public --permanent --remove-service=kdeconnect 2>/dev/null || true
    sudo firewall-cmd --zone=public --permanent --remove-port=1714-1764/tcp 2>/dev/null || true
    sudo firewall-cmd --zone=public --permanent --remove-port=1714-1764/udp 2>/dev/null || true
    sudo firewall-cmd --zone=public --permanent --remove-port=5000/tcp 2>/dev/null || true
    sudo firewall-cmd --reload
    log_success "Firewall rules removed"
fi

# Uninstall KDE Connect (optional)
read -p "Uninstall KDE Connect packages? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Uninstalling KDE Connect..."
    sudo dnf remove -y kdeconnect kdeconnect-kde kde-connect-indicator 2>/dev/null || true
    log_success "KDE Connect packages removed"
fi

log_success "KDE Connect Manager uninstalled"
log_info "You can manually remove the project directory: $PROJECT_DIR"

echo ""
