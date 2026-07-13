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
- ALSA diagnostic tools such as `arecord` and `aplay` from `alsa-utils`
- microphone input working on the device

The checked-in `apt-manual.txt` shows PocketSphinx and the main Pi GPIO/audio packages that were installed on the target system.

Minimal run steps:

```powershell
cd pi
python voice_bridge.py
```

If you use a virtual environment, install the packages you actually need rather than blindly applying the full frozen `requirements.txt`.

## Run On Boot

The repo includes a `systemd` unit at `pi/voice-bridge.service`.

If your checkout is at `/home/pi/voice-activated-table-lift/code`, install it with:

```bash
sudo cp /home/pi/voice-activated-table-lift/code/pi/voice-bridge.service /etc/systemd/system/voice-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable voice-bridge.service
sudo systemctl start voice-bridge.service
sudo systemctl status voice-bridge.service
```

If your repo lives somewhere else or runs under a different user, update `User`, `WorkingDirectory`, and `ExecStart` in the service file before enabling it.

## Configuration

`voice_config.json` currently contains:

- `cooldown_seconds`: minimum time between repeated sends of the same command
- `allow_repeat_stop`: whether `STOP` bypasses cooldown
- `pocketsphinx_binary`: executable to launch
- `audio_backend`: `pocketsphinx_mic` for direct PocketSphinx capture or
  `arecord_pipe` to pipe ALSA audio into PocketSphinx
- `audio_device`: optional PortAudio/ALSA capture device passed as `-adcdev`
- `audio_rate`: capture sample rate used by `arecord_pipe`
- `audio_channels`: capture channel count used by `arecord_pipe`
- `audio_format`: capture sample format used by `arecord_pipe`
- `audio_buffer_time_us`: ALSA capture buffer size used by `arecord_pipe`
- `keywords_file`: output file for generated keywords
- `keywords`: list of phrase mappings

The file also contains `serial_port` and `baud_rate`, but the present implementation does not use serial I/O.

Example:

```json
{
  "cooldown_seconds": 1.5,
  "allow_repeat_stop": true,
  "pocketsphinx_binary": "pocketsphinx_continuous",
  "audio_backend": "arecord_pipe",
  "audio_device": "plughw:0,0",
  "audio_rate": 16000,
  "audio_channels": 1,
  "audio_format": "S16_LE",
  "audio_buffer_time_us": 500000,
  "keywords_file": "keywords.list",
  "keywords": [
    { "phrase": "open", "threshold": "1e-20", "command": "EXTEND" },
    { "phrase": "close", "threshold": "1e-20", "command": "RETRACT" },
    { "phrase": "stop", "threshold": "1e-20", "command": "STOP" }
  ]
}
```

## Wiring Assumptions

The Pi uses two separate sets of GPIO wiring:

1. I2S microphone input into the Pi.
2. Digital command outputs from the Pi to the ESP32.

### I2S Microphone Wiring

For the Adafruit I2S MEMS Microphone Breakout - SPH0645LM4H used by this
project, wire the microphone signals to the Pi's I2S/PCM pins:

| Pi signal | Pi BCM GPIO | Physical header pin | I2S mic label commonly seen |
| --- | ---: | ---: | --- |
| PCM clock | `18` | `12` | `BCLK`, `SCK`, or `SCLK` |
| PCM frame sync | `19` | `35` | `LRCLK`, `WS`, `FS`, or `LRC` |
| PCM data in | `20` | `38` | `DOUT`, `SD`, `SDOUT`, or `DATA` |
| 3.3 V power | n/a | `1` or `17` | `3V` |
| Ground | n/a | any Pi ground pin | `GND` |
| Channel select | n/a | any Pi ground pin for mono | `SEL` |

If using two I2S mics on the same bus, both mics share `BCLK`, `LRCLK/WS`,
`DOUT/SD`, `3.3 V`, and `GND`. Set one mic's `SEL`, `L/R`, or `LR` pin low
and the other high so they occupy opposite left/right slots. On many breakout
boards that means one `SEL/LR` pin goes to `GND` and the other goes to `3.3 V`.

GPIO `17` and GPIO `27` are not microphone pins in this project.

### ESP32 Command Wiring

The script drives these Pi outputs:

- BCM `17` as the first command bit
- BCM `27` as the second command bit

The ESP32 firmware currently expects the incoming command bits on:

- GPIO `26` as `S1`
- GPIO `27` as `S0`

Use a shared ground between the Pi and ESP32, and verify voltage compatibility before direct GPIO connection.

## Audio Device Troubleshooting

By default, `voice_bridge.py` uses `arecord_pipe`, which captures from ALSA and
pipes raw audio into PocketSphinx:

```bash
arecord -D plughw:0,0 -c 1 -r 16000 -f S16_LE -t raw --buffer-time 500000 |
  pocketsphinx_continuous -infile /dev/stdin -kws keywords.list -samprate 16000
```

This avoids PocketSphinx's PortAudio capture path, which can fail on Ubuntu
Server with `Error opening audio device (null) for capture: Connection refused`.

If `audio_backend` is set to `pocketsphinx_mic`, `voice_bridge.py` starts
PocketSphinx with:

```bash
pocketsphinx_continuous -inmic yes -kws keywords.list
```

In that mode, if `audio_device` is set in `voice_config.json`, the bridge passes
`-adcdev <audio_device>` to PocketSphinx.

The error shown by PocketSphinx as `Failed to open audio device` means
PocketSphinx and its language model started, but PortAudio/ALSA could not open
a usable capture device. On Ubuntu Server this usually means the I2S sound-card
overlay is not enabled, ALSA does not have a default capture device, or the
runtime user does not have permission to use the audio device.

Check whether Linux sees any capture devices:

```bash
sudo apt update
sudo apt install alsa-utils python3-pyaudio
arecord -l
arecord -L
```

On newer Ubuntu releases, `pip install pyaudio` in the system Python may fail
with an "externally managed environment" error. That is expected; install the
system package with `sudo apt install python3-pyaudio` instead, or use a virtual
environment if you need pip-managed packages.

If no capture card appears, enable the sound-card overlay for the Adafruit
SPH0645LM4H breakout. On Ubuntu Server for Raspberry Pi this is normally edited
in `/boot/firmware/config.txt`; on Raspberry Pi OS it is usually
`/boot/config.txt`. Add:

```ini
dtoverlay=googlevoicehat-soundcard
```

After changing boot config, reboot and check `arecord -l` again.

Once a capture device exists, test recording before starting the bridge:

```bash
arecord -D plughw:1 -c1 -r 48000 -f S32_LE -t wav -V mono -v /tmp/mic-test.wav
aplay /tmp/mic-test.wav
```

For the bridge's default pipe path, test the same rate and format it uses:

```bash
arecord -D plughw:0,0 -c1 -r 16000 -f S16_LE -t raw --buffer-time 500000 |
  pocketsphinx_continuous -infile /dev/stdin -kws keywords.list -samprate 16000
```

`arecord` overrun messages mean the capture buffer filled before the downstream
process consumed all samples. Occasional overruns are not fatal if recognition
works. If they are frequent, increase `audio_buffer_time_us` in
`voice_config.json`, for example to `1000000`, or test whether `audio_rate`
`48000` is more stable with the sound card.

If `arecord -l` shows the mic but `pocketsphinx_continuous -inmic yes` still
fails, set the ALSA default capture device in `~/.asoundrc` or `/etc/asound.conf`
so PortAudio has a `default` input device to open, or set `audio_device` in
`voice_config.json` to an explicit ALSA device such as `plughw:1,0` after
confirming the card and device numbers with `arecord -l`.

Also verify that the service user is in the `audio` group:

```bash
groups
sudo usermod -aG audio "$USER"
```

Log out and back in after changing group membership.

## Limitations

- No debounce or confidence filtering beyond PocketSphinx keyword thresholds and cooldown.
- No unit tests are present for the Pi runtime.
