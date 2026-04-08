#include <Arduino.h>

static const int RPWM = 19;
static const int LPWM = 21;
static const int REN  = 23;
static const int LEN  = 5;

static const int PWM_FREQ = 20000;
static const int PWM_RES  = 8;
static const int PWM_CH_R = 0;
static const int PWM_CH_L = 1;

static const int S1 = 26;
static const int S0 = 27;
static const int CONTRACT_LIMIT_SWITCH = 25;

static const int MOTOR_SPEED = 255;
//String buf;

void motorStop() {
  ledcWrite(PWM_CH_R, 0);
  ledcWrite(PWM_CH_L, 0);
  //Serial.println("MOTOR STOP");
}

void motorRPWM() {
  ledcWrite(PWM_CH_R, MOTOR_SPEED);
  ledcWrite(PWM_CH_L, 0);
  //Serial.println("MOTOR RPWM");
}

void motorLPWM() {
  ledcWrite(PWM_CH_R, 0);
  ledcWrite(PWM_CH_L, MOTOR_SPEED);
  //Serial.println("MOTOR LPWM");
}

bool contractLimitReached() {
  return digitalRead(CONTRACT_LIMIT_SWITCH) == LOW;
}

void setup() {
  pinMode(S1, INPUT_PULLDOWN);
  pinMode(S0, INPUT_PULLDOWN);
  pinMode(CONTRACT_LIMIT_SWITCH, INPUT_PULLUP);

  pinMode(REN, OUTPUT);
  pinMode(LEN, OUTPUT);
  digitalWrite(REN, HIGH);
  digitalWrite(LEN, HIGH);

  ledcSetup(PWM_CH_R, PWM_FREQ, PWM_RES);
  ledcSetup(PWM_CH_L, PWM_FREQ, PWM_RES);
  ledcAttachPin(RPWM, PWM_CH_R);
  ledcAttachPin(LPWM, PWM_CH_L);

  motorStop();
  //Serial.println("READY");
}

void loop() {
  if (digitalRead(S1) == HIGH && digitalRead(S0) == HIGH) {
    motorStop();
  } else
  if (digitalRead(S0) == HIGH) {
    motorRPWM();
  } else if (digitalRead(S1) == HIGH) {
    if (contractLimitReached()) {
      motorStop();
    } else {
      motorLPWM();
    }
  } else {
    motorStop();
  }
}
