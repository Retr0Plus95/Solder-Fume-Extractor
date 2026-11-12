# Changelog

## Unreleased

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
- `hardware/layout/`: layout as data (`board.py`), electrical + physical checker
  (`pcb.py`), renderer for sheet 4, and a self-test that feeds it 8 broken boards.
- `firmware/tests/test_logic.cpp`: pot mapping, LCD string widths, stall/restart
  logic, ramp.
- `firmware/tools/build_avr.sh`: real avr-gcc build against the official Uno core.
  First real build: 0 warnings, 10.1 KB flash, 716 B RAM; 25 kHz confirmed in the binary.
- Sketch moved into `firmware/SolderFumeExtractor/` (Arduino IDE folder rule).
- Firmware header comments corrected; no code change (binary identical).

### README and printed parts
- README shows the drawings and a picture of the four 3D-printed parts with their sizes; the repository layout now matches the files.
- The four enclosure STL files and an MIT LICENSE added.
- README drawing copies in `images/` refreshed to Rev D.

### Initial

- Initial project repository created from the SFE-2026 Rev C drawing set and Firmware v1.2.
- Added firmware, build guide, schematic/reference drawings and perfboard documentation.
