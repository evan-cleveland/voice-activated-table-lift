# Voice-Activated Table Lift

This repository contains the two runtime pieces for a voice-controlled lift table:

- `pi/`: Raspberry Pi speech-detection bridge using PocketSphinx and GPIO output pins.
- `esp/actuator/`: ESP32 firmware that reads two control lines and drives the actuator motor.

The current design is GPIO-based end to end. The Pi listens for keywords, maps them to command bits, and drives two output pins. The ESP32 reads those bits and selects motor direction or stop.

## Architecture

Command mapping:

- `EXTEND` -> `01`
- `RETRACT` -> `10`
- `STOP` -> `11`
- idle / no command -> `00`

Current pin usage:

- Raspberry Pi outputs: BCM `17` and `27`
- ESP32 inputs: GPIO `26` and `27`
- ESP32 contract limit switch input: GPIO `25` with `INPUT_PULLUP`
- ESP32 motor driver pins:
  - `RPWM = 19`
  - `LPWM = 21`
  - `REN = 23`
  - `LEN = 5`

## Repo Layout

```text
code/
|- pi/
|  |- voice_bridge.py
|  |- voice_config.json
|  |- requirements.txt
|  |- requirements-user.txt
|  |- apt-manual.txt
|  `- keywords.list
`- esp/
   `- actuator/
      |- platformio.ini
      |- src/main.cpp
      |- include/
      |- lib/
      `- test/
```

## Typical Flow

1. Flash the ESP32 firmware from `esp/actuator/`.
2. Wire the Pi GPIO outputs to the ESP32 command inputs and connect grounds.
3. Install PocketSphinx and the Pi-side Python dependencies.
4. Adjust `pi/voice_config.json` if you want different phrases or thresholds.
5. Run `voice_bridge.py` on the Pi.

## Notes

- The ESP32 retract path is interlocked by a normally-open limit switch that pulls GPIO `25` to ground when depressed.
- `voice_config.json` still includes `serial_port` and `baud_rate`, but the current script does not use serial.
- `pi/requirements.txt` appears to be a full environment freeze, not a minimal project dependency list.
- The generated keyword file is written to `pi/keywords.list` each time the bridge starts.

## Subproject Docs

- [Pi runtime](C:/Users/Evan/documents/cs/projects/voice-activated-table-lift/code/pi/README.md)
- [ESP32 actuator firmware](C:/Users/Evan/documents/cs/projects/voice-activated-table-lift/code/esp/actuator/README.md)
