#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_SRC="$SCRIPT_DIR/voice-bridge.service"
SERVICE_DST="/etc/systemd/system/voice-bridge.service"
SERVICE_USER="${SUDO_USER:-$(id -un)}"
PYTHON_BIN="$(command -v python3)"

if [[ ! -f "$SERVICE_SRC" ]]; then
  echo "Service file not found: $SERVICE_SRC" >&2
  exit 1
fi

tmp_service="$(mktemp)"
sed \
  -e "s|^User=.*|User=$SERVICE_USER|" \
  -e "s|^WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|" \
  -e "s|^ExecStart=.*|ExecStart=$PYTHON_BIN $SCRIPT_DIR/voice_bridge.py|" \
  "$SERVICE_SRC" > "$tmp_service"

sudo cp "$tmp_service" "$SERVICE_DST"
rm -f "$tmp_service"

if ! groups "$SERVICE_USER" | grep -qw audio; then
  echo "Adding $SERVICE_USER to the audio group. Log out and back in, or reboot, before relying on boot-time audio access."
  sudo usermod -aG audio "$SERVICE_USER"
fi

sudo systemctl daemon-reload
sudo systemctl enable voice-bridge.service
sudo systemctl restart voice-bridge.service
sudo systemctl status voice-bridge.service --no-pager
