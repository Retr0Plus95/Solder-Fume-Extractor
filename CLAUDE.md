# Solder Fume Extractor — notes for Claude

A bench solder-fume extractor. Two Corsair 120 mm 4-pin PWM fans pull air through a mesh
pre-filter and an activated-carbon pad. A bare ATmega328P (programmed in an Arduino Uno,
then moved to the board) reads a 10 k pot, makes 25 kHz PWM through a 2N2222A, reads both
fans' tachometers, and shows speed, RPM, faults and filter hours on a 1602 I2C LCD.

**Status:** drawing set **Rev E**, firmware **v1.3** (pot on A2). The owner's prototype
("The Mega Extractor 5000"; the name may change) is **finished and working** as of
2026-11-14: their own placement on a 7×9 cm board, not sheet 4's. See "Owner's build" below
and `docs/Build_Log.md`.

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
- Parts they actually have and fitted:
  - **D1 = 1N5402G** (3 A, 200 V, DO-201AD). Its legs are ~1.3 mm thick, so the holes
    need opening up from the standard 1.0 mm.
  - **C1 = two 100 µF 50 V electrolytics in parallel** (C1A, C1B).
  - **F1 = 2 A slow-blow** (fitted by 2026-11-14).
  - **U1 = L7805CV** on the prototype instead of the MP1584 buck. Fine for the logic; the
    USB port (sheet 3, not built) needs the buck module back.
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
| `Wire.setWireTimeout(25000, true)`, and the PWM set up **after** the LCD starts | Wire waits forever by default. A stuck I2C bus must never leave the fans stopped: with the timeout it can't hang, and if the display init ever did hang, the PWM pin is still floating, so the fans run at 100 %. |
| Pot dead band: on at 7 %, off at 4 % | A knob resting on the edge would otherwise flick the fans on and off, each time with a full-power start burst. |
| Pot on **A2 (pin 25)**, not A0 | The prototype chip's A0 input was damaged by early power faults. A2 works on any chip, so the whole design moved there (Rev E) and the firmware matches the prototype. |
| Drawings show the **recommended** circuit; the prototype's differences live in `docs/Build_Log.md` and the README's as-built table | The prototype lacks R12/R13 and C4 and uses a 7805. Don't delete those parts from the drawings to "match" it: they protect the next builder. |

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
images/photos/                    README photos and GIF clips of the finished prototype
docs/Build_Log.md                 the prototype: faults found, as-built differences, loose ends
*.stl                             the four printed enclosure parts (owner's own models)
check.sh                          runs everything; it must end "ALL CHECKS PASSED"
```

**`images/SFE-*.png` are plain copies of the PNGs in `docs/`** for the README. After
re-exporting a drawing (or after `check.sh` redraws SFE-04), copy it over the matching
file in `images/` too, or the README shows a stale sheet.

**Photos in the repo are cropped to the hardware.** The owner's phone clips carry
stickers, a location tag and, in one, a person on a monitor behind the board: crop those
out, and never publish frames showing a real person's photo. `my-board/` holds the owner's
own board photos and is never committed (see `.gitignore`).

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
6. Don't claim anything works on hardware beyond what the owner has reported (see
   "Owner's build"). Nothing has been bench-tested by us.

## Verified vs not verified

- **Verified:**
  - Real avr-gcc 7.3 build against ArduinoCore-avr: 0 warnings at `-Wall -Wextra`,
    10.1 KB flash, 716 B RAM, builds at 16 and 12 MHz.
  - v1.3 built on the owner's PC with the arduino-cli inside the Arduino IDE 2 (AVR core
    1.8.8, their installed LiquidCrystal I2C): 0 sketch warnings, 8,836 B flash, 526 B RAM.
    `check.sh` runs this build. The host logic tests need g++, which this PC doesn't have:
    the v1.3 dead-band test was checked in a Python model of the same code.
  - The timer TOP value in the binary.
  - The pot mapping over all 1024 positions, every LCD string length, the
    stall/restart logic, and all 10,201 ramp transitions.
  - The layout's netlist, and its physical fit using typical part sizes.
- **Reported by the owner on their build (2026-11-13/14):** the chip runs on the board at
  16 MHz, the LCD answers at 0x27; the knob sets both fans' speed and the tachs read back
  (64 % → 1800 and 1830 rpm, photo in `images/photos/running-lcd.jpg`). With the tach
  lines unconnected the stall check showed `!BOTH FANS STOP` and the fans stayed at
  100 %, as designed.
- **Not verified:**
  - The stall auto-restart and the watchdog reset on real hardware.
  - The buck module's real pad positions (they vary; the module is taped down and wired).
  - The exact body sizes of the owner's parts.
  - Upload, bootloader and watchdog behaviour on their Uno.

## Owner's build (finished 2026-11-14)

Full record in `docs/Build_Log.md`. In short, it differs from the drawings by: an
**L7805CV** for U1 (first fitted backwards, so the 5 V rail and C2, rated 10 V, saw about
11.8 V); **no R12/R13** (tach lines go straight to pins 4/5 with their 10 k pull-ups);
**no C4**; the pot on **A2** because the chip's A0 is damaged; the chip in female header
strips. Loose ends they listed: solder the pot jumper to leg 25, clean flux between legs
23 and 24, recheck the 7805 (read 5.4 V once), the knob's floor gives ~30 % (pot bottom
end at 0.55 V: check for a shared ground with fan current, or a bad joint), fit R12/R13,
keep the 7805 clear of the PLA case, a fresh ATmega328P when convenient.

## Good next steps

1. Work through the loose ends above (the build log has them as a checklist).
2. Add the project to the owner's website projects page (next thing they asked for).
3. If they build the USB port: put the MP1584 back for U1 (the 7805 can't supply it) and
   trim it to 5.10 V.
4. Optional, using free pins: a fault buzzer on D7, a thermistor on A3.
