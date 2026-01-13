#ifndef UTILS_H
#define UTILS_H

#include <Arduino.h>

#define LED_BUILTIN_PIN 2

class StatusLED {
public:
    StatusLED(int pin = LED_BUILTIN_PIN);
    void begin();
    
    // Status patterns
    void setAPMode();      // Piscando rápido
    void setConnecting();  // Piscando lento
    void setConnected();   // Fixo ligado
    void setError();       // Desligado
    void update();
    
private:
    int pin;
    int mode; // 0=off, 1=fast, 2=slow, 3=on
    unsigned long lastToggle;
    bool state;
    
    static const unsigned long FAST_BLINK = 200;  // 200ms
    static const unsigned long SLOW_BLINK = 1000; // 1000ms
};

#endif // UTILS_H
