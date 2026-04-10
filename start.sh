#!/bin/bash
set -euo pipefail

SKIP_SYSTEM_PACKAGES=false

for arg in "$@"; do
    case $arg in
        --skip-system-packages) SKIP_SYSTEM_PACKAGES=true; shift ;;
        *) ;;
    esac
done

if [ "$SKIP_SYSTEM_PACKAGES" = false ]; then
    echo "[INFO] Installing system dependencies..."

    if command -v apt >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y \
            python3-dev \
            python3-venv \
            libdbus-1-dev \
            libglib2.0-dev \
            gcc \
            network-manager
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y \
            python3-devel \
            dbus-devel \
            glib2-devel \
            gcc \
            NetworkManager
    else
        echo "[ERROR] Unsupported package manager"
        exit 1
    fi
fi

echo "[INFO] Creating virtual environment..."

echo "
python3 -m venv venv
source venv/bin/activate

echo '[INFO] Installing Python dependencies...'
pip install --upgrade pip
pip install -r requirements.txt

echo '[INFO] Setup complete!' "
