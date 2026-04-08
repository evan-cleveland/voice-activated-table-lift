#!/usr/bin/env bash
set -euo pipefail

sudo systemctl stop voice-bridge.service || true
sudo systemctl disable voice-bridge.service
sudo systemctl daemon-reload
sudo systemctl status voice-bridge.service --no-pager || true
