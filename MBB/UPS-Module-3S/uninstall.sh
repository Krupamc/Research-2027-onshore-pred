#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="lafvin-ups"
APP_DIR="/opt/${APP_NAME}"
CONFIG_FILE="/etc/${APP_NAME}.conf"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
PURGE=false

if [[ ${1:-} == "--purge" ]]; then
    PURGE=true
elif [[ $# -gt 0 ]]; then
    echo "Usage: sudo ./uninstall.sh [--purge]" >&2
    exit 2
fi

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this uninstaller with sudo: sudo ./uninstall.sh" >&2
    exit 1
fi

systemctl disable --now "${APP_NAME}.service" 2>/dev/null || true
rm -f "$SERVICE_FILE"
rm -rf "$APP_DIR" "/run/${APP_NAME}"
systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true

if $PURGE; then
    rm -f "$CONFIG_FILE"
    echo "Removed configuration: ${CONFIG_FILE}"
else
    echo "Kept configuration: ${CONFIG_FILE}"
    echo "Use --purge to remove it as well."
fi

echo "LAFVIN UPS monitor removed."
