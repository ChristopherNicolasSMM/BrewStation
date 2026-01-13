#include "mqtt_client.h"

MQTTClientManager* MQTTClientManager::instance = nullptr;

MQTTClientManager::MQTTClientManager(ConfigManager& configManager, WiFiClient& wifiClient)
    : configManager(configManager), wifiClient(wifiClient), 
      mqttClient(wifiClient), enabled(false), actuatorCallback(nullptr),
      lastReconnectAttempt(0) {
    instance = this;
}

bool MQTTClientManager::begin() {
    if (!configManager.hasMQTTConfig()) {
        Serial.println("[MQTT] MQTT não configurado");
        return false;
    }
    
    if (!configManager.loadMQTTConfig(mqttConfig)) {
        Serial.println("[MQTT] Erro ao carregar configuração MQTT");
        return false;
    }
    
    enabled = mqttConfig.enabled;
    
    if (!enabled) {
        Serial.println("[MQTT] MQTT desabilitado");
        return false;
    }
    
    mqttClient.setServer(mqttConfig.host, mqttConfig.port);
    mqttClient.setCallback(mqttCallback);
    
    Serial.println("[MQTT] Cliente MQTT inicializado");
    Serial.print("[MQTT] Host: ");
    Serial.print(mqttConfig.host);
    Serial.print(":");
    Serial.println(mqttConfig.port);
    
    return true;
}

void MQTTClientManager::loop() {
    if (!enabled) {
        return;
    }
    
    if (!mqttClient.connected()) {
        unsigned long now = millis();
        if (now - lastReconnectAttempt > RECONNECT_INTERVAL) {
            lastReconnectAttempt = now;
            reconnect();
        }
    } else {
        mqttClient.loop();
    }
}

bool MQTTClientManager::connect() {
    if (!enabled) {
        return false;
    }
    
    if (mqttClient.connected()) {
        return true;
    }
    
    return reconnect();
}

bool MQTTClientManager::reconnect() {
    if (!WiFi.isConnected()) {
        return false;
    }
    
    Serial.print("[MQTT] Tentando conectar ao broker...");
    
    String clientId = getDeviceId();
    String willTopic = getStatusTopic();
    
    bool connected = false;
    
    if (mqttConfig.username[0] != '\0') {
        connected = mqttClient.connect(
            clientId.c_str(),
            mqttConfig.username,
            mqttConfig.password,
            willTopic.c_str(),
            1,
            true,
            "offline"
        );
    } else {
        connected = mqttClient.connect(
            clientId.c_str(),
            willTopic.c_str(),
            1,
            true,
            "offline"
        );
    }
    
    if (connected) {
        Serial.println(" Conectado!");
        
        // Publicar status online
        publishStatus("online");
        
        // Subscrever aos tópicos de atuadores (se houver callback)
        // Isso pode ser expandido para subscrever automaticamente
        // aos atuadores configurados
    } else {
        Serial.print(" Falhou. Estado: ");
        Serial.println(mqttClient.state());
    }
    
    return connected;
}

void MQTTClientManager::disconnect() {
    if (mqttClient.connected()) {
        publishStatus("offline");
        mqttClient.disconnect();
    }
}

bool MQTTClientManager::isConnected() {
    return enabled && mqttClient.connected();
}

bool MQTTClientManager::publishStatus(const String& status) {
    if (!isConnected()) {
        return false;
    }
    
    String topic = getStatusTopic();
    return mqttClient.publish(topic.c_str(), status.c_str(), true);
}

bool MQTTClientManager::publishSensor(const String& port, const String& value) {
    if (!isConnected()) {
        return false;
    }
    
    String topic = getSensorTopic(port);
    return mqttClient.publish(topic.c_str(), value.c_str());
}

bool MQTTClientManager::publishActuatorState(const String& port, const String& state) {
    if (!isConnected()) {
        return false;
    }
    
    String topic = getActuatorStateTopic(port);
    return mqttClient.publish(topic.c_str(), state.c_str(), true);
}

bool MQTTClientManager::subscribeToActuator(const String& port) {
    if (!isConnected()) {
        return false;
    }
    
    String topic = getActuatorSetTopic(port);
    bool result = mqttClient.subscribe(topic.c_str(), 1);
    
    if (result) {
        Serial.print("[MQTT] Inscrito em: ");
        Serial.println(topic);
    }
    
    return result;
}

void MQTTClientManager::setActuatorCallback(void (*callback)(const String& port, const String& value)) {
    actuatorCallback = callback;
}

String MQTTClientManager::getStatusTopic() {
    return getTopicBase() + "/" + getDeviceId() + "/status";
}

String MQTTClientManager::getSensorTopic(const String& port) {
    return getTopicBase() + "/" + getDeviceId() + "/sensor/" + port;
}

String MQTTClientManager::getActuatorSetTopic(const String& port) {
    return getTopicBase() + "/" + getDeviceId() + "/actuator/" + port + "/set";
}

String MQTTClientManager::getActuatorStateTopic(const String& port) {
    return getTopicBase() + "/" + getDeviceId() + "/actuator/" + port + "/state";
}

String MQTTClientManager::getDeviceId() {
    return String(mqttConfig.deviceId);
}

String MQTTClientManager::getTopicBase() {
    return String(mqttConfig.topicBase);
}

void MQTTClientManager::mqttCallback(char* topic, byte* payload, unsigned int length) {
    if (instance == nullptr) {
        return;
    }
    
    String topicStr = String(topic);
    String payloadStr = "";
    
    for (unsigned int i = 0; i < length; i++) {
        payloadStr += (char)payload[i];
    }
    
    Serial.print("[MQTT] Mensagem recebida [");
    Serial.print(topicStr);
    Serial.print("] ");
    Serial.println(payloadStr);
    
    // Verificar se é um tópico de atuador
    String setTopicSuffix = "/set";
    if (topicStr.endsWith(setTopicSuffix)) {
        String port = topicStr.substring(0, topicStr.length() - setTopicSuffix.length());
        int lastSlash = port.lastIndexOf('/');
        if (lastSlash >= 0) {
            port = port.substring(lastSlash + 1);
        }
        
        if (instance->actuatorCallback != nullptr) {
            instance->actuatorCallback(port, payloadStr);
        }
    }
}
