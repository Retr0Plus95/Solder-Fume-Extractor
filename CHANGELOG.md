# Changelog

## Unreleased

### The prototype is finished — drawing set Rev E (2026-11-15)
- The first unit works: the knob sets both fans and the LCD reads them back (64 % →
  1800 and 1830 rpm). [`docs/Build_Log.md`](docs/Build_Log.md) records the seven faults
  found during bring-up, how the prototype differs from the drawings, its loose ends and
  the lessons.
- **The speed knob moved from A0 (pin 23) to A2 (pin 25)**, after the prototype chip's A0
  input was damaged. Firmware line 94 is `PIN_POT = A2` (the firmware stays v1.3, matching
  what is on the prototype); sheets 1, 2 and the pot detail, the perfboard layout and the
  Maker Forge project file all follow. Build an early board with the pot on pin 23? Move
  the wire to pin 25, or set `PIN_POT` back to `A0`.
- The project has a name: **Sir Sucks-a-Lot** (it was "The Mega Extractor 5000" for a day).
  The README title and the poster carry it; the repository keeps its name, so links still work.
- The whole project is MIT licensed, the 3D-printed case (`.stl` files) included; the
  README says so.
- README: photos and short clips of the finished build, an as-built table, the status
  changed to finished. The photos are cropped to the hardware.
- Build guide: points to the build log up front; pin table and free-pin list updated.
- `check.sh` now runs `build_avr.sh` through `bash`, and both scripts are marked
  executable in git, so the real AVR build also runs from a fresh clone on Linux or macOS.

### First power-up (the owner's build, 2026-11-13)
- Build guide fault table: `!BOTH FANS STOP` while the fans spin means R12 / R13 (the
  4.7 kΩ links from the tach lines to chip pins 4 and 5) are missing or a tach wire is
  loose. Fans that ignore the pot can also be a PWM wire that isn't connected. The
  full-speed restart bursts in the first 15 s are normal.
- Build guide: the MP1584's trimmer is multi-turn; notes on fitting an L7805 instead
  (fine for the 5 V side, not for the USB port).

### Firmware v1.3
- The LCD can no longer stop the fans. A stuck I2C bus (loose display wire, bad joint,
  noise) used to hang the chip forever, and in setup that happened with the PWM already
  at 0 % and the watchdog still off. Every I2C transfer now gives up after 25 ms, and
  the PWM is only set up after the display has started, so a hang leaves the fans at
  100 %.
- The pot has a small dead band: the fans start at 7 % and stop at 4 %, so a knob resting
  on the edge can't flick them on and off with a full-power start burst each time.
- Build guide: a factory-fresh ATmega328P runs at 1 MHz (internal 8 MHz divided by 8),
  not 8 MHz, until the Uno bootloader sets the fuses. Corrected in §5 and the fault table.
- `check.sh` now finds the arduino-cli inside the Arduino IDE 2, so the real firmware
  build runs on Windows, and it fails if the sketch itself has any warning.

### Drawing set Rev D
- Perfboard layout (sheet 4) redone. The Rev C layout was wired correctly, but a new
  physical-fit check found 62 problems: two legs in one hole (3 places), six resistors
  drawn too short to lie flat or stand up, the buck module drawn too small with R4
  under it, D1 overlapping C1, R5 under the socket, wires drawn across other joints.
- Fan headers moved to the top edge, so fan current stays off the logic ground.
- Buck module now taped down and wired to the rails with four short wires.
- D1 is now a 1N5402G (3 A, DO-201AD), still a reverse shunt. Its legs need 1.3–1.5 mm holes.
- C1 is now two 100 µF 50 V electrolytics in parallel (C1A, C1B).
- Build guide: D1 diode-test check before first power-up; buck set to 5.00 V until the
  USB port is fitted; LCD pull-up troubleshooting; corrected library author
  (Frank de Brabander).
- Sheet 3: stale fan-inrush text corrected for the v1.2 soft ramp.

### Tooling
- `my-board/` is ignored by git: photos of your own board for Bench's "Your board" view stay on
  your computer.
- The project file now says how each resistor is mounted (`mount`: `stand` or `flat`), by the
  same rule as the layout checker, so Bench no longer says R4 stands when it lies flat.
- `forge-project.json` now also holds the board (every part's holes, the buses, links, bridges and
  connections) and the build order with the reason for each step, written from `board.py` and the
  new `hardware/layout/build_steps.py` by `export_board.py`. `check.sh` runs it, so Bench always
  shows the checked layout.
- `forge-project.json`: the project file for Maker Forge Bench (the soldering drawing viewer).
  It lists the six sheets, and all 37 parts with value, job ("why"), and which way round the
  polarised ones go.
- `hardware/layout/`: layout as data (`board.py`), electrical + physical checker
  (`pcb.py`), renderer for sheet 4, and a self-test that feeds it 8 broken boards.
- `firmware/tests/test_logic.cpp`: pot mapping, LCD string widths, stall/restart
  logic, ramp.
- `firmware/tools/build_avr.sh`: real avr-gcc build against the official Uno core.
  First real build: 0 warnings, 10.1 KB flash, 716 B RAM; 25 kHz confirmed in the binary.
- Sketch moved into `firmware/SolderFumeExtractor/` (Arduino IDE folder rule).
- Firmware header comments corrected; no code change (binary identical).
- `render.py` now writes UTF-8, so `check.sh` no longer crashes on Windows at the sheet 4 redraw.

### README and printed parts
- README shows the drawings and a picture of the four 3D-printed parts with their sizes; the repository layout now matches the files.
- The four enclosure STL files and an MIT LICENSE added.
- README drawing copies in `images/` refreshed to Rev D.

### Initial

- Initial project repository created from the SFE-2026 Rev C drawing set and Firmware v1.2.
- Added firmware, build guide, schematic/reference drawings and perfboard documentation.
