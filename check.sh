#!/usr/bin/env bash
# Run every check this project has. Exits non-zero if anything fails.
# On Windows, run it from Git Bash:  ./check.sh
set -uo pipefail
cd "$(dirname "$0")"; fail=0
PY=$(command -v python3 || command -v python)
step(){ echo; echo "=== $1"; }
step "perfboard layout: electrical + physical check"
( cd hardware/layout && "$PY" -c "import pcb, board, sys; e,_,_=pcb.report(board.BOARD,'CURRENT LAYOUT'); sys.exit(1 if e else 0)" ) || fail=1
step "checker self-test (must catch 8 deliberate faults)"
( cd hardware/layout && "$PY" test_checker.py ) || fail=1
step "redraw sheet 4 from the checked layout data"
( cd hardware/layout && "$PY" render.py ../../docs/layout/SFE-04_Perfboard_Layout.svg ) || fail=1
step "firmware logic tests (host)"
if command -v g++ >/dev/null; then
  ( cd firmware/tests && g++ -std=c++17 -O1 -Wall -o "${TMPDIR:-/tmp}/sfe_test_logic" test_logic.cpp && "${TMPDIR:-/tmp}/sfe_test_logic" ) || fail=1
else echo "skipped: no g++"; fi
step "firmware: real AVR build"
if command -v arduino-cli >/dev/null; then
  arduino-cli compile --fqbn arduino:avr:uno --warnings all firmware/SolderFumeExtractor || fail=1
elif command -v avr-gcc >/dev/null; then firmware/tools/build_avr.sh || fail=1
else echo "skipped: neither arduino-cli nor avr-gcc installed"; fi
echo; [ $fail -eq 0 ] && echo "ALL CHECKS PASSED" || echo "SOMETHING FAILED - read above"
exit $fail
