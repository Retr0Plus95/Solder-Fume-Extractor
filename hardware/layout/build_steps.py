# -*- coding: utf-8 -*-
"""The build order for the Rev D perfboard, with the reason for each step (Build Guide §13).

export_board.py writes these into forge-project.json's "build" section, and refuses to if a step
names a part board.py doesn't have, or if a board part is in no step or in two. Edit the text here,
never in the JSON.
"""

STEPS = [
    dict(id="buses", title="Bare-wire buses", what=["buses"], parts=[], why=(
        "Solid tinned wire along rows 2, 4, 6, 17, 18 and 19, plus the short 0 V spur on row 8, "
        "soldered at every hole. These are the rails everything else connects to: +12 V on row 2, "
        "0 V on row 4, +5 V on row 6. They go in first while the board is empty, so the wire lies "
        "flat and every hole is easy to reach.")),
    dict(id="links", title="Insulated links", what=["links"], parts=[], why=(
        "The insulated wires from the wire list, ticked off one at a time. They go in before the parts, "
        "while there's room to bend each wire around other joints. The lines on sheet 4 show which "
        "holes join, not the exact path. Where a link crosses a bare bus, keep the iron off the insulation.")),
    dict(id="bridges", title="The two solder bridges", what=["bridges"], parts=[], why=(
        "Two small solder blobs joining neighbouring holes, at 26,8 to 26,9 and 29,8 to 29,9. Each one joins "
        "a tach pull-up (R8, R9) to its series resistor (R12, R13): that's the point where a fan's speed "
        "signal arrives. R8/R12 and R9/R13 go into those same holes, so if solder would fill the holes, "
        "make the bridges after fitting those resistors instead.")),
    dict(id="socket", title="The DIP socket (notch LEFT)", what=[], parts=["U2"], why=(
        "Solder the socket, not the chip. It sits flat and gives every other part a fixed place to line up "
        "with. The notch goes LEFT, as on sheet 4. The chip goes in only after the power-up checks.")),
    dict(id="power", title="The power strip", what=[], parts=["J0", "D1", "C1A", "C1B", "U1", "C2", "C3", "C10", "J2", "J3"], why=(
        "Power in, protection and the 5 V supply, along the top. D1 is a reverse-polarity shunt: its band "
        "(cathode) goes to the +12 V row, so a backwards supply blows the fuse instead of the circuit. "
        "C1A, C1B, C2 and C10 go stripe (−) to the 0 V row. The fan headers sit beside the +12 V and 0 V "
        "rows so fan current goes straight back to the input without passing through the logic ground. "
        "The buck module sits on foam tape, wired to the rails with four short wires: read its own "
        "silkscreen for IN+, IN−, OUT+ and OUT−.")),
    dict(id="mcu", title="The chip's support parts", what=[], parts=["R4", "C6", "C7"], why=(
        "R4 holds the reset pin (pin 1) high, so the chip runs instead of staying in reset. C6 and C7 are "
        "the crystal's load capacitors, pins 9 and 10 to 0 V: without them the clock may not start.")),
    dict(id="fans", title="Fan drive and tach", what=[], parts=["R8", "R12", "R9", "R13", "R7", "R5", "Q1", "R6"], why=(
        "Each fan's speed (tach) wire, pin 3 of its header, gets a 10 k pull-up to +5 V (R8, R9) because "
        "the fan can only pull it low, and a 4.7 k resistor into the chip (R12 to pin 4, R13 to pin 5) that "
        "protects the pin if a fan lead ever touches +12 V. Q1 switches both fans' PWM line, driven through "
        "R5 from pin 15; R7 pulls that line up, and R6 holds Q1 off so the fans run at full speed if the "
        "chip is dead or in reset (fail-safe). Most resistors stand upright: body over one hole, the leg "
        "bent over into the other.")),
    dict(id="panel", title="The panel side", what=[], parts=["R2", "R3", "C4", "J5", "J4", "J6"], why=(
        "Headers along the bottom edge: J5 to the front panel (both LEDs and the speed knob), J4 to the "
        "LCD, J6 to push-button SW2. R2 and R3 limit the LEDs' current; C4 smooths the knob's voltage into "
        "pin 25 (A2) so the reading doesn't jitter.")),
    dict(id="underside", title="The underside parts", what=[], parts=["C5", "C8", "Y1", "C9"], why=(
        "C5 across socket pins 7 and 8, C8 across 21 and 22, Y1 across 9 and 10 (legs bent inward), and C9 "
        "from pin 20 to the 0 V spur hole directly above it. They go underneath because that's the only "
        "way to keep their legs short, which decoupling capacitors and the crystal need.")),
    dict(id="checks", title="Power-up checks, before the chip", what=[], parts=[], why=(
        "Build Guide §7: power the buck module alone and set it to 5.00 V with a meter; check there's no "
        "short between the rails; diode-test D1; only then plug in the chip, notch left, and connect "
        "the fans.")),
]
