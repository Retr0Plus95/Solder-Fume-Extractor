// Host-side tests for the firmware's pure logic.
// These functions are COPIES of the ones in SolderFumeExtractor.ino (marked
// "copied from sketch"). If you change the sketch, update the copy here too.
//   build & run:  g++ -std=c++17 -O1 -Wall -o test_logic test_logic.cpp && ./test_logic
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <initializer_list>

static int failures = 0;
#define CHECK(cond, ...) do { if (!(cond)) { failures++; printf("  FAIL: " __VA_ARGS__); printf("\n"); } } while (0)

// ---- copied from sketch -------------------------------------------------
const uint8_t  MIN_DUTY_PCT = 25, OFF_THRESHOLD_PCT = 4, RAMP_STEP_PCT = 3;
const uint16_t STALL_RPM = 250, FILTER_LIFE_HOURS = 120;
const uint8_t  STALL_SECONDS = 3, MAX_RESTARTS = 3;

int32_t potAccum = 0, potLastSeen = 0; int fakeAdc = 0;
int analogRead(int) { return fakeAdc; }
uint8_t readDemand() {
  uint16_t acc = 0;
  for (uint8_t i = 0; i < 8; i++) acc += analogRead(0);
  int32_t raw = acc >> 3;
  potAccum += raw - (potAccum >> 4);
  int32_t filtered = potAccum >> 4;
  if (filtered < 0) filtered = 0;
  if (filtered > 1023) filtered = 1023;
  uint8_t pct = (uint8_t)(((uint32_t)filtered * 100UL) / 1023UL);
  if (pct <= OFF_THRESHOLD_PCT) return 0;
  uint32_t span = 100UL - OFF_THRESHOLD_PCT;
  uint32_t v = (uint32_t)(pct - OFF_THRESHOLD_PCT) * (100UL - MIN_DUTY_PCT);
  return (uint8_t)(MIN_DUTY_PCT + (v / span));
}

bool restartPending = false;
void evalFan(uint16_t rpm, bool driven, uint8_t &stallCount, uint8_t &restarts, bool &fault) {
  if (!driven) { stallCount = 0; return; }
  if (rpm >= STALL_RPM) { stallCount = 0; restarts = 0; fault = false; return; }
  if (stallCount < 255) stallCount++;
  if (stallCount >= STALL_SECONDS && !fault) {
    if (restarts < MAX_RESTARTS) { restarts++; stallCount = 0; restartPending = true; }
    else fault = true;
  }
}

uint8_t dutyPct = 0, targetPct = 0;
void setDuty(uint8_t p) { dutyPct = p; }
void applyRamp() {
  uint8_t cur = dutyPct;
  if (targetPct > cur) cur = (uint8_t)((targetPct - cur > RAMP_STEP_PCT) ? cur + RAMP_STEP_PCT : targetPct);
  else if (targetPct < cur) cur = (uint8_t)((cur - targetPct > RAMP_STEP_PCT) ? cur - RAMP_STEP_PCT : targetPct);
  else return;
  setDuty(cur);
}
// -------------------------------------------------------------------------

static void test_pot() {
  for (int target : {0, 1, 7, 500, 1016, 1023}) {
    potAccum = 0; fakeAdc = target;
    for (int i = 0; i < 400; i++) readDemand();
    int settled = potAccum >> 4;
    CHECK(abs(settled - target) <= 1, "pot filter settles at %d, wanted %d", settled, target);
  }
  int prev = -1, maxd = 0;
  for (int a = 0; a <= 1023; a++) {
    potAccum = (int32_t)a << 4; fakeAdc = a;
    int d = readDemand();
    if (d > 0) { CHECK(d >= prev, "duty not monotonic at adc %d", a); CHECK(d >= MIN_DUTY_PCT, "duty %d below stall floor", d); prev = d; }
    if (d > maxd) maxd = d;
  }
  CHECK(maxd == 100, "full pot gives %d%%, wanted 100", maxd);
  printf("  pot filter + mapping checked over 1024 positions\n");
}

static void test_lcd() {
  char buf[17];
  for (const char *st : {"FAULT! ", "STOPPED", "STARTUP", "MAXIMUM", "RUNNING"})
    for (int d : {0, 7, 75, 100}) {
      snprintf(buf, sizeof buf, "Spd:%3u%% %-7s", (unsigned)d, st);
      CHECK(strlen(buf) == 16, "line 1 is %zu chars: [%s]", strlen(buf), buf);
    }
  for (int r : {0, 9, 999, 1450, 9999}) {
    snprintf(buf, sizeof buf, "A%4u B%4u rpm ", (unsigned)r, (unsigned)r);
    CHECK(strlen(buf) == 16, "rpm line is %zu chars", strlen(buf));
  }
  for (int h : {0, 7, 99, 119, 999}) {
    snprintf(buf, sizeof buf, "Filter:%3u/%3u h", (unsigned)h, (unsigned)FILTER_LIFE_HOURS);
    CHECK(strlen(buf) == 16, "filter line is %zu chars", strlen(buf));
  }
  for (const char *s : {"!BOTH FANS STOP ", "!FAN A NO SIGNAL", "!FAN B NO SIGNAL", "CHANGE FILTER!  ", "FILTER HOURS = 0"})
    CHECK(strlen(s) == 16, "fixed string wrong length: [%s]", s);
  printf("  every LCD string is exactly 16 characters\n");
}

static void test_stall() {
  uint8_t sc = 0, rs = 0; bool f = false; int kicks = 0, latchedAt = 0;
  for (int s = 1; s <= 20 && !f; s++) {
    restartPending = false; evalFan(0, true, sc, rs, f);
    if (restartPending) kicks++;
    if (f) latchedAt = s;
  }
  CHECK(f && kicks == 3 && latchedAt == 12, "stalled fan: %d restarts, latched at %ds", kicks, latchedAt);
  sc = 0; rs = 0; f = false;
  for (int s = 1; s <= 15; s++) { restartPending = false; evalFan(s >= 8 ? 1400 : 0, true, sc, rs, f); }
  CHECK(!f && rs == 0, "recovering fan did not clear");
  sc = 9; f = false; evalFan(0, false, sc, rs, f);
  CHECK(sc == 0 && !f, "undriven fan was judged");
  printf("  stall: 3 restarts then latch at 12 s; recovery clears; undriven ignored\n");
}

static void test_ramp() {
  for (int a = 0; a <= 100; a++)
    for (int b = 0; b <= 100; b++) {
      dutyPct = (uint8_t)a; targetPct = (uint8_t)b; int n = 0;
      while (dutyPct != b && n < 500) { applyRamp(); n++; }
      CHECK(dutyPct == b, "ramp %d->%d stuck at %u", a, b, dutyPct);
    }
  dutyPct = 0; targetPct = 100; int t = 0;
  while (dutyPct < 100) { applyRamp(); t++; }
  CHECK(t * 25 == 850, "0->100%% takes %d ms, expected 850", t * 25);
  CHECK(t * 25 < 1200, "ramp longer than KICK_MS");
  printf("  ramp: all 10201 transitions land exactly; 0->100%% in %d ms\n", t * 25);
}

int main() {
  test_pot(); test_lcd(); test_stall(); test_ramp();
  printf(failures ? "\n%d FAILURE(S)\n" : "\nALL LOGIC TESTS PASSED\n", failures);
  return failures ? 1 : 0;
}
