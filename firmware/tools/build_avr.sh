#!/usr/bin/env bash
# Real AVR build of the sketch with avr-gcc, mirroring the Arduino IDE's Uno
# settings, with -Wall -Wextra on the sketch so warnings actually show.
# Needs: avr-gcc, avr-libc, git.  Fetches the official Arduino AVR core and the
# LiquidCrystal I2C library into firmware/.deps on first run.
#   usage:  firmware/tools/build_avr.sh [F_CPU]      (default 16000000L)
# On a machine with arduino-cli, this is the simpler equivalent:
#   arduino-cli compile --fqbn arduino:avr:uno --warnings all firmware/SolderFumeExtractor
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
INO="$HERE/SolderFumeExtractor/SolderFumeExtractor.ino"
DEPS="$HERE/.deps"; OUT="$HERE/.build"; FCPU="${1:-16000000L}"
command -v avr-gcc >/dev/null || { echo "avr-gcc not found (Debian/Ubuntu: apt install gcc-avr avr-libc; macOS: brew tap osx-cross/avr && brew install avr-gcc)"; exit 2; }
mkdir -p "$DEPS" "$OUT/obj"
[ -d "$DEPS/core" ]   || git clone -q --depth 1 https://github.com/arduino/ArduinoCore-avr.git "$DEPS/core"
[ -d "$DEPS/lcdlib" ] || git clone -q --depth 1 https://github.com/johnrickman/LiquidCrystal_I2C.git "$DEPS/lcdlib"
CORE="$DEPS/core"; MCU="-mmcu=atmega328p"
DEFS="-DF_CPU=$FCPU -DARDUINO=10819 -DARDUINO_AVR_UNO -DARDUINO_ARCH_AVR"
INC="-I$CORE/cores/arduino -I$CORE/variants/standard -I$CORE/libraries/Wire/src -I$CORE/libraries/Wire/src/utility -I$CORE/libraries/EEPROM/src -I$DEPS/lcdlib"
CF="$MCU $DEFS $INC -Os -g -w -ffunction-sections -fdata-sections -flto -fno-fat-lto-objects"
CXXF="$CF -std=gnu++11 -fpermissive -fno-exceptions -fno-threadsafe-statics"
rm -f "$OUT"/obj/*.o
for s in "$CORE"/cores/arduino/*.c "$CORE"/cores/arduino/*.cpp "$CORE"/libraries/Wire/src/*.cpp "$CORE"/libraries/Wire/src/utility/*.c "$DEPS"/lcdlib/*.cpp; do
  o="$OUT/obj/$(basename "$s").o"
  case "$s" in *.c) avr-gcc $CF -std=gnu11 -c "$s" -o "$o" ;; *) avr-g++ $CXXF -c "$s" -o "$o" ;; esac
done
avr-gcc $MCU $DEFS -x assembler-with-cpp -flto -c "$CORE/cores/arduino/wiring_pulse.S" -o "$OUT/obj/wiring_pulse.S.o"
{ echo '#include <Arduino.h>'; echo '#line 1 "SolderFumeExtractor.ino"'; cat "$INO"; } > "$OUT/sketch.cpp"
avr-g++ $MCU $DEFS $INC -Os -g -Wall -Wextra -ffunction-sections -fdata-sections -flto -fno-fat-lto-objects \
  -std=gnu++11 -fno-exceptions -fno-threadsafe-statics -c "$OUT/sketch.cpp" -o "$OUT/obj/sketch.o" 2>&1 | tee "$OUT/warnings.txt"
[ -s "$OUT/warnings.txt" ] && { echo "sketch produced warnings - see above"; exit 1; }
avr-gcc $MCU -Os -g -flto -fuse-linker-plugin -Wl,--gc-sections -o "$OUT/fw.elf" "$OUT"/obj/*.o -lm
avr-objcopy -O ihex -R .eeprom "$OUT/fw.elf" "$OUT/SolderFumeExtractor.hex"
avr-size -C --mcu=atmega328p "$OUT/fw.elf" | grep -E "Program|Data"
echo "OK: $OUT/SolderFumeExtractor.hex (F_CPU=$FCPU)"
