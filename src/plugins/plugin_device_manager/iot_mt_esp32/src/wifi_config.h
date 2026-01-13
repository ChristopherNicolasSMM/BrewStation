#ifndef WIFI_CONFIG_H
#define WIFI_CONFIG_H

#include <WiFi.h>
#include <WiFiAP.h>
#include "config_manager.h"

class WiFiManager {
public:
    WiFiManager(ConfigManager& configManager);
    
    bool begin();
    void update();
    
    // AP Mode
    bool startAP();
    void stopAP();
    bool isAPMode();
    
    // Station Mode
    bool connectToWiFi(const WiFiConfig& config);
    bool isConnected();
    IPAddress getIP();
    String getSSID();
    int getRSSI();
    
    // Fallback logic
    void handleFallback();
    bool shouldFallbackToAP();
    
    // Status
    wl_status_t getStatus();

private:
    ConfigManager& configManager;
    bool apMode;
    unsigned long lastConnectionAttempt;
    unsigned long lastStatusCheck;
    static const unsigned long CONNECTION_TIMEOUT = 30000; // 30 segundos
    static const unsigned long STATUS_CHECK_INTERVAL = 10000; // 10 segundos
    static const char* AP_SSID;
    static const IPAddress AP_IP;
    static const IPAddress AP_SUBNET;
    
    bool tryConnect(const WiFiConfig& config);
};

#endif // WIFI_CONFIG_H
