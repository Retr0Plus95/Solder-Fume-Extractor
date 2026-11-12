# -*- coding: utf-8 -*-
"""Draw a checked board (pcb.py model) as a blueprint-style SVG.
Bodies are drawn from the same shapes the checker uses, so the picture
cannot disagree with what was verified.   usage:  python3 render.py out.svg"""
import sys, pcb, board as BRD

B = BRD.BOARD
COLS, ROWS = B["cols"], B["rows"]
PX = 30                       # px per hole
K = PX / pcb.PITCH            # px per mm
X0, Y0 = 150, 232
W, H = 1560, 1536
BG, LINE, DIM, ACC = "#0b2545", "#e8f1fb", "#9fc3e3", "#ffc857"
RED, CYAN, GRN, WIRE, ORG = "#ff8f6b", "#7fd8ff", "#8fe388", "#ffc857", "#ff8f6b"
MONO, SANS = "monospace", "sans-serif"
NETCOL = {"P12V": RED, "P5V": CYAN, "GND": LINE}
o = []
def add(s): o.append(s)
def X(c): return X0 + (c - 1) * PX
def Y(r): return Y0 + (r - 1) * PX
def mx(v): return X0 + v * K
def my(v): return Y0 + v * K
def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def ln(x1, y1, x2, y2, c=LINE, w=2, op=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}" stroke-linecap="round" opacity="{op}"{d}/>')
def poly(pts, c, w, op=1.0):
    p = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    add(f'<polyline points="{p}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round" opacity="{op}"/>')
def rect(x, y, w, h, c=LINE, sw=2, fill="none", rx=0, op=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{c}" stroke-width="{sw}" opacity="{op}"{d}/>')
def circ(x, y, r, c=LINE, sw=1.4, fill="none", op=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{c}" stroke-width="{sw}" opacity="{op}"{d}/>')
def txt(x, y, s, size=13, c=LINE, anchor="start", fam=SANS, weight="normal", ls="0", op=1.0):
    add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" fill="{c}" text-anchor="{anchor}" font-weight="{weight}" letter-spacing="{ls}" opacity="{op}">{esc(s)}</text>')
def tbox(x, y, s, size, c, anchor="middle", weight="bold"):
    w = len(str(s)) * size * 0.62 + 6
    x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
    add(f'<rect x="{x0:.1f}" y="{y-size+1:.1f}" width="{w:.1f}" height="{size+4:.1f}" fill="{BG}" opacity="0.85"/>')
    txt(x, y, s, size, c, anchor, MONO, weight)

add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
add(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
rect(24, 24, W - 48, H - 48, LINE, 3); rect(36, 36, W - 72, H - 72, LINE, 1)
txt(60, 92, "SOLDER FUME EXTRACTOR — PERFBOARD LAYOUT  ·  REV D", 22, LINE, "start", SANS, "bold", "1.2")
txt(60, 118, "component side, looking down on the parts · 0.1 in grid · 32 × 20 holes ≈ 81 × 51 mm "
              "· bodies drawn to scale", 12.5, DIM, "start", MONO)
txt(60, 140, "Checked by pcb.py: every net connected, no shorts, one leg per hole, no part under another, "
              "no wire across a foreign joint.", 12.5, GRN, "start", MONO)

# board + holes
rect(X(1) - 18, Y(1) - 18, (COLS - 1) * PX + 36, (ROWS - 1) * PX + 36, DIM, 2, rx=8, op=0.55)
for c in range(1, COLS + 1):
    for r in range(1, ROWS + 1):
        circ(X(c), Y(r), 3.1, DIM, 1.1, op=0.35)
for c in range(1, COLS + 1, 2): txt(X(c), Y(1) - 72, c, 10, DIM, "middle", MONO)
for r in range(1, ROWS + 1):    txt(X(1) - 36, Y(r) + 4, r, 10, DIM, "middle", MONO)

# buses (underside, drawn first)
for (r, c1, c2, net, lab) in B["buses"]:
    col = NETCOL[net]
    ln(X(c1), Y(r), X(c2), Y(r), col, 8, 0.8)
    for c in range(c1, c2 + 1): circ(X(c), Y(r), 3.3, col, 0, col)
    if c2 == COLS: txt(X(c2) + 18, Y(r) + 4, lab, 10.5, col, "start", MONO, "bold")
    else:          tbox(X(c2) + 8, Y(r) + 4, lab, 9.5, col, "start")

# links + bridges (underside)
for L in B["links"]:
    poly([(X(a), Y(b)) for a, b in L], WIRE, 1.9, 0.7)
for L in B["links"]:
    for h in (L[0], L[-1]): circ(X(h[0]), Y(h[1]), 3.6, WIRE, 0, WIRE)
for a, b in B["bridges"]:
    ln(X(a[0]), Y(a[1]), X(b[0]), Y(b[1]), "#d8dee6", 7, 1.0)

# U1 module outline and its four wires
P = B["parts"]
u = P["U1"]; c1, r1, c2, r2 = u["keepout"]
x1, y1, x2, y2 = X(c1), Y(r1), X(c2), Y(r2)
add(f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{x2-x1:.1f}" height="{y2-y1:.1f}" rx="6" fill="#16365f" fill-opacity="0.45" stroke="{ACC}" stroke-width="2.2" stroke-dasharray="8 6"/>')
txt((x1 + x2) / 2, (y1 + y2) / 2 - 18, "U1  MP1584 buck module", 13, ACC, "middle", MONO, "bold")
txt((x1 + x2) / 2, (y1 + y2) / 2 + 2, "22 × 17 mm · on double-sided foam tape", 10.5, DIM, "middle", MONO)
txt((x1 + x2) / 2, (y1 + y2) / 2 + 20, "set to 5.00 V before wiring", 10.5, GRN, "middle", MONO)
txt((x1 + x2) / 2, (y1 + y2) / 2 + 38, "pad layout varies \u2014 read the silkscreen", 9.5, DIM, "middle", MONO)
pads = {"INp": (x1 + 18, y1 + 18, "IN+"), "INn": (x1 + 18, y2 - 18, "IN−"),
        "OUTp": (x2 - 18, y1 + 18, "OUT+"), "OUTn": (x2 - 18, y2 - 18, "OUT−")}
for pin, (px, py, lab) in pads.items():
    hx, hy = X(u["pins"][pin][0]), Y(u["pins"][pin][1])
    rect(px - 7, py - 7, 14, 14, ACC, 1.6, BG, 2)
    col = RED if pin == "INp" else (CYAN if pin == "OUTp" else LINE)
    poly([(px, py), (px, (py + hy) / 2 if py > hy else py), (hx, hy)], col, 2.4, 0.95)
    circ(hx, hy, 4, col, 0, col)
    txt(px + (12 if pin.startswith("IN") else -12), py + 4, lab, 9.5, col,
        "start" if pin.startswith("IN") else "end", MONO, "bold")

# part bodies from the checker's own shapes
LBL = {  # ref, value, colour, label anchor offset in px from body centre, text-anchor
 "D1": ("D1", "1N5402G", RED, (0, 44), "middle"),
 "C1A": ("C1A", "100µ 50V", RED, (0, 0), "middle"), "C1B": ("C1B", "100µ 50V", RED, (0, 0), "middle"),
 "C2": ("C2", "100µ", RED, (0, 0), "middle"), "C10": ("C10", "10µ", RED, (24, 4), "start"),
 "C3": ("C3", "100n", GRN, (0, -36), "middle"), "C4": ("C4", "100n", GRN, (0, 26), "middle"),
 "C6": ("C6", "22p", GRN, (-14, 4), "end"), "C7": ("C7", "22p", GRN, (14, 4), "start"),
 "R4": ("R4", "10k", ACC, (14, 4), "start"),
 "R8": ("R8", "10k", ACC, (-15, 4), "end"), "R12": ("R12", "4k7", ACC, (-15, 4), "end"),
 "R9": ("R9", "10k", ACC, (-15, 4), "end"), "R13": ("R13", "4k7", ACC, (-15, 4), "end"),
 "R7": ("R7", "10k", ACC, (15, 4), "start"), "R5": ("R5", "1k", ACC, (15, 4), "start"),
 "R6": ("R6", "10k", ACC, (15, 4), "start"),
 "R2": ("R2", "330R", ACC, (-15, 4), "end"), "R3": ("R3", "330R", ACC, (15, 4), "start"),
}
for name, part in P.items():
    t = part["type"]
    if t in ("module", "underside"):
        continue
    for sh in pcb.body_shapes(part):
        col = LBL.get(name, (0, 0, LINE))[2]
        if t == "dip": col = LINE
        if t == "header": col = CYAN
        if sh[0] == "circle":
            _, cx, cy, r = sh
            fill = "#132f55" if t in ("elec", "diode_stand") else BG
            circ(mx(cx), my(cy), r * K, col, 2.2, fill)
        elif t == "to92":
            _, a, b, c_, d = sh
            r_ = (c_ - a) * K / 2
            add(f'<path d="M {mx(a):.1f} {my(d):.1f} L {mx(c_):.1f} {my(d):.1f} L {mx(c_):.1f} {my(b)+r_:.1f} '
                f'A {r_:.1f} {r_:.1f} 0 0 0 {mx(a):.1f} {my(b)+r_:.1f} Z" fill="{BG}" stroke="{LINE}" stroke-width="2.2"/>')
            ln(mx(a) + 3, my(d) - 3, mx(c_) - 3, my(d) - 3, ACC, 2)
        else:
            _, a, b, c_, d = sh
            rect(mx(a), my(b), (c_ - a) * K, (d - b) * K, col, 2.2, BG, 3 if t != "dip" else 6)
    # standing resistor / diode: show the hairpin lead
    if t in ("res", "diode_stand") and (t == "diode_stand" or pcb.res_mount(part) == "stand"):
        pins = list(part["pins"].items())
        body = part["body"]
        other = [h for p, h in pins if p != body][0]
        bh = part["pins"][body]
        col = LBL[name][2]
        ln(X(bh[0]), Y(bh[1]), X(other[0]), Y(other[1]), col, 2.2, 0.9, "3 3")
        circ(X(other[0]), Y(other[1]), 3.4, col, 0, col)
    if t == "res" and pcb.res_mount(part) == "flat":
        a, b = list(part["pins"].values())
        ln(X(a[0]), Y(a[1]), X(b[0]), Y(b[1]), ACC, 2.2, 0.9)
    if t == "cer" or t == "elec":
        a, b = list(part["pins"].values())
        for h in (a, b): circ(X(h[0]), Y(h[1]), 3.4, LBL[name][2], 0, LBL[name][2])
    if name in LBL:
        ref, val, col, (dx, dy), anc = LBL[name]
        sh = pcb.body_shapes(part)[0]
        cx, cy = (mx(sh[1]), my(sh[2])) if sh[0] == "circle" else (mx((sh[1] + sh[3]) / 2), my((sh[2] + sh[4]) / 2))
        if t in ("elec",) and (dx, dy) == (0, 0):
            txt(cx, cy - 2, ref, 10.5, col, "middle", MONO, "bold"); txt(cx, cy + 11, val, 8.5, DIM, "middle", MONO)
        else:
            tbox(cx + dx, cy + dy - 6, ref, 10, col, anc); tbox(cx + dx, cy + dy + 7, val, 8.5, DIM, anc, "normal")

# polarity marks
for name in ("C1A", "C1B", "C2", "C10"):
    ph = P[name]["pins"]["p"]
    txt(X(ph[0]) + 9, Y(ph[1]) - 4, "+", 13, RED, "start", SANS, "bold")
kh = P["D1"]["pins"]["K"]
txt(X(kh[0]) + 14, Y(kh[1]) + 2, "band", 9, RED, "start", MONO, "bold")
ln(X(kh[0]) - 9, Y(kh[1]) + 6, X(kh[0]) + 9, Y(kh[1]) + 6, RED, 3)

# DIP socket labels
cx = (X(11) + X(24)) / 2; cy = (Y(10) + Y(13)) / 2
add(f'<path d="M {X(11)-14} {cy-14} a 14 14 0 0 0 0 28" fill="none" stroke="{LINE}" stroke-width="2.2"/>')
txt(cx, cy - 4, "U2  ATmega328P", 14, ACC, "middle", MONO, "bold")
txt(cx, cy + 14, "28-pin DIP socket · notch LEFT", 10.5, DIM, "middle", MONO)
for n in range(1, 15):  txt(X(10 + n), Y(13) + 26, n, 9, DIM, "middle", MONO)
for n in range(15, 29): txt(X(10 + (29 - n)), Y(10) - 16, n, 9, DIM, "middle", MONO)

# Q1
q = P["Q1"]["pins"]
tbox(X(q["C"][0]) + 16, Y(q["B"][1]) - 6, "Q1", 10.5, ACC, "start"); tbox(X(q["C"][0]) + 16, Y(q["B"][1]) + 8, "2N2222A", 8.5, DIM, "start", "normal")
for lab in ("E", "B", "C"):
    circ(X(q[lab][0]), Y(q[lab][1]), 3.6, LINE, 0, LINE)
    txt(X(q[lab][0]), Y(q[lab][1]) + 18, lab, 10, DIM, "middle", MONO, "bold")

# headers
HL = {"J0": ("POWER IN", ["+12V", "GND"]), "J2": ("FAN A", ["GND", "+12V", "SNS", "PWM"]),
      "J3": ("FAN B", ["GND", "+12V", "SNS", "PWM"]),
      "J5": ("PANEL", ["+5V", "POT", "GND", "LED A", "LED B", "GND"]),
      "J4": ("LCD", ["GND", "VCC", "SDA", "SCL"]), "J6": ("SW2", ["D4", "GND"])}
for name, (lab, pins) in HL.items():
    hs = list(P[name]["pins"].values())
    top = hs[0][1] == 1
    for i, h in enumerate(hs):
        circ(X(h[0]), Y(h[1]), 3.6, CYAN, 0, CYAN)
        txt(X(h[0]), Y(h[1]) + (-26 if top else 30), pins[i], 8.5, DIM, "middle", MONO)
    mid = (X(hs[0][0]) + X(hs[-1][0])) / 2
    txt(mid, Y(hs[0][1]) + (-40 if top else 46), f"{name} · {lab}", 10.5, CYAN, "middle", MONO, "bold")

# ---------------- side panels
lx = 1170
rect(lx, 170, 350, 240, LINE, 2, rx=6)
txt(lx + 16, 198, "LEGEND", 13, ACC, "start", SANS, "bold", "1.3")
items = [(RED, 6, "bare wire bus — +12 V"), (LINE, 6, "bare wire bus — 0 V"),
         (CYAN, 6, "bare wire bus — +5 V"), (WIRE, 2, "insulated link (underside)"),
         ("#d8dee6", 7, "solder bridge, 2 holes"), (ACC, 2.2, "standing part: dotted = bent leg")]
for i, (c, w, t) in enumerate(items):
    yy = 224 + i * 28
    ln(lx + 20, yy, lx + 58, yy, c, w, 1, "3 3" if "dotted" in t else None)
    txt(lx + 70, yy + 4, t, 11, LINE, "start", MONO)
txt(lx + 16, 384, "Lines show WHICH holes join, not the", 10, DIM, "start", MONO)
txt(lx + 16, 398, "exact path. Bend wires around joints.", 10, DIM, "start", MONO)

ux, uy = lx, 424
rect(ux, uy, 350, 232, LINE, 2, rx=6)
txt(ux + 16, uy + 28, "UNDERSIDE PARTS", 13, ACC, "start", SANS, "bold", "1.2")
txt(ux + 16, uy + 47, "solder straight onto the socket pins", 10.5, DIM, "start", MONO)
ln(ux, uy + 58, ux + 350, uy + 58, LINE, 1.2)
und = [("C5", "100 nF CER", "pin 7 ↔ pin 8"), ("C8", "100 nF CER", "pin 21 ↔ pin 22"),
       ("Y1", "16 MHz", "pin 9 ↔ pin 10  (bend legs in)"), ("C9", "100 nF CER", "pin 20 ↔ 0 V spur above it")]
for i, (a, b, c_) in enumerate(und):
    yy = uy + 84 + i * 36
    txt(ux + 18, yy, a, 12, ACC, "start", MONO, "bold")
    txt(ux + 60, yy, b, 10.5, GRN if "CER" in b else LINE, "start", MONO)
    txt(ux + 18, yy + 15, c_, 10, DIM, "start", MONO)
txt(ux + 16, uy + 222, "Shortest legs possible — that is the point.", 10, ACC, "start", MONO)

px_, py_ = lx, 672
rect(px_, py_, 350, 196, RED, 2, rx=6)
txt(px_ + 16, py_ + 28, "BEFORE FIRST POWER-UP", 13, RED, "start", SANS, "bold", "1.2")
chk = ["Meter on DIODE test, red on +12 V row,", "black on 0 V row: the reading must CLIMB",
       "to OL as C1A/C1B charge. A steady 0.5-", "0.7 V means D1 is in BACKWARDS.",
       "", "Both C1 stripes (-) face the 0 V row.", "D1 band faces the +12 V row.",
       "Q1 flat face toward row 16 (downward)."]
for i, t in enumerate(chk):
    txt(px_ + 16, py_ + 56 + i * 18, t, 10.5, LINE if t else LINE, "start", MONO)

# ---------------- wire list
ty = 912
rows_ = []
pin_net = {(c, p): n for n, pins in B["nets"].items() for (c, p) in pins}
hole_net = {}
for c, part in P.items():
    for p, h in part["pins"].items():
        if (c, p) in pin_net: hole_net[h] = pin_net[(c, p)]
for (r, c1, c2, net, _) in B["buses"]:
    for c in range(c1, c2 + 1): hole_net.setdefault((c, r), net)
def fmt(h): return f"{h[0]},{h[1]}"
for L in B["links"]:
    rows_.append((fmt(L[0]), fmt(L[-1]), hole_net.get(L[0]) or hole_net.get(L[-1]) or "-"))
for pin in ("INp", "INn", "OUTp", "OUTn"):
    rows_.append(("U1 " + {"INp": "IN+", "INn": "IN-", "OUTp": "OUT+", "OUTn": "OUT-"}[pin],
                  fmt(u["pins"][pin]), {"INp": "P12V", "OUTp": "P5V"}.get(pin, "GND")))
for a, b in B["bridges"]:
    rows_.append((fmt(a), fmt(b), "bridge"))
rect(60, ty, W - 120, 580, LINE, 2)
txt(78, ty + 30, f"WIRE LIST — {len(B['links'])} LINKS · 4 MODULE WIRES · {len(B['bridges'])} BRIDGES",
    14, ACC, "start", SANS, "bold", "1.3")
ln(60, ty + 42, W - 60, ty + 42, LINE, 1.4)
per = 17
for k, (a, b, n) in enumerate(rows_):
    cx_ = 86 + (k // per) * 360
    yy = ty + 70 + (k % per) * 27
    txt(cx_, yy, f"{k+1:2d}", 10.5, DIM, "start", MONO)
    txt(cx_ + 30, yy, f"{a:>8}", 11, LINE, "start", MONO)
    txt(cx_ + 112, yy, "→", 11, DIM, "start", MONO)
    txt(cx_ + 134, yy, f"{b:>6}", 11, LINE, "start", MONO)
    txt(cx_ + 200, yy, n, 11, NETCOL.get(n, ACC), "start", MONO, "bold")
txt(78, ty + 548, "Coordinates are column,row. Order: bare-wire buses → links → bridges → parts → underside parts → "
                   "smoke test → chip.", 11, DIM, "start", MONO)
txt(78, ty + 566, "Use insulated wire for every link. Where a link crosses a bare bus, keep the iron off the insulation.",
    11, DIM, "start", MONO)
add("</svg>")
# UTF-8 explicitly: on Windows the default is cp1252, which can't write the ≈ and → used above.
with open(sys.argv[1] if len(sys.argv) > 1 else "SFE-04_Perfboard_Layout.svg", "w",
          encoding="utf-8", newline="\n") as f:
    f.write("\n".join(o))
print("rendered", len(o), "elements,", len(rows_), "wire-list rows")
