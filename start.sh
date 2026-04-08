#!/bin/bash
set -euo pipefail

SKIP_SYSTEM_PACKAGES=false

# Разбираем флаги
for arg in "$@"; do
    case $arg in
        --skip-system-packages)
            SKIP_SYSTEM_PACKAGES=true
            shift
            ;;
        *)
            ;;
    esac
done

echo "[INFO] Skip system packages: $SKIP_SYSTEM_PACKAGES"

if [ "$SKIP_SYSTEM_PACKAGES" = false ]; then
    echo "[INFO] Detecting package manager..."

    if command -v apt >/dev/null 2>&1; then
        echo "[INFO] Using apt (Debian/Ubuntu)"

        sudo apt update
        sudo apt install -y \
            python3-dev \
            libdbus-1-dev \
            libglib2.0-dev \
            libgirepository1.0-dev \
            gcc \
            network-manager \
            dnsutils

    elif command -v dnf >/dev/null 2>&1; then
        echo "[INFO] Using dnf (Fedora/RHEL)"

        sudo dnf install -y \
            python3-devel \
            dbus-devel \
            glib2-devel \
            gobject-introspection-devel \
            gcc \
            NetworkManager \
            bind-utils

    else
        echo "[ERROR] Unsupported package manager"
        exit 1
    fi
else
    echo "[INFO] Skipping system packages installation"
fi

echo "[INFO] Creating virtual environment..."
 sudo apt install python3.11-venv
python3 -m venv venv
source venv/bin/activate

echo "[INFO] Installing Python dependencies..."
pip install --upgrade pip
pip install --default-timeout=100 -r requirements.txt

echo "[INFO] Setup complete!"
