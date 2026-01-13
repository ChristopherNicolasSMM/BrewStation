#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#include <WiFi.h>
#include <PubSubClient.h>
#include "config_manager.h"

class MQTTClientManager {
public:
    MQTTClientManager(ConfigManager& configManager, WiFiClient& wifiClient);
    
    bool begin();
    void loop();
    bool connect();
    void disconnect();
    bool isConnected();
    
    // Publishing
    bool publishStatus(const String& status);
    bool publishSensor(const String& port, const String& value);
    bool publishActuatorState(const String& port, const String& state);
    
    // Subscribing
    bool subscribeToActuator(const String& port);
    void setActuatorCallback(void (*callback)(const String& port, const String& value));
    
    // Topics
    String getStatusTopic();
    String getSensorTopic(const String& port);
    String getActuatorSetTopic(const String& port);
    String getActuatorStateTopic(const String& port);

private:
    ConfigManager& configManager;
    WiFiClient& wifiClient;
    PubSubClient mqttClient;
    MQTTConfig mqttConfig;
    bool enabled;
    
    void (*actuatorCallback)(const String& port, const String& value);
    
    static void mqttCallback(char* topic, byte* payload, unsigned int length);
    static MQTTClientManager* instance;
    
    String getDeviceId();
    String getTopicBase();
    void reconnect();
    unsigned long lastReconnectAttempt;
    static const unsigned long RECONNECT_INTERVAL = 5000; // 5 segundos
};

#endif // MQTT_CLIENT_H
