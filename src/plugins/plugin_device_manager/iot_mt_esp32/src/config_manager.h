#ifndef CONFIG_MANAGER_H
#define CONFIG_MANAGER_H

#include <Preferences.h>
#include <IPAddress.h>

struct WiFiConfig {
    char ssid[64];
    char password[64];
    bool useStaticIP;
    IPAddress ip;
    IPAddress gateway;
    IPAddress subnet;
    IPAddress dns1;
    IPAddress dns2;
};

struct MQTTConfig {
    bool enabled;
    char host[128];
    uint16_t port;
    char username[64];
    char password[64];
    char deviceId[64];
    char topicBase[128];
};

class ConfigManager {
public:
    ConfigManager();
    ~ConfigManager();
    
    bool begin();
    void end();
    
    // WiFi configuration
    bool loadWiFiConfig(WiFiConfig& config);
    bool saveWiFiConfig(const WiFiConfig& config);
    bool hasWiFiConfig();
    
    // MQTT configuration
    bool loadMQTTConfig(MQTTConfig& config);
    bool saveMQTTConfig(const MQTTConfig& config);
    bool hasMQTTConfig();
    
    // Reset
    void resetAll();
    void resetWiFi();
    void resetMQTT();
    
    // Generate device ID
    String generateDeviceId();

private:
    Preferences preferences;
    static const char* NAMESPACE;
    static const char* KEY_WIFI_SSID;
    static const char* KEY_WIFI_PASSWORD;
    static const char* KEY_WIFI_STATIC_IP;
    static const char* KEY_WIFI_IP;
    static const char* KEY_WIFI_GATEWAY;
    static const char* KEY_WIFI_SUBNET;
    static const char* KEY_WIFI_DNS1;
    static const char* KEY_WIFI_DNS2;
    static const char* KEY_MQTT_ENABLED;
    static const char* KEY_MQTT_HOST;
    static const char* KEY_MQTT_PORT;
    static const char* KEY_MQTT_USERNAME;
    static const char* KEY_MQTT_PASSWORD;
    static const char* KEY_MQTT_DEVICE_ID;
    static const char* KEY_MQTT_TOPIC_BASE;
};

#endif // CONFIG_MANAGER_H
