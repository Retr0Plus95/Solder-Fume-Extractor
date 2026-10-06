# Solder Fume Extractor — Build Guide
**Drawing set SFE-2026, Rev C · Firmware v1.2** · Sheet 1 schematic · Sheet 2 reference · Sheet 3 USB port · `SolderFumeExtractor.ino`

---

## 1. What it does

Two 120 mm Corsair 4-pin fans pull fume through a mesh pre-filter and an activated
carbon pad. A stripped-down ATmega328P reads a 10 kΩ pot, generates a 25 kHz PWM
signal, and drives both fans through a single 2N2222A. Both tachometer outputs are
read back on interrupts, so the screen shows real RPM rather than just the demand.

| Spec | Value |
|---|---|
| Supply | 12 V DC, 2 A (barrel 5.5/2.1 mm) |
| Logic rail | 5.00 V from an MP1584EN buck module |
| PWM | 25.0 kHz, Timer1 phase-correct, TOP derived from F_CPU |
| Speed range | Off, then 25 %–100 % over the pot travel |
| Tach resolution | 2 pulses/rev, 1 s window (±30 rpm) |
| Fault detection | < 250 rpm while driven for 3 s |
| Idle current | ~110 mA at 12 V (fans off, backlight on) |
| USB output | 5 V, 1 A max, BC1.2 dedicated charging port |

---

## 2. Safety — read this first

- **Rosin/colophony fume is a respiratory sensitiser.** Repeated exposure causes
  occupational asthma, and once you're sensitised it is permanent. A carbon filter
  reduces exposure; it does not eliminate it. Keep the room ventilated too.
- Position the intake **100–150 mm from the joint**. Capture velocity falls off with
  the square of distance — at 300 mm the unit is doing almost nothing.
- **The activated carbon pad is what actually removes the fume.** A bare fan just
  redirects it. Do not run the unit without one.
- Use a proper enclosed 12 V PSU. Do not build a mains-side supply into the box
  unless you already know how to do that safely.
- The USB output is live only when SW1 is on. That is deliberate.
- The fuse F1 is not optional. A shorted fan lead on an unfused 2 A supply will
  melt wiring insulation.

---

## 3. Bill of materials

### Semiconductors & modules
| Ref | Part | Qty | Notes |
|---|---|---|---|
| U1 | MP1584EN buck converter module | 1 | Or LM2596. 7805 + heatsink also works. |
| U2 | ATmega328P-PU + 28-pin DIP socket | 1 | Socket strongly recommended |
| Q1 | 2N2222A NPN, TO-92 | 1 | Note the pinout — see §6 |
| D1 | **1N4007** or 1N4002 | 1 | Reverse-polarity **shunt**, cathode to +12 V |
| D2, D3 | 5 mm green LED | 2 | Fan A / Fan B status |
| Y1 | 16.000 MHz HC-49S crystal | 1 | |
| — | LCD 1602A + PCF8574 I²C backpack | 1 | Address 0x27 or 0x3F |

### Passives
| Ref | Value | Qty |
|---|---|---|
| R2, R3 | 330 Ω 1/4 W | 2 |
| R4, R6, R7, R8, R9 | 10 kΩ 1/4 W | 5 |
| R5 | 1 kΩ 1/4 W | 1 |
| R12, R13 | 4.7 kΩ 1/4 W | 2 |
| RV1 | 10 kΩ **linear** potentiometer + knob | 1 |
| C1 | 470 µF 25 V **ELECTROLYTIC** (polarised) | 1 |
| C2 | 100 µF 10 V **ELECTROLYTIC** (polarised) | 1 |
| C3, C5, C8, C9 | 100 nF **CERAMIC** | 4 |
| C6, C7 | 22 pF **CERAMIC** | 2 |
| C10 | 10 µF **ELECTROLYTIC** (polarised) | 1 |

### Mechanical & other
2 × Corsair 120 mm 4-pin PWM fan · 2 × 4-pin fan header (or cut the fan leads and
solder direct) · F1 **2 A slow-blow** fuse + panel holder · J5 USB-A socket ·
F2 1.1 A hold PTC · C11 220 µF 10 V ELECTROLYTIC · SW1 illuminated rocker, 12 V lamp,
19.2 × 13 mm cutout · 12 V 2 A PSU · DC barrel jack · activated carbon pad
(120 × 250 mm) · aluminium mesh pre-filter · enclosure, 3 mm acrylic or aluminium
panel · M4 fan screws · hookup wire, 20 AWG for power, 26 AWG for signals.

---

## 4. Complete connection table

### ATmega328P (DIP-28) — every pin accounted for

On sheet 1 the **amber** label outside each pin is the Arduino pin name; the text
inside the package is the AVR port name and the physical DIP pin number. Sheet 2's
pinout map shows both as well — amber for the Arduino name, blue for the net.
| Pin | Name | Arduino | Connects to |
|---|---|---|---|
| 1 | PC6 / RESET | — | R4 10 kΩ → +5 V; FTDI DTR via 100 nF (programming only) |
| 2 | PD0 / RXD | D0 | FTDI TX (programming only) |
| 3 | PD1 / TXD | D1 | FTDI RX (programming only) |
| 4 | PD2 | D2 | **TACH_A** — via R12 4.7 kΩ; R8 10 kΩ → +5 V at the fan side |
| 5 | PD3 | D3 | **TACH_B** — via R13 4.7 kΩ; R9 10 kΩ → +5 V at the fan side |
| 6 | PD4 | D4 | **SW2** — momentary button to GND (optional, internal pull-up) |
| 7 | VCC | — | +5 V, C5 100 nF to GND |
| 8 | GND | — | 0 V |
| 9 | XTAL1 | — | Y1 + C6 22 pF → GND |
| 10 | XTAL2 | — | Y1 + C7 22 pF → GND |
| 11 | PD5 | D5 | **LED_A** → R2 330 Ω → D2 anode |
| 12 | PD6 | D6 | **LED_B** → R3 330 Ω → D3 anode |
| 13 | PD7 | D7 | spare |
| 14 | PB0 | D8 | spare |
| 15 | PB1 / OC1A | D9 | **PWM_CTL** → R5 1 kΩ → Q1 base |
| 16 | PB2 | D10 | spare |
| 17 | PB3 | D11 | spare (MOSI, ISP) |
| 18 | PB4 | D12 | spare (MISO, ISP) |
| 19 | PB5 | D13 | spare (SCK, ISP) |
| 20 | AVCC | — | +5 V, C9 100 nF to GND |
| 21 | AREF | — | C8 100 nF to GND (nothing else) |
| 22 | GND | — | 0 V |
| 23 | PC0 | A0 | **POT** — RV1 wiper, C4 100 nF to GND |
| 24 | PC1 | A1 | spare |
| 25 | PC2 | A2 | spare |
| 26 | PC3 | A3 | spare |
| 27 | PC4 / SDA | A4 | LCD backpack SDA |
| 28 | PC5 / SCL | A5 | LCD backpack SCL |

### Everything else
| From | To |
|---|---|
| DC jack + | F1 → SW1 common |
| SW1 output | +12 V rail |
| SW1 lamp terminal | 0 V (lamp is internally fed from the switched side) |
| DC jack − | 0 V star point |
| +12 V rail | C1 470 µF +, **D1 cathode**, U1 IN+, fan A pin 2, fan B pin 2 |
| D1 anode | 0 V (reverse shunt — normally blocking) |
| U1 OUT+ | +5 V rail, C2, C3 |
| RV1 track ends | +5 V and 0 V (swap if the knob turns backwards) |
| D2, D3 cathodes | 0 V |
| Q1 emitter | 0 V |
| Q1 base | R5 from D9; R6 10 kΩ to 0 V |
| Q1 collector | fan A pin 4, fan B pin 4, R7 10 kΩ to +5 V |
| LCD backpack | +5 V, 0 V, SDA, SCL |

### 4-pin fan connector
Looking into the fan's connector with the retention tab uppermost, **pin 1 is the
one nearest the tab**:

| Pin | Function | Usual colour |
|---|---|---|
| 1 | GND | black |
| 2 | +12 V | yellow (sometimes red) |
| 3 | SENSE / tach | green |
| 4 | CONTROL / PWM | blue |

Corsair sometimes uses all-black sleeved leads. **Verify with a meter** before
powering up: pin 1–2 should read as the supply pair. Both fans' pin 4 wires join
together at Q1's collector — one transistor drives both.

---

## 5. Programming the ATmega328P

Three ways, pick one:

**A. Borrow an Uno — recommended.** Upload the sketch to a DIP-socket Arduino Uno
(Board: Arduino Uno), then lever the chip out and move it to your board. No fuse
changes, no programmer, no extra hardware. The Uno already runs its chip at 16 MHz
from an external crystal, which is exactly what your Y1 provides.

**B. FTDI / USB-TTL adapter.** Wire adapter TX→pin 2, RX→pin 3, GND→GND, 5 V→+5 V,
and DTR→pin 1 through a 100 nF capacitor. Upload as "Arduino Uno". This needs the
bootloader already burned.

**C. ISP.** Connect a USBasp or "Arduino as ISP" to pins 17, 18, 19, 1, 7, 8. Use
*Burn Bootloader* first (Board: Arduino Uno) to set the fuses for a 16 MHz external
crystal, then *Upload Using Programmer*.

**Crystal check before you solder.** You want a **two-legged** 16.000 MHz part
(a flat silver HC-49S can) plus two 22 pF caps. A four-pad metal block is an active
oscillator and needs different fuses — don't use it here. A 32.768 kHz watch crystal
will not run this chip at all.

`PWM_TOP` computes itself from `F_CPU`, so 16, 12 and 8 MHz all give exactly
25.000 kHz. You only change the board selection, never the constant.

> The fuse setting matters more than the bootloader. A factory chip runs on its
> internal 8 MHz oscillator and will ignore your crystal — the PWM would come out
> at 12.5 kHz and every timing in the sketch would be double. Burning the Uno
> bootloader once fixes the fuses permanently.

Library needed: **LiquidCrystal_I2C by John Rickman**, via Library Manager.

---

## 6. Notes on the 2N2222A drive stage

The Intel 4-wire spec makes the PWM input an **open-collector** input: the fan pulls
it up internally to about 5 V and expects the controller to drag it low. That is
exactly what Q1 does, and it means the signal is inverted along the way.

Rather than invert in software, Timer1 runs in **inverting compare mode**, so the two
inversions cancel and `OCR1A` maps straight to fan duty. The useful side effect is
the fail-safe: while the MCU is in reset, D9 is a floating input, R6 holds Q1 off,
the fan PWM line floats high, and **both fans run at 100 %**. A crashed controller
never silently stops extracting.

2N2222A pinout in TO-92, flat face toward you, legs down: **E – B – C** left to
right. (The metal-can 2N2222 is the opposite way round — check yours.) Q1 sinks
about 5 mA per fan; it is enormously over-specified for the job, which is fine.

---

## 7. Bring-up procedure

Do these in order. Do not skip step 2.

1. **Board unpopulated except U1.** Apply 12 V. Measure U1 output, adjust the trim
   pot to **5.10 V** (5.00 V if you are not fitting the USB port). Power down.
2. **Continuity check.** Meter across +12 V/0 V and +5 V/0 V — both should read well
   over 1 kΩ. Anything near zero means find the short now, not later.
3. Fit U2, the crystal, the caps and the LCD. Power up. You should see the splash
   screen for 2 seconds and both fans at full speed.
4. If the screen is lit but blank, adjust the contrast pot on the I²C backpack. If it
   is completely dead, change `LCD_ADDRESS` to `0x3F` and re-upload.
5. Turn RV1 fully down — fans should stop, screen shows `STOPPED`. Turn up slowly:
   the fans should kick to full for ~0.6 s, then settle. RPM should track the demand.
6. Unplug fan B while running. Within 3 seconds LED B should blink fast and the
   screen should show `!FAN B NO SIGNAL`. Plug it back in; it should clear.
7. Do all of the above with **nothing plugged into the USB port**. Add that load
   only once the fans and display are behaving.

---

## 8. Reading the display

```
Spd: 75% RUNNING     <- demand %, and state
A1450 B1480 rpm      <- measured RPM, both fans
```

| Line 1 state | Meaning |
|---|---|
| `STOPPED` | Pot at minimum, PWM at 0 % |
| `STARTUP` | 100 % spin-up burst, ~0.6 s |
| `RUNNING` | Normal |
| `MAXIMUM` | 98 % or above |
| `FAULT!` | A fan is not reporting RPM |

Line 2 shows RPM for 10 s, then the filter hour meter for 2.5 s. Running hours are
saved to EEPROM every 10 minutes and survive a power cut. At 120 hours it switches
to `CHANGE FILTER!`.

---

## 9. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Fans always at full, ignore the pot | D9 not reaching Q1's base, or Q1 in backwards (E/C swapped) |
| Fans never spin | PWM line stuck low — Q1 shorted C–E, or R5 shorted |
| Fans buzz or whine audibly | PWM isn't 25 kHz — fuses still set to internal 8 MHz oscillator (see §5) |
| RPM reads 0 but the fan spins | Missing tach pull-up (R8/R9), or SENSE and PWM wires swapped |
| RPM reads roughly double | Fan puts out 4 pulses/rev — set `PULSES_PER_REV` to 4 |
| Backlight goes dark after 30 s | Normal — nudge the pot to wake it |
| Speed jumps around | Missing C4 on the pot wiper, or pot wiring runs next to the fan leads |
| LCD blank / garbled | Wrong I²C address, contrast pot, or SDA/SCL swapped |
| Fuse blows the moment you power up | Supply polarity reversed — D1 did its job |
| Fuse blows only sometimes at power-on | Fast-blow fitted; it must be slow-blow (T-rated) |
| U1 chirps and won't start | Too much output capacitance — reduce C11 |
| D1 running hot | It is in backwards, or wired in series instead of as a shunt |
| Fan restarts 3× then shows FAULT | Genuinely obstructed, or the bearing has gone |
| Fan stops at low settings | Raise `MIN_DUTY_PCT` to 30 or 35; some fans stall below 30 % |

---

## 10. Maintenance & variations

- **Carbon pad:** replace at 120 running hours or when solder smell breaks through.
  Reset the counter by uncommenting the reset line noted at the end of the sketch,
  uploading once, then re-commenting.
- **Mesh pre-filter:** wash in warm water with detergent, dry fully before refitting.
- **3-pin fans:** they have no PWM input. Delete Q1/R5/R6/R7 and switch the +12 V
  rail with a logic-level MOSFET low-side instead — but note that PWM'ing the supply
  makes the tach signal unusable.
- **Free pins** D4, D7, D8, D10–D13, A1–A3 are broken out for a filter-reset button,
  a buzzer on fault, or a thermistor.


---

## 11. Firmware features

**Soft ramp (v1.2).** Commanded duty slews at 3 % per 25 ms rather than stepping, so
the fans ease up over about 850 ms instead of being slammed to 100 %. This lowers the
peak current the fans draw at power-on. Note what it does *not* cover: the inrush into
C1 when you flip SW1 is a separate event a few milliseconds long, and that is what a
slow-blow fuse is for.

**Watchdog timer.** If the firmware ever hangs, the chip resets after 2 s. Because a
reset leaves D9 floating and R6 holds Q1 off, the fans revert to 100 % — the safe
direction. A hung controller can no longer sit there at 30 % forever.

**Stall auto-restart.** A fan reading under 250 rpm for 3 s while driven gets a
1.5 s full-power restart attempt, up to three times, before the fault latches. A fan
briefly snagged on a cable tie now recovers by itself instead of needing a power
cycle. Turning the pot to zero clears the fault counters.

**Backlight timeout.** The LCD backlight sleeps after 30 s of no activity while the
fans are stopped, saving roughly 150 mW and extending backlight life. Any real
movement of the pot wakes it. While the fans run it stays on.

**Optional filter-reset button (SW2).** A momentary button from D4 to GND. Hold 2 s
and the filter hour meter zeroes, confirmed by `FILTER HOURS = 0` on the display.
D4 uses the internal pull-up, so if you don't fit the button the pin reads high and
nothing happens. No resistor needed.

---

## 12. USB output port (sheet 3)

A plain 5 V outlet for phones and USB gadgets, taken off the same MP1584 buck that
feeds the logic.

**Do not use a TP4056 for this.** A TP4056 is a single-cell lithium charger — its
USB-C connector is an *input*, and it sources nothing. It is the wrong device for
charging a phone. Keep it for a battery project.

### Circuit
| From | To |
|---|---|
| U1 OUT+ (+5 V) | F2 (1.1 A PTC) → J5 pin 1 VBUS |
| C11 220 µF 10 V | across VBUS and GND, **at the socket** |
| J5 pin 2 (D−) | strapped to J5 pin 3 (D+) |
| J5 pin 4 (GND) | star ground at U1 OUT−, on its own wire |

Shorting D+ to D− makes it a BC 1.2 dedicated charging port, which is what tells a
phone it may draw more than the 100 mA a data port allows. Without the strap most
devices trickle or refuse entirely. There is no data connection — this is power only.

For a USB-C socket instead, omit the strap and fit 22 kΩ from **CC1 to +5 V** and
22 kΩ from **CC2 to +5 V**. Note these are pull-*ups*: a USB-C source advertises its
capability with Rp. The 5.1 kΩ pull-downs you may have read about are what a *sink*
fits, and using them here would do nothing.

### Revised power budget
| Load | at 5 V | at 12 V | Watts |
|---|---|---|---|
| Fan A + Fan B, worst case | — | 0.60 A | 7.2 W |
| ATmega + LCD + LEDs | 0.11 A | 0.065 A | 0.78 W |
| USB port at 1.0 A | 1.00 A | 0.49 A | 5.9 W |
| **Total** | **1.11 A** | **1.16 A** | **13.9 W** |
| 12 V 2 A adapter | — | 2.00 A | 24.0 W |
| Headroom | — | 0.84 A | 42 % |

**F1 goes up from 1.5 A to 2 A slow-blow.** Steady draw is now 1.16 A, and both fans
kick to 100 % for 0.6 s at power-up, which can touch 1.6 A momentarily. A 1 A fuse
anywhere in the 12 V line will nuisance-blow.

**Put your 1 A fuse in the 5 V feed to the socket instead** — that is the right place
for it, since a shorted phone cable is the most likely fault in the whole build. A
1.1 A hold PTC is better still, because it resets itself when you unplug the cable.

### Three things that catch people

**D1 carries no current, so its rating no longer matters.** As a reverse shunt it
only conducts during a fault. This is why the series-diode current problem went away
entirely rather than needing a bigger part.

**Keep C11 at 220 µF, not larger.** A buck converter has to charge its whole output
capacitance during soft-start. With 470 µF at the socket plus C2 and C10, that's
580 µF, which at a 1 ms soft-start demands roughly 2.9 A on top of the load current —
past the MP1584's 3 A limit. The module then hiccups and may never start. 220 µF
keeps the surge near 1.2 A and is still ample for USB plug-in inrush.

**Trim U1 to 5.10 V, not 5.00 V.** The PTC at F2 has around 0.15 Ω resistance, so at
1 A the socket sees 0.15 V less than the rail. 5.10 V in means about 4.95 V at the
socket under full load, comfortably above the 4.75 V USB floor. 5.10 V is harmless
to the ATmega, which is rated to 5.5 V.

### D1 is a shunt, not a series part

Wire the 1N4007 **across** the rail, cathode (banded end) to +12 V, anode to 0 V,
downstream of F1. Normally it is reverse-biased and does nothing at all: no current,
no heat, **no voltage drop**, so the fans get the full 12 V. Connect the supply
backwards and it conducts, F1 clears, and everything downstream is protected.

The trade-off versus a series Schottky is that after a reversal you replace a fuse
rather than just unplugging. In exchange you lose no voltage in normal use, which
with two fans is the better deal. Note that a 12 V 2 A adapter will current-limit
rather than dump 20 A, so the fuse may take a moment to open — the diode handles
that easily (30 A for 8.3 ms rating).

### Two things that catch people
The MP1584 now carries 1.11 A of a realistic 2 A ceiling. It sits in the fan airflow,
which helps. Warm is fine; above about 60 °C add a heatsink.

RV1 is fed from +5 V and the ADC reference is AVCC, also +5 V, so the pot reading is
ratiometric — rail sag cancels out and fan speed will *not* drift when the USB port
loads up. What does not cancel is a **ground offset**. Run the socket's ground return
directly to the star point; if up to 1 A shares a track with the pot's ground, that
offset lands straight in your ADC reading.

No firmware change. The MCU has no knowledge of this port.

---

## 13. Perfboard layout (sheet 4)

A verified component placement on a 32 x 20 hole board, about 81 x 51 mm.

**Perfboard, not stripboard.** Plain pad-per-hole board has no copper strips, so
there are no track cuts to get wrong — the single most common beginner error on
stripboard. Everything is either a bare-wire bus or an insulated link.

**Build order:**

1. **Bare-wire buses first**, while the board is empty and easy to work on. Solid
   tinned wire laid along the row, soldered at each hole it passes. Five runs:
   +12 V (row 2), 0 V (rows 4, 17, 19), +5 V (rows 6, 18), plus a short 0 V spur on
   row 8 that feeds the AVCC decoupling.
2. **The 48 insulated links**, from the wire list. Tick each one off as you go.
3. **The DIP socket** — notch to the LEFT — then the rest of the parts.
4. **The four underside parts last:** C5 across socket pins 7 and 8, C8 across pins
   21 and 22, Y1 across pins 9 and 10 with its leads formed to 2.54 mm, and C9 from
   pin 20 up to the 0 V spur. These mount underneath, directly across the pins,
   because that is the only way to get the leads short enough to work.
5. **The chip goes in last of all**, after the smoke test.

**How this was checked.** The layout is defined as data — every component pin at a
hole coordinate, every bus, every link — and a script builds the actual electrical
connectivity from it and compares that against the schematic netlist. It confirms
all 22 nets are fully connected, that no two nets touch, that no spare pin is tied
to anything, and that no lead sits under the socket body. The first version failed:
ground came out in six separate islands. That is exactly the kind of fault this
catches and eyeballing does not.

**What is not checked** is physical fit. Lead spans are sanity-checked against
component sizes, but verify your buck module's pad spacing before committing — those
modules vary between suppliers, and U1 is drawn for pads 6 holes apart.

---

## 14. Capacitor types — two, not interchangeable

On the schematic every capacitor is tagged under its value: **ELEC** in orange,
**CER** in green. The symbols differ too — an electrolytic has one curved plate and
a `+`, a ceramic has two straight plates. There is a legend on sheet 1.

**Electrolytic** (cylindrical cans, **polarised** — a stripe marks the negative leg):
C1 470 µF, C2 100 µF, C10 10 µF, C11 220 µF.

**Ceramic** (small discs or blobs, no polarity, fit either way):
C3, C5, C8, C9 at 100 nF, and C6, C7 at 22 pF.

The split is physics, not preference. You cannot get 470 µF cheaply in a ceramic, and
electrolytics stop working well above roughly 100 kHz because of their internal
resistance and inductance. So the large ones do bulk storage at low frequency and the
small ceramics handle the fast transients. That is why C2 and C3 sit side by side
apparently doing the same job — they cover different frequency ranges.

**Two ways to get this wrong:**

A backwards electrolytic heats up and eventually vents. The stripe marks the
**negative** side.

Do not substitute 22 pF with 100 nF at the crystal. Those values are 4500× apart;
with 100 nF the oscillator will not start and the chip will appear completely dead.

---

*Drawings: `SFE-01_Schematic`, `SFE-02_Reference`, `SFE-03_USB_Port`, each as SVG
and high-resolution PNG. Firmware: `SolderFumeExtractor.ino` / `_code.txt`.*