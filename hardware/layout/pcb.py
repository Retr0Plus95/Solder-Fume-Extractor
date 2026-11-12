# -*- coding: utf-8 -*-
"""Perfboard model + checker for the Solder Fume Extractor.

A board is described as data (parts with pins at hole coordinates, bare-wire
buses, insulated links, solder bridges, a netlist). check(board) then proves:

  ELECTRICAL  every net is fully connected, no two nets touch, spare MCU pins
              are tied to nothing.
  PHYSICAL    one lead per hole, no lead under another part's body, no two
              bodies overlapping, lead spans a real part can actually make,
              no link drawn straight across someone else's solder joint,
              bridges only between neighbouring holes.

Coordinates are (column, row), 1-based, 0.1 in (2.54 mm) pitch.
Body sizes are typical catalogue dimensions, not a specific part's datasheet.
"""
import math

PITCH = 2.54
TOL = 0.30          # mm two bodies may overlap and still count as "touching"
LEAD_R = 0.40       # mm effective lead radius
JOINT_CLEAR = 0.90  # mm a straight link must clear a foreign solder joint


def mm(h):
    return ((h[0] - 1) * PITCH, (h[1] - 1) * PITCH)


# ----------------------------------------------------------------- shapes
def _rect(x1, y1, x2, y2):
    return ("rect", min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def _axis_rect(a, b, length, width):
    (x1, y1), (x2, y2) = mm(a), mm(b)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    if abs(y1 - y2) < 1e-6:   # horizontal leads
        return _rect(cx - length / 2, cy - width / 2, cx + length / 2, cy + width / 2)
    return _rect(cx - width / 2, cy - length / 2, cx + width / 2, cy + length / 2)


def span(part):
    (c1, r1), (c2, r2) = list(part["pins"].values())[:2]
    return max(abs(c1 - c2), abs(r1 - r2))


def res_mount(part):
    return part.get("mount") or ("flat" if span(part) >= 4 else "stand")


def body_shapes(part):
    t, p = part["type"], part["pins"]
    if t == "res":
        a, b = list(p.values())
        if res_mount(part) == "flat":
            return [_axis_rect(a, b, 6.5, 2.5)]
        x, y = mm(p[part["body"]])
        return [("circle", x, y, 1.3)]
    if t == "cer":
        a, b = list(p.values())
        return [_axis_rect(a, b, 4.5, 2.6)]
    if t == "elec":
        (x1, y1), (x2, y2) = [mm(h) for h in p.values()]
        return [("circle", (x1 + x2) / 2, (y1 + y2) / 2, part["D"] / 2)]
    if t == "diode_stand":
        x, y = mm(p[part["body"]])
        return [("circle", x, y, part["D"] / 2)]
    if t == "to92":
        bx, by = mm(p["B"])
        rnd, flat = 3.4, 0.6
        if part["round"] == "up":
            return [_rect(bx - 2.5, by - rnd, bx + 2.5, by + flat)]
        return [_rect(bx - 2.5, by - flat, bx + 2.5, by + rnd)]
    if t == "dip":
        xs = [mm(h)[0] for h in p.values()]
        ys = [mm(h)[1] for h in p.values()]
        return [_rect(min(xs) - 1.6, min(ys) - 1.6, max(xs) + 1.6, max(ys) + 1.6)]
    if t == "header":
        xs = [mm(h)[0] for h in p.values()]
        ys = [mm(h)[1] for h in p.values()]
        half = part.get("half", 1.27)
        return [_rect(min(xs) - 1.27, min(ys) - half, max(xs) + 1.27, max(ys) + half)]
    if t == "module":
        c1, r1, c2, r2 = part["keepout"]
        (x1, y1), (x2, y2) = mm((c1, r1)), mm((c2, r2))
        return [_rect(x1, y1, x2, y2)]
    return []  # underside parts have no top-side body


def _pt_in(shape, x, y, grow=0.0):
    if shape[0] == "circle":
        _, cx, cy, r = shape
        return math.hypot(x - cx, y - cy) < r + grow
    _, x1, y1, x2, y2 = shape
    return x1 - grow < x < x2 + grow and y1 - grow < y < y2 + grow


def _overlap(a, b):
    """Penetration depth in mm (<=0 means clear)."""
    if a[0] == "rect" and b[0] == "rect":
        dx = min(a[3], b[3]) - max(a[1], b[1])
        dy = min(a[4], b[4]) - max(a[2], b[2])
        return min(dx, dy) if dx > 0 and dy > 0 else 0.0
    if a[0] == "circle" and b[0] == "circle":
        return a[3] + b[3] - math.hypot(a[1] - b[1], a[2] - b[2])
    c, r = (a, b) if a[0] == "circle" else (b, a)
    _, cx, cy, rad = c
    _, x1, y1, x2, y2 = r
    nx, ny = max(x1, min(cx, x2)), max(y1, min(cy, y2))
    return rad - math.hypot(cx - nx, cy - ny)


def _seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


# ------------------------------------------------------------------ check
class _UF:
    def __init__(s): s.p = {}
    def f(s, x):
        s.p.setdefault(x, x)
        while s.p[x] != x:
            s.p[x] = s.p[s.p[x]]; x = s.p[x]
        return x
    def u(s, a, b): s.p[s.f(a)] = s.f(b)


def is_top_lead(part):
    return part["type"] != "underside"


def check(B):
    errs, warns, info = [], [], []
    P, NETS = B["parts"], B["nets"]
    pin_net = {(c, p): n for n, pins in NETS.items() for (c, p) in pins}

    # every netlist pin must exist, every placed pin must be in the netlist
    for (c, p) in pin_net:
        if c not in P or p not in P[c]["pins"]:
            errs.append(f"netlist names {c}.{p}, which is not placed")
    for c, part in P.items():
        for p in part["pins"]:
            if (c, p) not in pin_net and not (c == "U2" and p in B["spare"]):
                errs.append(f"{c}.{p} is placed but in no net")

    bus_hole = {}
    for (r, c1, c2, net, _) in B["buses"]:
        for c in range(c1, c2 + 1):
            bus_hole[(c, r)] = net

    # ---------------- ELECTRICAL
    uf = _UF()
    for (r, c1, c2, _, _) in B["buses"]:
        for c in range(c1, c2):
            uf.u((c, r), (c + 1, r))
    for L in B["links"] + B["bridges"]:
        uf.u(L[0], L[-1])
    for net, pins in NETS.items():
        groups = {}
        for c, p in pins:
            groups.setdefault(uf.f(P[c]["pins"][p]), []).append(f"{c}.{p}")
        if len(groups) > 1:
            errs.append(f"net {net} split into {len(groups)}: " +
                        " | ".join(",".join(v) for v in groups.values()))
    gnets = {}
    for net, pins in NETS.items():
        for c, p in pins:
            gnets.setdefault(uf.f(P[c]["pins"][p]), set()).add(net)
    for (r, c1, c2, net, _) in B["buses"]:
        gnets.setdefault(uf.f((c1, r)), set()).add(net)
    for ns in gnets.values():
        if len(ns) > 1:
            errs.append(f"SHORT between {sorted(ns)}")
    for sp in B["spare"]:
        g = uf.f(P["U2"]["pins"][sp])
        if g in gnets:
            errs.append(f"spare U2 pin {sp} tied to {sorted(gnets[g])}")

    # hole -> net (for joint checks)
    hole_net = {}
    for c, part in P.items():
        for p, h in part["pins"].items():
            if (c, p) in pin_net:
                hole_net[h] = pin_net[(c, p)]
    joint = set(hole_net)                       # holes with something soldered
    for L in B["links"] + B["bridges"]:
        a, b = L[0], L[-1]
        joint.add(a); joint.add(b)
        for h in (a, b):
            if h not in hole_net:
                g = uf.f(h)
                if g in gnets and len(gnets[g]) == 1:
                    hole_net[h] = next(iter(gnets[g]))

    # ---------------- PHYSICAL
    # P1 one through-hole lead per hole
    occ = {}
    for c, part in P.items():
        if not is_top_lead(part):
            continue
        for p, h in part["pins"].items():
            occ.setdefault(h, []).append(f"{c}.{p}")
    for h, who in occ.items():
        if len(who) > 1:
            errs.append(f"hole {h}: {len(who)} leads in one hole ({', '.join(who)})")

    # P2 lead under a foreign body / module wire under its own module
    shapes = {c: body_shapes(part) for c, part in P.items()}
    for c, shs in shapes.items():
        for sh in shs:
            for h, who in occ.items():
                owners = {w.split(".")[0] for w in who}
                x, y = mm(h)
                if c in owners and P[c]["type"] != "module":
                    continue
                if _pt_in(sh, x, y, LEAD_R):
                    what = "its own wire hole" if c in owners else ", ".join(who)
                    errs.append(f"{what} at {h} is under the body of {c}")

    # P3 body overlap
    names = list(shapes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for a in shapes[names[i]]:
                for b in shapes[names[j]]:
                    d = _overlap(a, b)
                    if d > TOL:
                        errs.append(f"bodies of {names[i]} and {names[j]} overlap by {d:.1f} mm")

    # P4 spans a real part can make
    for c, part in P.items():
        t = part["type"]
        if t in ("res", "cer", "elec", "diode_stand"):
            (c1, r1), (c2, r2) = list(part["pins"].values())
            if c1 != c2 and r1 != r2:
                errs.append(f"{c} is placed diagonally")
            s = span(part)
            if t == "res":
                m = res_mount(part)
                if m == "stand" and s not in (1, 2):
                    errs.append(f"{c}: standing resistor across {s} holes - "
                                f"too far to stand, too short to lie flat (needs 4)")
                if m == "flat" and s < 4:
                    errs.append(f"{c}: flat resistor across {s} holes (needs 4)")
            if t == "elec" and s != 2:
                errs.append(f"{c}: electrolytic across {s} holes (use 2)")
            if t == "cer" and s not in (1, 2, 3):
                errs.append(f"{c}: ceramic across {s} holes")
            if t == "diode_stand" and s != 2:
                errs.append(f"{c}: standing diode across {s} holes (use 2)")

    # P5 underside parts must land on a joint or a bus
    u2 = set(P["U2"]["pins"].values()) if "U2" in P else set()
    for c, part in P.items():
        if part["type"] == "underside":
            for p, h in part["pins"].items():
                if h not in u2 and h not in bus_hole:
                    errs.append(f"underside part {c}.{p} at {h} has nothing to solder to")

    # P6 bridges: neighbours only, and flag risky neighbours
    for a, b in B["bridges"]:
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
            errs.append(f"bridge {a}-{b} is not between neighbouring holes")
        n = hole_net.get(a)
        for h in (a, b):
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (h[0] + d[0], h[1] + d[1])
                if nb in (a, b) or nb not in hole_net:
                    continue
                if hole_net[nb] != n:
                    warns.append(f"bridge {a}-{b}: neighbour {nb} is {hole_net[nb]} - keep the blob small")

    # P7 a link (each straight run between bends) must not cross a foreign joint
    crossings = 0
    for L in B["links"]:
      a, b = L[0], L[-1]
      n = hole_net.get(a) or hole_net.get(b)
      for k in range(len(L) - 1):
        A, Bm = mm(L[k]), mm(L[k + 1])
        for h in joint:
            if h in (a, b) and hole_net.get(h) == n:
                continue
            if _seg_dist(mm(h), A, Bm) < JOINT_CLEAR and hole_net.get(h) != n:
                errs.append(f"link {a}->{b} ({n}) runs across the {hole_net.get(h,'?')} joint at {h}")
        for (r, c1, c2, bn, _) in B["buses"]:
            if bn == n:
                continue
            y = (r - 1) * PITCH
            if A[1] != Bm[1] and (A[1] - y) * (Bm[1] - y) < 0:
                t = (y - A[1]) / (Bm[1] - A[1])
                xc = A[0] + t * (Bm[0] - A[0])
                if (c1 - 1) * PITCH - 1 <= xc <= (c2 - 1) * PITCH + 1:
                    crossings += 1
    info.append(f"{crossings} places where an insulated link crosses a bare bus")

    # P8 inside the board
    W, H = (B["cols"] - 1) * PITCH, (B["rows"] - 1) * PITCH
    for c, shs in shapes.items():
        for sh in shs:
            x1, y1, x2, y2 = ((sh[1] - sh[3], sh[2] - sh[3], sh[1] + sh[3], sh[2] + sh[3])
                              if sh[0] == "circle" else sh[1:])
            if x1 < -1.5 or y1 < -1.5 or x2 > W + 1.5 or y2 > H + 1.5:
                (warns if P[c]["type"] == "header" else errs).append(
                    f"{c} hangs over the board edge")
    return errs, warns, info


def report(B, title):
    e, w, i = check(B)
    print(f"== {title} ==")
    print(f"   {len(B['parts'])} parts, {len(B['nets'])} nets, "
          f"{sum(len(v) for v in B['nets'].values())} net pins, "
          f"{len(B['buses'])} buses, {len(B['links'])} links, {len(B['bridges'])} bridges")
    for x in i: print("   info:", x)
    for x in w: print("   WARN:", x)
    if e:
        print(f"   {len(e)} ERROR(S)")
        for x in e: print("    -", x)
    else:
        print("   PASS - electrical and physical checks clean")
    return e, w, i
