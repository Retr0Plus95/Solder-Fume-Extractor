/* =====================================================================
   SOLDER FUME EXTRACTOR  -  dual 4-pin PWM fan controller
   Firmware v1.2
   Target : bare ATmega328P-PU @ 16 MHz, 5 V, Arduino UNO bootloader
   Board  : Tools > Board > "Arduino Uno"
   Library: LiquidCrystal_I2C by John Rickman (Library Manager)

   Hardware pins (Arduino name -> DIP-28 physical pin)
     D2  (pin 4)  TACH_A   fan A sense, INT0, 10k pull-up, 4k7 series
     D3  (pin 5)  TACH_B   fan B sense, INT1, 10k pull-up, 4k7 series
     D4  (pin 6)  SW2      filter-hours reset button to GND (OPTIONAL)
     D5  (pin 11) LED_A    green status LED via 330R
     D6  (pin 12) LED_B    green status LED via 330R
     D9  (pin 15) PWM_CTL  OC1A -> 1k -> base of Q1 (2N2222A)
     A0  (pin 23) POT      RV1 10k wiper
     A4  (pin 27) SDA      LCD backpack
     A5  (pin 28) SCL      LCD backpack

   IMPORTANT - inverted drive
     Q1 is an open-collector sink on the fans' PWM line. When the MCU
     pin is HIGH, Q1 conducts and drags the PWM line LOW (= 0 % demand).
     Timer1 is therefore configured in INVERTING compare mode, which
     cancels the hardware inversion. After that, OCR1A maps directly:
        OCR1A = 0        ->  fans 0 %
        OCR1A = PWM_TOP  ->  fans 100 %
     While the MCU is in reset the pin is a floating input, Q1 is held
     off by R6, and the fans free-run at 100 %. That is deliberate: a
     crashed controller must never silently stop the extraction.

   v1.1 changes
     - Watchdog timer. If the firmware ever hangs, the chip resets and
       the fans revert to 100 % rather than sticking at some old speed.
     - Stall auto-restart. A fan that stops gets three full-power
       restart attempts before the fault latches, so a momentarily
       obstructed fan recovers by itself.
     - Backlight timeout. The LCD backlight sleeps after 30 s of no
       activity while the fans are stopped; touching the pot wakes it.
     - Optional filter-hours reset button on D4.

   v1.2 changes
     - Soft ramp. Commanded duty now slews at 3 % per 25 ms instead of
       stepping, so the fans are eased up to speed rather than slammed
       to 100 %. This lowers the peak supply current at power-on, which
       matters if you are running a 1 A fast-blow fuse.
   ===================================================================== */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <EEPROM.h>
#include <avr/wdt.h>
#include <string.h>

/* ------------------------- user settings ------------------------- */
#define LCD_ADDRESS        0x27   // try 0x3F if the screen stays blank
#define LCD_COLS           16
#define LCD_ROWS            2

const uint8_t  MIN_DUTY_PCT      = 25;   // below this most fans stall
const uint8_t  OFF_THRESHOLD_PCT =  4;   // pot below this = fans off
const uint16_t KICK_MS           = 1200; // spin-up burst (includes the ramp)
const uint16_t RESTART_KICK_MS   = 2200; // longer burst for a restart try
const uint8_t  RAMP_STEP_PCT     =    3; // max duty change per 25 ms tick
const uint8_t  MAX_RESTARTS      =   3;  // tries before latching a fault
const uint16_t STALL_RPM         = 250;  // under this while driven = stalled
const uint8_t  STALL_SECONDS     =   3;  // consecutive seconds before acting
const uint8_t  PULSES_PER_REV    =   2;  // Intel 4-wire spec
const uint16_t FILTER_LIFE_HOURS = 120;  // carbon pad service interval
const uint32_t BACKLIGHT_MS      = 30000UL;  // idle before backlight sleeps
const uint16_t BTN_HOLD_MS       = 2000; // hold time to reset filter hours

/* ------------------------- fixed constants ------------------------ */
const uint8_t  PIN_TACH_A = 2;
const uint8_t  PIN_TACH_B = 3;
const uint8_t  PIN_BTN    = 4;
const uint8_t  PIN_LED_A  = 5;
const uint8_t  PIN_LED_B  = 6;
const uint8_t  PIN_PWM    = 9;
const uint8_t  PIN_POT    = A0;

/* Timer1 TOP for a 25 kHz carrier, derived from whatever crystal is fitted.
   Phase-correct PWM:  f = F_CPU / (2 * prescaler * TOP),  prescaler = 1.
     16 MHz -> TOP = 320      12 MHz -> TOP = 240      8 MHz -> TOP = 160
   F_CPU comes from the board you select in the IDE, so it MUST match the
   crystal on the board or every timing in this sketch will be wrong.
   16 MHz: Board = "Arduino Uno".  12 or 8 MHz: use MiniCore and pick the
   matching clock, then Burn Bootloader once before uploading.            */
const uint16_t PWM_TOP    = (uint16_t)(F_CPU / 50000UL);

const int      EE_MAGIC_ADDR   = 0;
const int      EE_MINUTES_ADDR = 4;
const uint32_t EE_MAGIC        = 0x5FE10001UL;

LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLS, LCD_ROWS);

void updateDisplay();            // forward declaration

/* --------------------------- state -------------------------------- */
volatile uint16_t pulseA = 0, pulseB = 0;
volatile uint32_t lastEdgeA = 0, lastEdgeB = 0;

uint16_t rpmA = 0, rpmB = 0;
uint8_t  dutyPct   = 0;          // what the fans are actually being given
uint8_t  targetPct = 0;          // where the ramp is heading
uint8_t  demandPct = 0;          // what the pot is asking for
bool     faultA = false, faultB = false;
uint8_t  stallCountA = 0, stallCountB = 0;
uint8_t  restartsA = 0, restartsB = 0;
bool     restartPending = false;

bool     kicking = false;
uint32_t kickStart = 0;
uint16_t kickLength = KICK_MS;

int32_t  potAccum = 0;           // pot EMA accumulator, scaled x16
int32_t  potLastSeen = 0;        // for backlight wake detection
uint32_t runSeconds = 0;         // seconds this power-up while running
uint32_t runMinutesTotal = 0;    // lifetime, mirrored in EEPROM
uint32_t lastEepromMinutes = 0;

bool     backlightOn = true;
uint32_t lastActivity = 0;
bool     btnDown = false;
uint32_t btnStart = 0;
bool     resetMsg = false;
uint32_t resetMsgStart = 0;

uint32_t tPot = 0, tTach = 0, tLed = 0, tLcd = 0;
bool     ledPhaseFast = false, ledPhaseSlow = false;
uint8_t  ledTick = 0;
uint8_t  lcdPage = 0;
uint8_t  lcdPageTick = 0;

/* -------------------------- interrupts ---------------------------- */
void isrTachA() {
  uint32_t now = micros();
  if (now - lastEdgeA > 500) { lastEdgeA = now; pulseA++; }   // debounce
}
void isrTachB() {
  uint32_t now = micros();
  if (now - lastEdgeB > 500) { lastEdgeB = now; pulseB++; }
}

/* ------------------------- PWM generation ------------------------- */
void setupPwm25kHz() {
  pinMode(PIN_PWM, OUTPUT);
  // Mode 10: phase-correct PWM, TOP = ICR1.  COM1A1:0 = 11 -> inverting.
  TCCR1A = _BV(COM1A1) | _BV(COM1A0) | _BV(WGM11);
  TCCR1B = _BV(WGM13)  | _BV(CS10);              // no prescaler
  ICR1   = PWM_TOP;
  OCR1A  = 0;                                    // start at 0 %
}

void setDuty(uint8_t pct) {
  if (pct > 100) pct = 100;
  OCR1A = (uint16_t)(((uint32_t)pct * PWM_TOP) / 100UL);
  dutyPct = pct;
}

/* Slew the commanded duty toward targetPct. A fan told to jump straight to
   100 % draws its full starting surge at once; easing it up spreads that
   over most of a second. Note this shapes the FAN's draw only - the inrush
   into C1 when you flip SW1 is separate and is what a slow-blow fuse is for. */
void applyRamp() {
  uint8_t cur = dutyPct;
  if (targetPct > cur) {
    cur = (uint8_t)((targetPct - cur > RAMP_STEP_PCT) ? cur + RAMP_STEP_PCT : targetPct);
  } else if (targetPct < cur) {
    cur = (uint8_t)((cur - targetPct > RAMP_STEP_PCT) ? cur - RAMP_STEP_PCT : targetPct);
  } else {
    return;
  }
  setDuty(cur);
}

void beginKick(uint16_t ms) {
  kicking    = true;
  kickStart  = millis();
  kickLength = ms;
}

/* --------------------------- helpers ------------------------------ */
uint8_t readDemand() {
  // 8x oversample, then a 16x-scaled IIR filter to kill the last of the
  // jitter. The accumulator is kept scaled so that small positive errors
  // are not truncated away by the shift - a plain "x += (raw-x)>>3" can
  // stall up to 7 counts short of the target when the pot is turned up.
  uint16_t acc = 0;
  for (uint8_t i = 0; i < 8; i++) acc += analogRead(PIN_POT);
  int32_t raw = acc >> 3;                       // 0..1023

  potAccum += raw - (potAccum >> 4);            // EMA, time constant ~16
  int32_t filtered = potAccum >> 4;
  if (filtered < 0) filtered = 0;
  if (filtered > 1023) filtered = 1023;

  // any real movement of the knob counts as user activity
  int32_t moved = filtered - potLastSeen;
  if (moved < 0) moved = -moved;
  if (moved > 15) { potLastSeen = filtered; lastActivity = millis(); }

  uint8_t pct = (uint8_t)(((uint32_t)filtered * 100UL) / 1023UL);
  if (pct <= OFF_THRESHOLD_PCT) return 0;
  // remap the usable part of the travel onto MIN_DUTY..100
  uint32_t span = 100UL - OFF_THRESHOLD_PCT;
  uint32_t v = (uint32_t)(pct - OFF_THRESHOLD_PCT) * (100UL - MIN_DUTY_PCT);
  return (uint8_t)(MIN_DUTY_PCT + (v / span));
}

void saveRuntime(bool force) {
  if (force || runMinutesTotal >= lastEepromMinutes + 10) {
    EEPROM.put(EE_MINUTES_ADDR, runMinutesTotal);
    lastEepromMinutes = runMinutesTotal;
  }
}

void loadRuntime() {
  uint32_t magic = 0;
  EEPROM.get(EE_MAGIC_ADDR, magic);
  if (magic != EE_MAGIC) {                      // first run: initialise
    runMinutesTotal = 0;
    EEPROM.put(EE_MINUTES_ADDR, runMinutesTotal);
    EEPROM.put(EE_MAGIC_ADDR, EE_MAGIC);
  } else {
    EEPROM.get(EE_MINUTES_ADDR, runMinutesTotal);
  }
  lastEepromMinutes = runMinutesTotal;
}

/* One fan's health, evaluated once per second.
   Not driven  -> hold whatever we already decided, judge nothing.
   Spinning    -> clear everything, the fan is fine.
   Stalled 3 s -> spend a restart attempt, or latch the fault. */
void evalFan(uint16_t rpm, bool driven,
             uint8_t &stallCount, uint8_t &restarts, bool &fault) {
  if (!driven) { stallCount = 0; return; }

  if (rpm >= STALL_RPM) {
    stallCount = 0;
    restarts   = 0;
    fault      = false;
    return;
  }

  if (stallCount < 255) stallCount++;
  if (stallCount >= STALL_SECONDS && !fault) {
    if (restarts < MAX_RESTARTS) {
      restarts++;
      stallCount     = 0;
      restartPending = true;
    } else {
      fault = true;
    }
  }
}

/* ---------------------------- setup ------------------------------- */
void setup() {
  MCUSR = 0;                                    // clear any reset flags
  wdt_disable();                                // and park the watchdog

  pinMode(PIN_LED_A, OUTPUT);
  pinMode(PIN_LED_B, OUTPUT);
  pinMode(PIN_TACH_A, INPUT);                   // external 10k pull-ups fitted
  pinMode(PIN_TACH_B, INPUT);
  pinMode(PIN_BTN, INPUT_PULLUP);               // reads HIGH if not fitted
  digitalWrite(PIN_LED_A, HIGH);
  digitalWrite(PIN_LED_B, HIGH);

  setupPwm25kHz();

  Wire.begin();
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print(F(" FUME EXTRACTOR "));
  lcd.setCursor(0, 1); lcd.print(F("  SFE-2026 v1.2 "));

  loadRuntime();
  potAccum    = (int32_t)analogRead(PIN_POT) << 4;   // preload the filter
  potLastSeen = potAccum >> 4;

  attachInterrupt(digitalPinToInterrupt(PIN_TACH_A), isrTachA, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_TACH_B), isrTachB, FALLING);

  for (uint8_t p = 0; p <= 100; p += 2) {       // ramped proof-of-life
    setDuty(p);
    delay(16);
  }
  targetPct = 100;
  delay(1150);                                  // ~2 s splash in total

  lcd.clear();
  digitalWrite(PIN_LED_A, LOW);
  digitalWrite(PIN_LED_B, LOW);

  noInterrupts(); pulseA = 0; pulseB = 0; interrupts();
  uint32_t now = millis();
  tPot = tTach = tLed = tLcd = lastActivity = now;

  wdt_enable(WDTO_2S);        // from here on, a hang reboots into 100 %
}

/* ----------------------------- loop ------------------------------- */
void loop() {
  wdt_reset();
  uint32_t now = millis();

  /* ---- 25 ms : pot / demand / spin-up / restart logic ---- */
  if (now - tPot >= 25) {
    tPot = now;
    uint8_t newDemand = readDemand();

    if (newDemand > 0 && demandPct == 0) {      // off -> on transition
      beginKick(KICK_MS);
    }
    demandPct = newDemand;

    if (demandPct == 0) {                       // switched off: forget faults
      kicking = false;
      restartPending = false;
      faultA = faultB = false;
      restartsA = restartsB = 0;
      stallCountA = stallCountB = 0;
      targetPct = 0;
    } else {
      if (restartPending) { restartPending = false; beginKick(RESTART_KICK_MS); }
      if (kicking) {
        targetPct = 100;
        if (now - kickStart >= kickLength) kicking = false;
      } else {
        targetPct = demandPct;
      }
      lastActivity = now;                       // running counts as activity
    }
    applyRamp();                                // ease toward the target
  }

  /* ---- 1000 ms : tachometers, faults, runtime ---- */
  if (now - tTach >= 1000) {
    tTach += 1000;

    noInterrupts();
    uint16_t pa = pulseA, pb = pulseB;
    pulseA = 0; pulseB = 0;
    interrupts();

    rpmA = (uint16_t)((uint32_t)pa * 60UL / PULSES_PER_REV);
    rpmB = (uint16_t)((uint32_t)pb * 60UL / PULSES_PER_REV);

    bool driven = (dutyPct >= MIN_DUTY_PCT);
    evalFan(rpmA, driven, stallCountA, restartsA, faultA);
    evalFan(rpmB, driven, stallCountB, restartsB, faultB);

    if (dutyPct > 0) {
      runSeconds++;
      if (runSeconds >= 60) {
        runSeconds = 0;
        runMinutesTotal++;
        saveRuntime(false);
      }
    }
  }

  /* ---- 125 ms : status LEDs and the reset button ---- */
  if (now - tLed >= 125) {
    tLed = now;
    ledTick++;
    ledPhaseFast = ledTick & 0x01;              // ~4 Hz
    ledPhaseSlow = (ledTick >> 1) & 0x01;       // ~2 Hz

    bool a, b;
    if (dutyPct == 0)      { a = b = false; }
    else if (kicking)      { a = b = ledPhaseSlow; }
    else {
      a = faultA ? ledPhaseFast : true;
      b = faultB ? ledPhaseFast : true;
    }
    digitalWrite(PIN_LED_A, a);
    digitalWrite(PIN_LED_B, b);

    // optional SW2: hold 2 s to zero the filter hour meter
    if (digitalRead(PIN_BTN) == LOW) {
      if (!btnDown) { btnDown = true; btnStart = now; }
      else if (!resetMsg && (now - btnStart >= BTN_HOLD_MS)) {
        runMinutesTotal = 0;
        runSeconds      = 0;
        saveRuntime(true);
        resetMsg      = true;
        resetMsgStart = now;
      }
      lastActivity = now;
    } else {
      btnDown = false;
    }
    if (resetMsg && (now - resetMsgStart >= 2000)) resetMsg = false;
  }

  /* ---- 500 ms : LCD and backlight ---- */
  if (now - tLcd >= 500) {
    tLcd = now;

    bool want = (now - lastActivity) < BACKLIGHT_MS;
    if (want != backlightOn) {
      backlightOn = want;
      if (want) lcd.backlight(); else lcd.noBacklight();
    }
    updateDisplay();
  }
}

/* --------------------------- display ------------------------------ */
void updateDisplay() {
  char buf[LCD_COLS + 1];
  const char *state;

  if      (faultA || faultB) state = "FAULT! ";
  else if (dutyPct == 0)     state = "STOPPED";
  else if (kicking)          state = "STARTUP";
  else if (dutyPct >= 98)    state = "MAXIMUM";
  else                       state = "RUNNING";

  snprintf(buf, sizeof(buf), "Spd:%3u%% %-7s", (unsigned)dutyPct, state);
  lcd.setCursor(0, 0);
  lcd.print(buf);

  // line 2 rotates: RPM for 10 s, then filter hours for 2.5 s
  if (++lcdPageTick >= (lcdPage == 0 ? 20 : 5)) {
    lcdPageTick = 0;
    lcdPage ^= 1;
  }

  if (resetMsg) {
    strcpy(buf, "FILTER HOURS = 0");
  } else if (faultA || faultB) {
    if (faultA && faultB)  strcpy(buf, "!BOTH FANS STOP ");
    else if (faultA)       strcpy(buf, "!FAN A NO SIGNAL");
    else                   strcpy(buf, "!FAN B NO SIGNAL");
  } else if (lcdPage == 0) {
    snprintf(buf, sizeof(buf), "A%4u B%4u rpm ",
             (unsigned)(rpmA > 9999 ? 9999 : rpmA),
             (unsigned)(rpmB > 9999 ? 9999 : rpmB));
  } else {
    uint16_t hours = (uint16_t)(runMinutesTotal / 60UL);
    if (hours > 999) hours = 999;
    if (hours >= FILTER_LIFE_HOURS)
      strcpy(buf, "CHANGE FILTER!  ");
    else
      // exactly 16 columns: 7 + 3 + 1 + 3 + 2
      snprintf(buf, sizeof(buf), "Filter:%3u/%3u h", (unsigned)hours,
               (unsigned)FILTER_LIFE_HOURS);
  }

  lcd.setCursor(0, 1);
  lcd.print(buf);
}

/* =====================================================================
   Free pins for future work: D7, D8, D10-D13, A1, A2, A3.
   Obvious additions: a buzzer on fault (D7), a second pot for a boost
   preset (A1), a thermistor watching the carbon pad (A2).
   ===================================================================== */
