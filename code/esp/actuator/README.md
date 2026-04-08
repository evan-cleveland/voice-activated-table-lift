# ESP32 Actuator Firmware

This PlatformIO project reads a 2-bit command from external GPIO lines and drives a motor controller for the table lift actuator.

## Project

- Platform: `espressif32`
- Board: `esp32dev`
- Framework: `arduino`
- Monitor speed: `115200`

## Source Layout

- `src/main.cpp`: main firmware
- `include/`: shared headers, currently unused
- `lib/`: local libraries, currently unused
- `test/`: PlatformIO test directory, currently unused

## Command Inputs

The firmware reads two input pins with pulldowns enabled:

- `S1 = 26`
- `S0 = 27`
- `CONTRACT_LIMIT_SWITCH = 25`

Command behavior:

- `11` -> stop motor
- `01` -> drive `RPWM`
- `10` -> drive `LPWM` unless the contract limit switch is active
- `00` -> stop motor

This matches the command encoding produced by the Pi bridge.

## Contract Limit Switch

The contract limit switch input uses the ESP32 internal pull-up:

- wiring mode: normally open
- inactive state: open circuit, input reads `HIGH`
- active state: switch depressed, input is connected to ground and reads `LOW`

When the switch is active, the firmware stops the motor and ignores further retract commands until the switch is released.

## Motor Driver Pins

- `RPWM = 19`
- `LPWM = 21`
- `REN = 23`
- `LEN = 5`

PWM configuration:

- frequency: `20000`
- resolution: `8`
- channels: `0` and `1`
- speed value: `255`

## Build And Flash

Typical PlatformIO commands:

```powershell
cd esp\actuator
pio run
pio run -t upload
pio device monitor -b 115200
```

You can also build and upload through the PlatformIO VS Code extension if that is how you are working on the ESP32 side.

## Wiring Notes

- The two command input lines should come from the Raspberry Pi GPIO outputs documented in the Pi README.
- Wire the contract limit switch between GPIO `25` and ground if you use the default pin assignment in `src/main.cpp`.
- Grounds must be shared between the control side and the ESP32.
- Confirm that the electrical interface between the Pi GPIO and ESP32 input pins is safe for your board configuration.
