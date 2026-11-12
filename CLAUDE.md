# Solder Fume Extractor — notes for Claude

A bench solder-fume extractor. Two Corsair 120 mm 4-pin PWM fans pull air through a mesh
pre-filter and an activated-carbon pad. A bare ATmega328P (programmed in an Arduino Uno,
then moved to the board) reads a 10 k pot, makes 25 kHz PWM through a 2N2222A, reads both
fans' tachometers, and shows speed, RPM, faults and filter hours on a 1602 I2C LCD.

**Status:** drawing set **Rev D**, firmware **v1.2**. Never yet powered on real hardware.
The owner is building it now on perfboard from sheet 4.

**Repo:** github.com/retr0plus95/Solder-Fume-Extractor, branch `main`. Claude commits and
pushes its own work once `check.sh` passes (the owner's instruction, 2026-11-12), and says what
was pushed. Ask first before anything destructive: force-pushing or rewriting history.

## Who you're working with

- A hobbyist who wants this **beginner friendly**. Explain the *why* behind changes in
  plain words. They enjoy learning how things work (they've asked about impedance,
  decoupling and how diodes behave).
- They want errors found, not reassurance. Check before claiming, and say plainly when
  something hasn't been verified.
- Windows PC with the Arduino IDE installed. Run `check.sh` from Git Bash.
- Parts they actually have and fitted (the drawings already reflect these):
  - **D1 = 1N5402G** (3 A, 200 V, DO-201AD). Its legs are ~1.3 mm thick, so the holes
    need opening up from the standard 1.0 mm.
  - **C1 = two 100 µF 50 V electrolytics in parallel** (C1A, C1B).
  - **F1 = 1 A fuse** for now. That's fine without the USB port (0.67 A steady).
    The USB port (sheet 3) waits until they get a **2 A slow-blow**.
  - 16.000 MHz two-leg crystal; 1N4007 and 1N4002 on hand; an Uno with a socketed DIP
    chip, used to program the ATmega.
- USB port: a **plain 5 V USB-A outlet for phones**, D+ strapped to D−. Not the TP4056
  board they own: that's a lithium-cell charger, and its USB-C is an *input*.
- No enclosure or case design wanted from you. For any 3D models, the owner uses their
  own app, Maker Forge.

## Design decisions — do not "fix" these

| Thing | Why it is the way it is |
|---|---|
| Timer1 in **inverting** compare mode | Q1 sinks the fans' open-collector PWM line, which inverts in hardware. Inverting mode cancels that, so `OCR1A` maps straight to duty. |
| `PWM_TOP = F_CPU / 50000` | Exactly 25.000 kHz at 16, 12 or 8 MHz. Confirmed in the real binary: `ICR1` = 0x0140 at 16 MHz. |
| R6 holds Q1 off, so the fans run **100 %** when the MCU is dead or in reset | Fail-safe: a crashed controller must never silently stop extraction. The watchdog depends on this. |
| **D1 is a reverse shunt** across the rail, band to +12 V, after F1 | It costs no voltage and makes no heat. If the supply is reversed, it conducts and F1 blows. |
| Tach pull-ups R8/R9 on the **fan side**, R12/R13 4.7 k in series to the MCU | The fan's tach output is open-collector. The series resistors protect the MCU pins if a lead touches +12 V. |
| ADC is ratiometric (pot fed from +5 V, reference = AVCC) | Rail sag doesn't shift fan speed. *Ground offset* does, which is why the fan current returns along the top 0 V row. |
| Soft ramp of 3 % per 25 ms | Spreads out the fans' acceleration current. It can't shape the first ~70 ms after switch-on: until the code runs, the PWM line floats high and the fans see full demand. That's the fail-safe. |
| Every LCD string is exactly 16 characters | A 17-character string was once silently cut short. `test_logic.cpp` enforces this. |

## Files

```
firmware/SolderFumeExtractor/SolderFumeExtractor.ino   the sketch (Board: Arduino Uno)
firmware/tests/test_logic.cpp     host tests; functions COPIED from the sketch, keep in sync
firmware/tools/build_avr.sh       real avr-gcc build against the official Uno core
hardware/layout/board.py          THE perfboard layout, as data. Edit this, never the SVG.
hardware/layout/pcb.py            electrical + physical checker
hardware/layout/render.py         draws docs/layout/SFE-04 from board.py
hardware/layout/test_checker.py   feeds the checker 8 broken boards; all must be caught
hardware/layout/board_prev.py     the old Rev C layout (62 errors), kept as a test case
hardware/layout/build_steps.py    the build order and the "why" of each step (edit the text here)
hardware/layout/export_board.py   writes forge-project.json's board + build sections (check.sh runs it)
hardware/layout/test_export.py    the export matches board.py; every board part in exactly one step
forge-project.json                Maker Forge Bench's project file: parts by hand, board + build generated
docs/schematics/                  SFE-01..03: SVG (source) + PNG
docs/layout/                      SFE-04 (generated) + SFE-D1 pot detail: SVG + PNG
docs/Build_Guide.md               the full build guide
images/                           README copies of the five drawing PNGs + SFE-parts.jpg
*.stl                             the four printed enclosure parts (owner's own models)
check.sh                          runs everything; it must end "ALL CHECKS PASSED"
```

**`images/SFE-*.png` are plain copies of the PNGs in `docs/`** for the README. After
re-exporting a drawing (or after `check.sh` redraws SFE-04), copy it over the matching
file in `images/` too, or the README shows a stale sheet.

**SFE-01..03 and SFE-D1 are hand-maintained SVG.** The Python that first generated them
was lost in a workspace reset. Edit their text directly, one change at a time, and
confirm each replacement matches exactly once. Re-export the PNG after any change.
**SFE-04 is generated:** change `board.py`, then run `check.sh`, which redraws it.

## Rules

1. Run `./check.sh` after any change. It must pass.
2. Layout changes go through `board.py`, must pass `pcb.py`, and must keep
   `test_checker.py` at 8/8.
3. Firmware changes must build with **zero warnings**. If you change logic that
   `test_logic.cpp` copies, update the copy.
4. Keep the BOM consistent across sheet 1, sheet 2, sheet 4 and guide §3. After changing
   a part, grep for its part number everywhere.
5. Add a line to `CHANGELOG.md` for anything a builder would notice.
6. Don't claim anything works on hardware. Nothing has been bench-tested yet.

## Verified vs not verified

- **Verified:**
  - Real avr-gcc 7.3 build against ArduinoCore-avr: 0 warnings at `-Wall -Wextra`,
    10.1 KB flash, 716 B RAM, builds at 16 and 12 MHz.
  - The timer TOP value in the binary.
  - The pot mapping over all 1024 positions, every LCD string length, the
    stall/restart logic, and all 10,201 ramp transitions.
  - The layout's netlist, and its physical fit using typical part sizes.
- **Not verified:**
  - Anything on real hardware.
  - The buck module's real pad positions (they vary; the module is taped down and wired).
  - The exact body sizes of the owner's parts.
  - Upload, bootloader and watchdog behaviour on their Uno.

## Good next steps

1. Install `arduino-cli`, then run `arduino-cli core install arduino:avr` and
   `arduino-cli lib install "LiquidCrystal I2C"` (author: Frank de Brabander).
   `check.sh` will use it for the real build. Upload through the Uno.
2. Bench bring-up per guide §7: buck alone at 5.00 V → short check → **D1 diode-test
   check** → chip → fans.
3. When the 2 A slow-blow arrives: build the USB port from sheet 3 and re-trim U1 to
   5.10 V.
4. Optional, using free pins: a fault buzzer on D7, a thermistor on A2.
