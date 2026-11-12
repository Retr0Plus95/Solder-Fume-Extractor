# -*- coding: utf-8 -*-
"""Writes forge-project.json's "board" and "build" sections from board.py and build_steps.py,
for Maker Forge Bench (its 3D board view, part connections and build steps). Every other part of
the project file is left exactly as it is. check.sh runs this, so the file never drifts from the
layout. Edit board.py and build_steps.py, never these two sections by hand.

    python export_board.py [path/to/forge-project.json]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pcb  # noqa: E402

EXTRAS = ("body", "D", "keepout", "round", "half")


def _point(hole):
    return [hole[0], hole[1]]


def board_section(B):
    parts = {}
    for ref, part in B["parts"].items():
        out = {
            "type": part["type"],
            "pins": {name: _point(hole) for name, hole in part["pins"].items()},
            "side": "bottom" if part["type"] == "underside" else "top",
        }
        for extra in EXTRAS:
            if extra in part:
                value = part[extra]
                out[extra] = list(value) if isinstance(value, tuple) else value
        if part["type"] == "res":
            # the same rule pcb.py's checker uses: flat when it spans 4+ holes, unless board.py says
            out["mount"] = pcb.res_mount(part)
            if out["mount"] == "flat":
                out.pop("body", None)  # a flat resistor has no body over a pin
        parts[ref] = out
    labels = {}
    for (_, _, _, net, label) in B["buses"]:
        labels.setdefault(net, label)
    return {
        "format": "perfboard",
        "source": "hardware/layout/board.py",
        "pitch": 2.54,
        "cols": B["cols"],
        "rows": B["rows"],
        "hole": 1.0,
        "parts": parts,
        "buses": [{"row": r, "from": a, "to": b, "net": net, "label": label, "side": "bottom"}
                  for (r, a, b, net, label) in B["buses"]],
        "links": [{"path": [_point(h) for h in link], "side": "bottom"} for link in B["links"]],
        "bridges": [{"holes": [_point(a), _point(b)], "side": "bottom"} for (a, b) in B["bridges"]],
        "nets": {name: [[ref, pin] for (ref, pin) in members] for name, members in B["nets"].items()},
        "netLabels": labels,
        "spare": list(B.get("spare", [])),
    }


def build_section(steps, B):
    """The build steps, checked against the board: every board part in exactly one step."""
    known = set(B["parts"])
    seen = []
    for step in steps:
        unknown = [ref for ref in step["parts"] if ref not in known]
        if unknown:
            raise ValueError(f"build step {step['id']!r} names parts board.py doesn't have: {unknown}")
        seen.extend(step["parts"])
    twice = sorted({ref for ref in seen if seen.count(ref) > 1})
    missing = sorted(known - set(seen))
    if twice or missing:
        raise ValueError(f"every board part must be in exactly one build step; twice: {twice}, in none: {missing}")
    return [{"id": s["id"], "title": s["title"], "why": s["why"], "parts": list(s["parts"]), "what": list(s["what"])}
            for s in steps]


def main(path=os.path.join(HERE, "..", "..", "forge-project.json")):
    import board
    import build_steps
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["board"] = board_section(board.BOARD)
    data["build"] = build_section(build_steps.STEPS, board.BOARD)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"forge-project.json: board ({len(data['board']['parts'])} parts) and build ({len(data['build'])} steps) written")


if __name__ == "__main__":
    main(*sys.argv[1:])
