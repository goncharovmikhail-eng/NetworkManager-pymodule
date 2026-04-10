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
        dbus \
        dbus-x11 \
        libdbus-1-dev \
        libglib2.0-dev \
        pkg-config \
        network-manager \
        python3-dbus

    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y \
        dbus \
        dbus-x11 \
        libdbus-1-dev \
        libglib2.0-dev \
        pkg-config \
        network-manager \
        python3-dbus
    else
        echo "[ERROR] Unsupported package manager"
        exit 1
    fi
fi

sudo systemctl start dbus
sudo systemctl start NetworkManager

echo "[INFO] Creating virtual environment..."

echo "
python3 -m venv venv --system-site-packages
source venv/bin/activate

pip install dist_out/dist/*.whl

echo '[INFO] Setup complete!' "
