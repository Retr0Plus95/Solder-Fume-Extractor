# Solder Fume Extractor

A custom solder fume extractor built to provide adjustable fume capture for an electronics workbench. The system combines dual 120 mm PWM fans, real-time RPM monitoring, microcontroller-based speed control, an LCD interface, and replaceable activated-carbon filtration in a custom enclosure.

## Features

- Dual 120 mm 4-pin PWM fans
- ATmega328P controller at 16 MHz
- 25 kHz PWM fan control
- Individual fan tachometer monitoring
- 1602 I²C LCD status display
- 10 kΩ linear speed control
- Fan stall detection and automatic restart
- Watchdog fail-safe
- Activated-carbon filtration with mesh pre-filter
- Optional 5 V / 1 A USB output
- Custom enclosure / 3D-printed parts

## Project status

Hardware bring-up and testing. The electronics are being verified before the final perfboard and enclosure assembly.

## Repository layout

```text
firmware/                 Arduino firmware
hardware/                 Future PCB/perfboard source files
mechanical/               Future enclosure and 3D-print files
docs/
  Build_Guide.md          Full build and wiring guide
  schematics/             Schematic and reference drawings
  layout/                 Perfboard and potentiometer drawings
images/                   Project/reference images
```

## Documentation

See [`docs/Build_Guide.md`](docs/Build_Guide.md) for the complete wiring, bill of materials, programming, bring-up procedure, troubleshooting notes, USB output and perfboard layout information.

## Firmware

The current firmware is in [`firmware/SolderFumeExtractor.ino`](firmware/SolderFumeExtractor.ino).

The firmware uses an ATmega328P with a 16 MHz external crystal and the Arduino Uno bootloader/fuse configuration described in the build guide.

## Hardware

The design documentation includes:

- Main system schematic
- MCU pinout and programming reference
- USB output and power budget
- Verified 32 × 20 hole perfboard layout
- Speed potentiometer wiring detail

## Safety

This project is intended to reduce exposure to soldering fumes; it is not a substitute for general workshop ventilation or appropriate safety practices. Activated carbon reduces exposure but does not eliminate all contaminants. Keep the extractor close to the soldering joint and maintain room ventilation.

The project uses a 12 V supply and contains fused power wiring. Follow the build guide's power-up and continuity checks before installing the microcontroller.

## License

No open-source license has been selected yet. Until a license is added, the contents remain all rights reserved.
