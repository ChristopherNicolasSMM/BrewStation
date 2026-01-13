#include "utils.h"

StatusLED::StatusLED(int pin) : pin(pin), mode(0), lastToggle(0), state(false) {
}

void StatusLED::begin() {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);
}

void StatusLED::setAPMode() {
    mode = 1; // Fast blink
}

void StatusLED::setConnecting() {
    mode = 2; // Slow blink
}

void StatusLED::setConnected() {
    mode = 3; // On
    digitalWrite(pin, HIGH);
}

void StatusLED::setError() {
    mode = 0; // Off
    digitalWrite(pin, LOW);
}

void StatusLED::update() {
    unsigned long now = millis();
    
    switch (mode) {
        case 1: // Fast blink
            if (now - lastToggle > FAST_BLINK) {
                state = !state;
                digitalWrite(pin, state ? HIGH : LOW);
                lastToggle = now;
            }
            break;
            
        case 2: // Slow blink
            if (now - lastToggle > SLOW_BLINK) {
                state = !state;
                digitalWrite(pin, state ? HIGH : LOW);
                lastToggle = now;
            }
            break;
            
        case 3: // On
            digitalWrite(pin, HIGH);
            break;
            
        default: // Off
            digitalWrite(pin, LOW);
            break;
    }
}
