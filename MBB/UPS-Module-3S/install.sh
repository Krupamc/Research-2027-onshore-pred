#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="lafvin-ups"
APP_DIR="/opt/${APP_NAME}"
CONFIG_FILE="/etc/${APP_NAME}.conf"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

log() {
    printf '[%s] %s\n' "$APP_NAME" "$*"
}

fail() {
    printf '[%s] ERROR: %s\n' "$APP_NAME" "$*" >&2
    exit 1
}

[[ ${EUID} -eq 0 ]] || fail "Run this installer with sudo: sudo ./install.sh"
[[ -f "${SCRIPT_DIR}/src/ups_monitor.py" ]] || fail "src/ups_monitor.py not found"
[[ -f "${SCRIPT_DIR}/src/ina219.py" ]] || fail "src/ina219.py not found"
[[ -f "${SCRIPT_DIR}/config/lafvin-ups.conf" ]] || fail "config/lafvin-ups.conf not found"
[[ -f "${SCRIPT_DIR}/systemd/lafvin-ups.service" ]] || fail "systemd/lafvin-ups.service not found"
command -v systemctl >/dev/null 2>&1 || fail "systemd/systemctl is required"
command -v apt-get >/dev/null 2>&1 || fail "This installer currently supports Raspberry Pi OS/Debian with apt-get"

MODEL="unknown Raspberry Pi"
if [[ -r /proc/device-tree/model ]]; then
    MODEL="$(tr -d '\0' </proc/device-tree/model)"
fi
log "Detected platform: ${MODEL}"

log "Installing system dependencies"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-smbus i2c-tools

log "Enabling I2C"
if command -v raspi-config >/dev/null 2>&1; then
    raspi-config nonint do_i2c 0 || log "Warning: raspi-config could not enable I2C automatically"
else
    BOOT_CONFIG=""
    if [[ -f /boot/firmware/config.txt ]]; then
        BOOT_CONFIG="/boot/firmware/config.txt"
    elif [[ -f /boot/config.txt ]]; then
        BOOT_CONFIG="/boot/config.txt"
    fi

    if [[ -n "$BOOT_CONFIG" ]]; then
        if ! grep -Eq '^[[:space:]]*dtparam=i2c_arm=on([[:space:]]|$)' "$BOOT_CONFIG"; then
            printf '\n# Enabled by LAFVIN UPS installer\ndtparam=i2c_arm=on\n' >>"$BOOT_CONFIG"
        fi
    else
        log "Warning: Raspberry Pi boot config was not found; enable I2C manually"
    fi
fi
modprobe i2c-dev 2>/dev/null || true

log "Installing application files"
install -d -m 0755 "$APP_DIR"
install -m 0755 "${SCRIPT_DIR}/src/ups_monitor.py" "${APP_DIR}/ups_monitor.py"
install -m 0644 "${SCRIPT_DIR}/src/ina219.py" "${APP_DIR}/ina219.py"

if [[ -f "$CONFIG_FILE" ]]; then
    log "Keeping existing configuration: ${CONFIG_FILE}"
else
    install -m 0644 "${SCRIPT_DIR}/config/lafvin-ups.conf" "$CONFIG_FILE"
    log "Installed default configuration: ${CONFIG_FILE}"
fi

install -m 0644 "${SCRIPT_DIR}/systemd/lafvin-ups.service" "$SERVICE_FILE"

log "Enabling and starting systemd service"
systemctl daemon-reload
systemctl enable --now "${APP_NAME}.service"

I2C_BUS="$(awk -F= '/^[[:space:]]*i2c_bus[[:space:]]*=/{gsub(/[[:space:]]/, "", $2); print $2; exit}' "$CONFIG_FILE")"
I2C_BUS="${I2C_BUS:-1}"
I2C_ADDRESS="$(awk -F= '/^[[:space:]]*i2c_address[[:space:]]*=/{gsub(/[[:space:]]/, "", $2); print $2; exit}' "$CONFIG_FILE")"
I2C_ADDRESS="${I2C_ADDRESS:-0x41}"

printf '\n'
log "Installation complete"
log "Service: systemctl status ${APP_NAME}.service"
log "Logs:    journalctl -u ${APP_NAME}.service -f"
log "Status:  cat /run/${APP_NAME}/status.json"
log "Test:    python3 ${APP_DIR}/ups_monitor.py --config ${CONFIG_FILE} --once"
printf '\n'
log "Check configuration: ${CONFIG_FILE}"
log "Automatic safe shutdown is enabled by default."
log "Verify the voltage readings and shutdown thresholds before long-term use."

if [[ -e "/dev/i2c-${I2C_BUS}" ]]; then
    log "I2C scan for bus ${I2C_BUS} (expected address ${I2C_ADDRESS}):"
    i2cdetect -y "$I2C_BUS" || true
else
    log "Warning: /dev/i2c-${I2C_BUS} is not available yet. Reboot, then check the service log."
fi
