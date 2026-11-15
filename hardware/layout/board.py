# -*- coding: utf-8 -*-
"""THE perfboard layout (drawing set Rev D) - checked electrically AND physically
by pcb.py. Edit this file, then run render.py; never hand-edit the SVG.

Changes from the previous layout (Rev C set)
  * D1 is a 1N5402G (3 A, DO-201AD body) standing, as a reverse shunt
  * C1 is two 100 uF 50 V electrolytics (C1A, C1B) instead of one 470 uF
  * fan headers moved to the TOP edge beside the +12 V / 0 V rails, so fan
    current never travels through the logic ground at the bottom
  * buck module (U1) sits on foam tape and is wired to the rails with four
    short wires; its real 22 x 17 mm outline is kept clear
  * every part now physically fits: one lead per hole, real lead spans,
    no part under another, no wire drawn across someone else's joint
"""

def _u2():
    u = {}
    for n in range(1, 15):  u[str(n)] = (10 + n, 13)
    for n in range(15, 29): u[str(n)] = (10 + (29 - n), 10)
    return u

def R(a, b, body="1", **k): return dict(type="res", pins={"1": a, "2": b}, body=body, **k)
def C(a, b): return dict(type="cer", pins={"1": a, "2": b})
def E(p, n, D): return dict(type="elec", pins={"p": p, "n": n}, D=D)
def H(*pins, half=1.27): return dict(type="header", pins={str(i+1): h for i, h in enumerate(pins)}, half=half)
def UND(**pins): return dict(type="underside", pins=pins)

BOARD = dict(cols=32, rows=20, spare=["2","3","13","14","16","17","18","19","23","24","26"])

BOARD["parts"] = {
    # --- power strip, rows 1-6
    "J0":  H((2,1),(3,1)),
    "D1":  dict(type="diode_stand", pins={"K":(2,2),"A":(2,4)}, body="A", D=5.4),
    "C1A": E((6,2),(6,4), 8.0),
    "C1B": E((10,2),(10,4), 8.0),
    "U1":  dict(type="module", pins={"INp":(4,2),"INn":(4,4),"OUTp":(8,6),"OUTn":(8,4)},
                keepout=(0.6,7.4,9.3,14.1)),
    "C2":  E((14,6),(14,4), 6.3),
    "C3":  C((16,6),(16,4)),
    "C10": E((18,6),(18,4), 5.0),
    "J2":  H((20,1),(21,1),(22,1),(23,1), half=2.9),
    "J3":  H((26,1),(27,1),(28,1),(29,1), half=2.9),
    # --- MCU
    "R4":  R((10,6),(10,10)),
    "U2":  dict(type="dip", pins=_u2()),
    "C5":  UND(**{"1":(17,13),"2":(18,13)}),
    "C8":  UND(**{"1":(18,10),"2":(17,10)}),
    "C9":  UND(**{"1":(19,10),"2":(19,8)}),
    "Y1":  UND(**{"1":(19,13),"2":(20,13)}),
    "C6":  C((19,14),(19,17)),
    "C7":  C((20,14),(20,17)),
    # --- tach and PWM, right block
    "R8":  R((26,6),(26,8), body="1"),
    "R12": R((26,9),(26,11), body="2"),
    "R9":  R((29,6),(29,8), body="1"),
    "R13": R((29,9),(29,11), body="2"),
    "R7":  R((31,6),(31,8), body="1"),
    "R5":  R((28,12),(28,13), body="1"),
    "Q1":  dict(type="to92", pins={"E":(27,15),"B":(28,15),"C":(29,15)}, round="up"),
    "R6":  R((28,16),(28,17), body="2"),
    # --- panel side
    "R2":  R((5,15),(5,17), body="1"),
    "R3":  R((6,15),(6,17), body="2"),
    "C4":  C((3,17),(4,17)),
    "J5":  H((2,20),(3,20),(4,20),(5,20),(6,20),(7,20)),
    "J4":  H((10,20),(11,20),(12,20),(13,20)),
    "J6":  H((15,20),(16,20)),
}

BOARD["buses"] = [
    (2,  2, 32, "P12V", "+12 V"),
    (4,  2, 32, "GND",  "0 V"),
    (6,  2, 32, "P5V",  "+5 V"),
    (8, 14, 22, "GND",  "0 V spur"),
    (17,10, 32, "GND",  "0 V"),
    (18, 2, 18, "P5V",  "+5 V"),
    (19, 2, 32, "GND",  "0 V"),
]

BOARD["links"] = [
    # power in and fan power - all on the top strip
    ((2,1),(2,2)), ((3,1),(3,4)),
    ((21,1),(21,2)), ((27,1),(27,2)),
    ((20,1),(20,4)), ((26,1),(26,4)),
    # bus ties
    ((15,4),(15,8)),                    # 0 V  rail <-> spur
    ((32,4),(32,17)), ((32,17),(32,19)),# 0 V  rail <-> lower 0 V buses
    ((9,6),(9,18)),                     # +5 V rail <-> lower +5 V bus
    # fan tach and PWM
    ((22,1),(22,3),(25,3),(25,7),(26,8)),  # J2 SENSE -> R8/R12 node
    ((28,1),(28,7),(29,8)),             # J3 SENSE -> R9/R13 node
    ((23,1),(23,3),(30,3),(30,7),(31,8)),  # J2 PWM -> R7
    ((29,1),(30.5,1.6),(30.5,7),(31,8)),   # J3 PWM -> R7
    ((29,15),(30,14),(30,9),(31,8)),    # Q1 C -> R7
    # tach into the MCU, under the socket
    ((26,11),(14,11),(14,13)),          # R12 -> pin 4
    ((29,11),(27,12),(15,12),(15,13)),  # R13 -> pin 5
    # PWM drive
    ((24,10),(27,10),(28,12)),          # pin 15 -> R5
    ((28,13),(28,15)),                  # R5 -> Q1 base
    ((28,15),(28,16)),                  # Q1 base -> R6
    ((27,15),(27,17)),                  # Q1 E -> 0 V
    # MCU support
    ((10,10),(11,13)),                  # R4 -> pin 1
    ((19,13),(19,14)), ((20,13),(20,14)),  # pins 9/10 -> C6/C7
    ((17,13),(17,18)),                  # pin 7 VCC -> +5 V
    ((18,13),(18,17)),                  # pin 8 GND -> 0 V
    ((19,10),(20,6)),                   # pin 20 AVCC -> +5 V
    ((17,10),(17,8)),                   # pin 22 GND -> spur
    # LEDs and pot
    ((21,13),(21,16),(5,16),(5,15)),    # pin 11 -> R2
    ((22,13),(22,15),(6,15)),           # pin 12 -> R3
    ((14,10),(14,9),(3,9),(3,17)),      # pin 25 (A2) -> C4 / pot
    ((5,17),(5,20)), ((6,17),(6,20)),
    ((3,17),(3,20)), ((4,17),(4,20)), ((4,20),(4,19)),
    ((7,20),(7,19)), ((2,20),(2,18)),
    # LCD and SW2
    ((12,10),(12,11),(12.5,12),(12.5,14),(12,15),(12,20)),  # pin 27 SDA
    ((11,10),(10.5,11),(10.5,14),(13,16),(13,20)),          # pin 28 SCL
    ((10,20),(10,19)), ((11,20),(11,18)),
    ((16,13),(15,20)), ((16,20),(16,19)),
]
BOARD["bridges"] = [((26,8),(26,9)), ((29,8),(29,9))]

BOARD["nets"] = {
 "P12V":[("J0","1"),("D1","K"),("C1A","p"),("C1B","p"),("U1","INp"),("J2","2"),("J3","2")],
 "GND":[("J0","2"),("D1","A"),("C1A","n"),("C1B","n"),("U1","INn"),("U1","OUTn"),
        ("C2","n"),("C3","2"),("C10","n"),("C5","2"),("C8","2"),("C9","2"),("C6","2"),
        ("C7","2"),("C4","2"),("Q1","E"),("R6","2"),("U2","8"),("U2","22"),
        ("J2","1"),("J3","1"),("J4","1"),("J5","3"),("J5","6"),("J6","2")],
 "P5V":[("U1","OUTp"),("C2","p"),("C3","1"),("C10","p"),("C5","1"),("C9","1"),("R4","1"),
        ("R7","1"),("R8","1"),("R9","1"),("U2","7"),("U2","20"),("J4","2"),("J5","1")],
 "RST":[("U2","1"),("R4","2")],
 "TACHA_F":[("J2","3"),("R8","2"),("R12","1")], "TACHA":[("R12","2"),("U2","4")],
 "TACHB_F":[("J3","3"),("R9","2"),("R13","1")], "TACHB":[("R13","2"),("U2","5")],
 "SW2N":[("U2","6"),("J6","1")],
 "X1":[("U2","9"),("Y1","1"),("C6","1")], "X2":[("U2","10"),("Y1","2"),("C7","1")],
 "LEDA":[("U2","11"),("R2","1")], "LEDA_O":[("R2","2"),("J5","4")],
 "LEDB":[("U2","12"),("R3","1")], "LEDB_O":[("R3","2"),("J5","5")],
 "PWMCTL":[("U2","15"),("R5","1")], "Q1B":[("R5","2"),("Q1","B"),("R6","1")],
 "PWMBUS":[("Q1","C"),("R7","2"),("J2","4"),("J3","4")],
 "POT":[("U2","25"),("C4","1"),("J5","2")],
 "SDA":[("U2","27"),("J4","3")], "SCL":[("U2","28"),("J4","4")],
 "AREF":[("U2","21"),("C8","1")],
}
