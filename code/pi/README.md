# Raspberry Pi Voice Bridge

This directory contains the speech-recognition process that listens for wake phrases and drives two GPIO outputs that represent actuator commands.

## Files

- `voice_bridge.py`: main runtime process
- `voice_config.json`: keyword list, PocketSphinx binary name, and cooldown settings
- `keywords.list`: generated PocketSphinx keyword file
- `requirements.txt`: current full pip freeze from the Pi environment
- `requirements-user.txt`: reserved for user-managed pip packages
- `apt-manual.txt`: manually installed apt packages from the target Pi

## Runtime Behavior

`voice_bridge.py` does the following:

1. Loads `voice_config.json`.
2. Rebuilds `keywords.list` from the configured phrases and thresholds.
3. Starts `pocketsphinx_continuous` with microphone input.
4. Maps recognized phrases to commands.
5. Drives GPIO outputs:
   - BCM `17`
   - BCM `27`
6. Applies a per-command cooldown.
7. Sends `STOP` on shutdown.

Configured commands in the checked-in config:

- `open` -> `EXTEND`
- `close` -> `RETRACT`
- `stop` -> `STOP`

Bit encoding used by the script:

- `EXTEND` -> `01`
- `RETRACT` -> `10`
- `STOP` -> `11`
- `NULL` -> `00`

## Setup

The code assumes a Raspberry Pi environment with:

- Python 3
- `gpiozero`
- PocketSphinx CLI available as `pocketsphinx_continuous`
- microphone input working on the device

The checked-in `apt-manual.txt` shows PocketSphinx and the main Pi GPIO/audio packages that were installed on the target system.

Minimal run steps:

```powershell
cd pi
python voice_bridge.py
```

If you use a virtual environment, install the packages you actually need rather than blindly applying the full frozen `requirements.txt`.

## Configuration

`voice_config.json` currently contains:

- `cooldown_seconds`: minimum time between repeated sends of the same command
- `allow_repeat_stop`: whether `STOP` bypasses cooldown
- `pocketsphinx_binary`: executable to launch
- `keywords_file`: output file for generated keywords
- `keywords`: list of phrase mappings

The file also contains `serial_port` and `baud_rate`, but the present implementation does not use serial I/O.

Example:

```json
{
  "cooldown_seconds": 1.5,
  "allow_repeat_stop": true,
  "pocketsphinx_binary": "pocketsphinx_continuous",
  "keywords_file": "keywords.list",
  "keywords": [
    { "phrase": "open", "threshold": "1e-20", "command": "EXTEND" },
    { "phrase": "close", "threshold": "1e-20", "command": "RETRACT" },
    { "phrase": "stop", "threshold": "1e-20", "command": "STOP" }
  ]
}
```

## Wiring Assumptions

The script drives:

- BCM `17` as the first command bit
- BCM `27` as the second command bit

The ESP32 firmware currently expects the incoming command bits on:

- GPIO `26` as `S1`
- GPIO `27` as `S0`

Use a shared ground between the Pi and ESP32, and verify voltage compatibility before direct GPIO connection.

## Limitations

- No daemon/service file is included yet.
- No debounce or confidence filtering beyond PocketSphinx keyword thresholds and cooldown.
- No unit tests are present for the Pi runtime.
