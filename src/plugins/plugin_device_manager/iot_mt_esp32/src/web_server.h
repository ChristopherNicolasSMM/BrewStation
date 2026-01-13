#ifndef WEB_SERVER_H
#define WEB_SERVER_H

#include <WiFi.h>
#include <WebServer.h>
#include <SPIFFS.h>
#include <ArduinoJson.h>
#include "config_manager.h"
#include "wifi_config.h"

class WebConfigServer {
public:
    WebConfigServer(ConfigManager& configManager, WiFiManager& wifiManager);
    
    bool begin();
    void handleClient();
    
    // Routes
    void handleRoot();
    void handleConfig();
    void handleStatus();
    void handleReset();
    void handleNotFound();
    
private:
    ConfigManager& configManager;
    WiFiManager& wifiManager;
    WebServer server;
    
    String getContentType(String filename);
    bool handleFileRead(String path);
    void sendJSON(int code, const JsonDocument& doc);
    void sendError(const String& message);
    void parseIPAddress(const String& ipStr, IPAddress& ip);
    String IPAddressToString(const IPAddress& ip);
};

#endif // WEB_SERVER_H
