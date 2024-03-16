#include <Arduino.h>
#include "HX711.h"

HX711 scale;

long scale_offset;
double scale_gain = 503.2608;

long encoder_count = 0;

constexpr double kShuntResistance = 0.0005;
constexpr double kGain = 10.0;

void encoder_isr() {
  encoder_count++;
}

void setup() {
  pinMode(PC13, OUTPUT);
  digitalWrite(PC13, HIGH);
  pinMode(PB12, INPUT_PULLUP);
  pinMode(PA1, INPUT_ANALOG);
  attachInterrupt(digitalPinToInterrupt(PB12), encoder_isr, CHANGE);
  Serial.begin(115200);
  scale.begin(PB9, PB10);
  scale.set_gain(64);
  while(!scale.is_ready()) {
    delay(10);
  }
  scale_offset = scale.read();
}

double GetCurrent() {
  int adc = analogRead(PA1);
  double current = (double)adc / 4095.0 * 3.3 / kGain / kShuntResistance;
  return current;
}

void loop() {
  // put your main code here, to run repeatedly:
  delay(20);
  if(scale.is_ready()) {
    Serial.printf("Raw: %10d Weight: %10d Encoder: %10d Raw: %10d Current: %10d\n", (scale.read() - scale_offset),  (long)((double)(scale.read() - scale_offset) / scale_gain), encoder_count, analogRead(PA1), (long)(GetCurrent() * 1000.0));
  } else {
    Serial.println("Scale not ready");
  }
}