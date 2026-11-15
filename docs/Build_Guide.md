# Solder Fume Extractor — Build Guide
**Drawing set SFE-2026, Rev E · Firmware v1.3** · Sheet 1 schematic · Sheet 2 reference · Sheet 3 USB port · Sheet 4 perfboard layout · `SolderFumeExtractor.ino`

> **The first unit is built and working.** It differs from these drawings in a few places (an L7805 instead of the buck module, no R12/R13 or C4 yet, its own board layout). See [the build log](Build_Log.md) for those differences and the seven faults found while bringing it up — read its *Lessons* before you power your own board.

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
| D1 | **1N5402G** (3 A, 200 V, DO-201AD) | 1 | Reverse-polarity **shunt**, band to +12 V. A 1N4007 also works. |
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
| C1A, C1B | 100 µF 50 V **ELECTROLYTIC** (polarised), in parallel = 200 µF | 2 |
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
| 23 | PC0 | A0 | spare (the pot was here until Rev E) |
| 24 | PC1 | A1 | spare |
| 25 | PC2 | A2 | **POT** — RV1 wiper, C4 100 nF to GND |
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
| +12 V rail | C1A + and C1B +, **D1 cathode (band)**, U1 IN+, fan A pin 2, fan B pin 2 |
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

> The fuse setting matters more than the bootloader. A factory-fresh chip runs on its
> internal oscillator divided by 8, so at **1 MHz**, and ignores your crystal: the PWM
> would come out at about 1.6 kHz (a loud whine) and every timing in the sketch would
> be 16 times too slow. Burning the Uno bootloader once fixes the fuses permanently
> (external 16 MHz crystal, no divide-by-8). A chip taken out of an Uno is already set.

Library needed: **LiquidCrystal I2C by Frank de Brabander** — in the Arduino IDE open
*Tools → Manage Libraries*, search `LiquidCrystal I2C`, and install the one with that
author. (Earlier versions of this guide named the wrong author, which would have sent
you looking for an entry the Library Manager doesn't show.)

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
   Then the **D1 check**: meter on diode test, red probe on the +12 V row, black on
   the 0 V row. The reading should start low and **climb to OL** as C1A/C1B charge.
   A steady 0.5–0.7 V means D1 is in backwards — it would short your supply the
   moment you switch on.
3. Fit U2, the crystal, the caps and the LCD. Power up. You should see the splash
   screen for 2 seconds and both fans at full speed.
4. If the screen is lit but blank, adjust the contrast pot on the I²C backpack. If it
   is completely dead, change `LCD_ADDRESS` to `0x3F` and re-upload.
5. Turn RV1 fully down — fans should stop, screen shows `STOPPED`. Turn up slowly:
   the fans ramp up to full over about a second, hold briefly, then settle to the
   knob setting. RPM should track the demand.
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
| Fans always at full, ignore the pot | D9 not reaching Q1's base, Q1 in backwards (E/C swapped), or the fans' PWM wire (pin 4, blue) not reaching Q1's collector: a fan runs flat out when its PWM wire is left open. Check: the DC voltage on the PWM wire should fall as you turn the pot down (a meter shows the average, about duty × 5 V) |
| Fans run full in bursts for the first 15 s or so | Normal while the chip can't hear a fan: it tries three 2.2 s full-speed restarts, then shows the fault and follows the pot again |
| `!BOTH FANS STOP` or `!FAN A NO SIGNAL`, but the fans spin | No speed signal reaches the chip. R12 / R13 (4.7 kΩ) missing between the fan's tach line (fan pin 3, after R8 / R9) and chip pin 4 / pin 5, or a loose tach wire. Without them pins 4 and 5 float, and touching the wires makes the reading jump |
| Fans never spin | PWM line stuck low — Q1 shorted C–E, or R5 shorted |
| Fans buzz or whine audibly | PWM isn't 25 kHz: the chip isn't running on the 16 MHz crystal. A factory-fresh chip runs at 1 MHz until the Uno bootloader is burned (see §5) |
| RPM reads 0 but the fan spins | Missing tach pull-up (R8/R9), or SENSE and PWM wires swapped |
| RPM reads roughly double | Fan puts out 4 pulses/rev — set `PULSES_PER_REV` to 4 |
| Backlight goes dark after 30 s | Normal — nudge the pot to wake it |
| LCD shows garbage or freezes now and then | Most PCF8574 backpacks have their own 4.7 kΩ pull-ups on SDA/SCL. If yours doesn't, add 4.7 kΩ from SDA to +5 V and from SCL to +5 V |
| Speed jumps around | Missing C4 on the pot wiper, or pot wiring runs next to the fan leads |
| LCD blank / garbled | Wrong I²C address, contrast pot, or SDA/SCL swapped |
| Fuse blows the moment you power up | Supply polarity reversed — D1 did its job |
| Fuse blows only sometimes at power-on | Fast-blow fitted; it must be slow-blow (T-rated) |
| U1 chirps and won't start | Too much output capacitance — reduce C11 |
| U1's output doesn't move when you turn its trimmer | The MP1584's trimmer is multi-turn: it can take 10 or more turns before the voltage changes. Set it with the module powered on its own and a meter on OUT, before anything else is connected |
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
- **Free pins** D4, D7, D8, D10–D13, A0, A1 and A3 are broken out for a filter-reset button,
  a buzzer on fault, or a thermistor.
- **An L7805 instead of U1:** it can power the 5 V side alone. Facing its printed side,
  the legs are IN, GND, OUT. It drops 7 V as heat, about 0.5 W at this load: warm, fine
  without a heatsink. It can't power the USB port (that would be 7 W), so go back to a
  buck module before building sheet 3. If it's ever fitted backwards, the 5 V rail sees
  nearly 12 V: check C2 (10 V) for bulging and replace it if in doubt.


---

## 11. Firmware features

**Soft ramp (v1.2).** Commanded duty slews at 3 % per 25 ms rather than stepping, so
the fans ease up over about 850 ms instead of being slammed to 100 %. That spreads out
the current the fans draw while they accelerate. Two things it does *not* cover:

- For the first ~70 ms after you flip SW1, the chip hasn't booted yet, so the fans
  see full demand. That is the fail-safe working (a dead controller means full
  extraction), and it is far too short to matter to a slow-blow fuse.
- The inrush into C1A/C1B when you flip SW1 lasts a few milliseconds and happens
  before any code runs. That is what a slow-blow (T-rated) fuse is for. With 200 µF
  instead of the original 470 µF this inrush is smaller than before.

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

Wire the 1N5402G **across** the rail, cathode (banded end) to +12 V, anode to 0 V,
downstream of F1. Normally it is reverse-biased and does nothing at all: no current,
no heat, **no voltage drop**, so the fans get the full 12 V. Connect the supply
backwards and it conducts, F1 clears, and everything downstream is protected.

The trade-off versus a series Schottky is that after a reversal you replace a fuse
rather than just unplugging. In exchange you lose no voltage in normal use, which
with two fans is the better deal. Note that a 12 V 2 A adapter will current-limit
rather than dump 20 A, so the fuse may take a moment to open — the diode handles
that easily (the 1N5402G is rated for a 200 A surge).

**The 1N5402G's legs are about 1.3 mm thick.** Ordinary perfboard holes are 1.0 mm,
so they probably won't go in. Open those two holes up with a 1.3–1.5 mm drill bit,
turning it by hand. Don't file or snip the legs thinner.

**If you wired it in series instead** (in line with the +12 V feed): it still works,
because it's rated 3 A, but it drops about 0.9 V at full load and runs warm, so the
fans lose roughly 8 % of their voltage. As a shunt it costs nothing.

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

## 13. Perfboard layout (sheet 4, Rev E)

A component placement on a 32 × 20 hole board, about 81 × 51 mm. It is checked both
electrically and physically by `hardware/layout/pcb.py`.

**Perfboard, not stripboard.** Plain pad-per-hole board has no copper strips, so
there are no track cuts to get wrong. Everything is either a bare-wire bus or an
insulated link.

**What changed from Rev C.** The Rev C layout's wiring was right, but a physical-fit check found
62 problems: two legs drawn into one hole in three places, six resistors drawn three
holes long (too short to lie flat, too far to stand up), the buck module drawn far
too small with R4 underneath it, D1 overlapping C1, R5 under the socket, and wires
drawn straight across other joints. If you soldered anything from the Rev C layout,
compare it against the current layout before going further.

**What changed in Rev E.** Only the pot's wire: it now goes to chip pin 25 (A2)
instead of pin 23 (A0). Nothing else on the layout moved.

**How it's laid out**

- **Power along the top:** +12 V (row 2), 0 V (row 4), +5 V (row 6). The fan headers
  sit on the top edge beside the +12 V and 0 V rows, so fan current goes straight
  back to the input without passing through the logic ground at the bottom.
- **U1 buck module on double-sided foam tape**, with four short wires to the rails.
  Its real outline (about 22 × 17 mm) is kept clear. The pads differ between
  suppliers, so read the module's own silkscreen for IN+/IN−/OUT+/OUT−.
- **D1 (1N5402G) and the two C1 cans** stand on the far left of the top strip.
- **Most resistors stand upright.** The solid circle is where the body sits; the
  dotted line is the leg you bend over the top and down into the other hole.
- **Panel, LCD and SW2 headers** sit along the bottom edge, all logic-level.

**Build order**

1. **Bare-wire buses first**, while the board is empty: solid tinned wire along the
   row, soldered at each hole. Rows 2, 4, 6, 17, 18, 19, plus the short 0 V spur on
   row 8.
2. **The insulated links** from the wire list, ticking each off. The lines on the
   drawing show *which holes join*, not the exact path: bend each wire around other
   joints, and keep the iron off the insulation where a link crosses a bare bus.
3. **The two solder bridges:** a small blob joining two neighbouring holes, at
   (26,8)–(26,9) and (29,8)–(29,9).
4. **The DIP socket** (notch LEFT), then the other parts.
5. **The four underside parts:** C5 across socket pins 7–8, C8 across pins 21–22, Y1
   across pins 9–10 (bend its legs inward), and C9 from pin 20 to the 0 V spur hole
   directly above it. They mount underneath because that's the only way to keep the
   legs short.
6. **The power-up checks** (§7), and only then the chip.

**How it was checked.** The layout is stored as data: every pin at a hole coordinate,
plus every bus, link and bridge. The checker builds the real connectivity and compares
it with the schematic netlist. Then it checks physical fit against typical catalogue
part sizes:

- one leg per hole
- no leg under another part's body, and no two bodies overlapping
- every resistor span is something a real resistor can make (1–2 holes standing, 4+
  flat)
- no wire drawn across a joint on a different net

To prove the checker isn't just saying yes, it was fed eight deliberately broken
layouts: a backwards D1, two legs in one hole, overlapping cans, a missing wire, a
floating ground, and so on. It caught all eight.

**What it can't check:** your actual parts. The body sizes are typical, not your
specific components. If a capacitor can is bigger than 8 mm or your buck module is
larger than 22 × 17 mm, place it by eye before soldering.

---

## 14. Capacitor types — two, not interchangeable

On the schematic every capacitor is tagged under its value: **ELEC** in orange,
**CER** in green. The symbols differ too — an electrolytic has one curved plate and
a `+`, a ceramic has two straight plates. There is a legend on sheet 1.

**Electrolytic** (cylindrical cans, **polarised** — a stripe marks the negative leg):
C1A and C1B 100 µF 50 V, C2 100 µF, C10 10 µF, C11 220 µF.

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