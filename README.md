# Voice-Activated Table Lift

This project is a coffee table with a hidden lift mechanism that opens a compartment when the control electronics are triggered by a voice-password system.

At the moment, this repository contains the actuator-side ESP32 firmware and the mechanical / electronics design files. The actual speech-recognition or password-detection code is not in this repo yet.

## What is in the repo

- `code/esp/actuator`: PlatformIO project for an ESP32 that drives the lift motor.
- `cad/box.*`: enclosure / printable box files for part of the hardware.
- `cad/pcb`: KiCad project directory for the PCB.

## Firmware behavior

The ESP32 firmware is a small motor controller built with the Arduino framework.

- GPIO `26` (`S1`) and GPIO `27` (`S0`) are digital control inputs.
- GPIO `19` (`RPWM`) and GPIO `21` (`LPWM`) output PWM to the motor driver.
- GPIO `23` (`REN`) and GPIO `5` (`LEN`) are held high to enable the driver.
- PWM runs at `20 kHz` with `8-bit` resolution.
- Motor speed is currently fixed at full duty cycle (`255`).

Control logic:

- `S0 = HIGH`, `S1 = LOW`: drive in one direction.
- `S1 = HIGH`, `S0 = LOW`: drive in the opposite direction.
- `S0 = HIGH`, `S1 = HIGH`: stop.
- both low: stop.

This makes the firmware easy to pair with an external controller that decides when to open or close the hidden compartment.

## Hardware notes

The current firmware assumes:

- an ESP32 development board,
- a motor driver that accepts separate right/left PWM inputs plus enable pins,
- a linear actuator or DC motor for the lift mechanism,
- two logic-level control signals from whatever handles the voice trigger.

Because the KiCad schematic in `cad/pcb` is still mostly empty, the exact wiring is best taken from the pin definitions in `code/esp/actuator/src/main.cpp`.

## Building and flashing

Requirements:

- [PlatformIO](https://platformio.org/)
- an ESP32 board supported by the `esp32dev` PlatformIO target

Build:

```bash
cd code/esp/actuator
pio run
```

Flash:

```bash
cd code/esp/actuator
pio run --target upload
```

Optional serial monitor:

```bash
cd code/esp/actuator
pio device monitor --baud 115200
```

## Project structure

```text
.
|-- cad/
|   |-- box.3mf
|   |-- box.SLDPRT
|   |-- box.STL
|   `-- pcb/
`-- code/
    `-- esp/
        `-- actuator/
            |-- platformio.ini
            `-- src/main.cpp
```

## Current limitations

- No speech-recognition pipeline is included here yet.
- No limit switches, current sensing, or position feedback are implemented in firmware.
- Motor speed and timing are not configurable.
- The KiCad schematic appears to be only a stub at the moment.

## Next steps

Useful follow-up work for this project:

- add the voice-password controller code or document the external trigger source,
- add endstop handling so the lift cannot overrun,
- document the wiring with a real schematic,
- add photos, assembly notes, and a bill of materials.
