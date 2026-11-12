# -*- coding: utf-8 -*-
"""The checker is only worth trusting if it fails when it should.
Each case breaks the current board in one specific way; all must be caught,
and the unbroken board must pass.   run:  python3 test_checker.py"""
import copy, sys
import pcb, board as c

CASES = [
    ("D1 cathode moved onto the +5 V row",
     lambda B: B["parts"]["D1"]["pins"].update(K=(2, 6)), "SHORT"),
    ("R12 leg pushed into R8's hole",
     lambda B: B["parts"]["R12"]["pins"].update({"1": (26, 8)}), "leads in one hole"),
    ("C1B moved next to C1A (8 mm cans 2 holes apart)",
     lambda B: B["parts"]["C1B"]["pins"].update(p=(8, 2), n=(8, 4)), "overlap"),
    ("R2 drawn 3 holes long",
     lambda B: B["parts"]["R2"]["pins"].update({"2": (5, 18)}), "across 3 holes"),
    ("tach link to pin 4 forgotten",
     lambda B: B["links"].remove(((26, 11), (14, 11), (14, 13))), "TACHA split"),
    ("bus tie removed so the lower 0 V floats",
     lambda B: B["links"].remove(((32, 4), (32, 17))), "GND split"),
    ("+12 V link drawn straight through Q1's base",
     lambda B: B["links"].append(((28, 20), (28, 2))), "runs across"),
    ("R4 slid under the buck module",
     lambda B: B["parts"]["R4"]["pins"].update({"1": (8, 7), "2": (8, 11)}), "under the body of U1"),
]

def main():
    e, _, _ = pcb.check(c.BOARD)
    ok = not e
    print(f"  {'PASS' if ok else 'FAIL':6s} unbroken board is clean")
    for desc, fn, expect in CASES:
        B = copy.deepcopy(c.BOARD); fn(B)
        e, _, _ = pcb.check(B)
        hit = any(expect in x for x in e)
        ok &= hit
        print(f"  {'CAUGHT' if hit else 'MISSED':6s} {desc}")
    print("\nchecker self-test:", "OK" if ok else "FAILED")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
