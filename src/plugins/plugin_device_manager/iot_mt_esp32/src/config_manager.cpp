#include "config_manager.h"
#include <WiFi.h>
#include <esp_system.h>

const char* ConfigManager::NAMESPACE = "brewstation";
const char* ConfigManager::KEY_WIFI_SSID = "wifi_ssid";
const char* ConfigManager::KEY_WIFI_PASSWORD = "wifi_pass";
const char* ConfigManager::KEY_WIFI_STATIC_IP = "wifi_static";
const char* ConfigManager::KEY_WIFI_IP = "wifi_ip";
const char* ConfigManager::KEY_WIFI_GATEWAY = "wifi_gw";
const char* ConfigManager::KEY_WIFI_SUBNET = "wifi_sub";
const char* ConfigManager::KEY_WIFI_DNS1 = "wifi_dns1";
const char* ConfigManager::KEY_WIFI_DNS2 = "wifi_dns2";
const char* ConfigManager::KEY_MQTT_ENABLED = "mqtt_en";
const char* ConfigManager::KEY_MQTT_HOST = "mqtt_host";
const char* ConfigManager::KEY_MQTT_PORT = "mqtt_port";
const char* ConfigManager::KEY_MQTT_USERNAME = "mqtt_user";
const char* ConfigManager::KEY_MQTT_PASSWORD = "mqtt_pass";
const char* ConfigManager::KEY_MQTT_DEVICE_ID = "mqtt_devid";
const char* ConfigManager::KEY_MQTT_TOPIC_BASE = "mqtt_base";

ConfigManager::ConfigManager() {
}

ConfigManager::~ConfigManager() {
    end();
}

bool ConfigManager::begin() {
    return preferences.begin(NAMESPACE, false);
}

void ConfigManager::end() {
    preferences.end();
}

bool ConfigManager::loadWiFiConfig(WiFiConfig& config) {
    if (!hasWiFiConfig()) {
        return false;
    }
    
    String ssid = preferences.getString(KEY_WIFI_SSID, "");
    String password = preferences.getString(KEY_WIFI_PASSWORD, "");
    
    if (ssid.length() == 0) {
        return false;
    }
    
    ssid.toCharArray(config.ssid, sizeof(config.ssid));
    password.toCharArray(config.password, sizeof(config.password));
    
    config.useStaticIP = preferences.getBool(KEY_WIFI_STATIC_IP, false);
    
    if (config.useStaticIP) {
        config.ip = IPAddress(preferences.getULong(KEY_WIFI_IP, 0));
        config.gateway = IPAddress(preferences.getULong(KEY_WIFI_GATEWAY, 0));
        config.subnet = IPAddress(preferences.getULong(KEY_WIFI_SUBNET, 0));
        config.dns1 = IPAddress(preferences.getULong(KEY_WIFI_DNS1, 0));
        config.dns2 = IPAddress(preferences.getULong(KEY_WIFI_DNS2, 0));
    }
    
    return true;
}

bool ConfigManager::saveWiFiConfig(const WiFiConfig& config) {
    if (!preferences.putString(KEY_WIFI_SSID, config.ssid)) {
        return false;
    }
    preferences.putString(KEY_WIFI_PASSWORD, config.password);
    preferences.putBool(KEY_WIFI_STATIC_IP, config.useStaticIP);
    
    if (config.useStaticIP) {
        preferences.putULong(KEY_WIFI_IP, (uint32_t)config.ip);
        preferences.putULong(KEY_WIFI_GATEWAY, (uint32_t)config.gateway);
        preferences.putULong(KEY_WIFI_SUBNET, (uint32_t)config.subnet);
        preferences.putULong(KEY_WIFI_DNS1, (uint32_t)config.dns1);
        preferences.putULong(KEY_WIFI_DNS2, (uint32_t)config.dns2);
    }
    
    return true;
}

bool ConfigManager::hasWiFiConfig() {
    String ssid = preferences.getString(KEY_WIFI_SSID, "");
    return ssid.length() > 0;
}

bool ConfigManager::loadMQTTConfig(MQTTConfig& config) {
    config.enabled = preferences.getBool(KEY_MQTT_ENABLED, false);
    
    if (!config.enabled) {
        return false;
    }
    
    String host = preferences.getString(KEY_MQTT_HOST, "");
    if (host.length() == 0) {
        return false;
    }
    
    host.toCharArray(config.host, sizeof(config.host));
    config.port = preferences.getUShort(KEY_MQTT_PORT, 1883);
    
    String username = preferences.getString(KEY_MQTT_USERNAME, "");
    username.toCharArray(config.username, sizeof(config.username));
    
    String password = preferences.getString(KEY_MQTT_PASSWORD, "");
    password.toCharArray(config.password, sizeof(config.password));
    
    String deviceId = preferences.getString(KEY_MQTT_DEVICE_ID, "");
    if (deviceId.length() == 0) {
        deviceId = generateDeviceId();
        preferences.putString(KEY_MQTT_DEVICE_ID, deviceId);
    }
    deviceId.toCharArray(config.deviceId, sizeof(config.deviceId));
    
    String topicBase = preferences.getString(KEY_MQTT_TOPIC_BASE, "brewstation/devices");
    topicBase.toCharArray(config.topicBase, sizeof(config.topicBase));
    
    return true;
}

bool ConfigManager::saveMQTTConfig(const MQTTConfig& config) {
    preferences.putBool(KEY_MQTT_ENABLED, config.enabled);
    
    if (config.enabled) {
        preferences.putString(KEY_MQTT_HOST, config.host);
        preferences.putUShort(KEY_MQTT_PORT, config.port);
        preferences.putString(KEY_MQTT_USERNAME, config.username);
        preferences.putString(KEY_MQTT_PASSWORD, config.password);
        preferences.putString(KEY_MQTT_DEVICE_ID, config.deviceId);
        preferences.putString(KEY_MQTT_TOPIC_BASE, config.topicBase);
    }
    
    return true;
}

bool ConfigManager::hasMQTTConfig() {
    return preferences.getBool(KEY_MQTT_ENABLED, false) && 
           preferences.getString(KEY_MQTT_HOST, "").length() > 0;
}

void ConfigManager::resetAll() {
    preferences.clear();
}

void ConfigManager::resetWiFi() {
    preferences.remove(KEY_WIFI_SSID);
    preferences.remove(KEY_WIFI_PASSWORD);
    preferences.remove(KEY_WIFI_STATIC_IP);
    preferences.remove(KEY_WIFI_IP);
    preferences.remove(KEY_WIFI_GATEWAY);
    preferences.remove(KEY_WIFI_SUBNET);
    preferences.remove(KEY_WIFI_DNS1);
    preferences.remove(KEY_WIFI_DNS2);
}

void ConfigManager::resetMQTT() {
    preferences.remove(KEY_MQTT_ENABLED);
    preferences.remove(KEY_MQTT_HOST);
    preferences.remove(KEY_MQTT_PORT);
    preferences.remove(KEY_MQTT_USERNAME);
    preferences.remove(KEY_MQTT_PASSWORD);
    preferences.remove(KEY_MQTT_DEVICE_ID);
    preferences.remove(KEY_MQTT_TOPIC_BASE);
}

String ConfigManager::generateDeviceId() {
    uint64_t chipId = ESP.getEfuseMac();
    String deviceId = "ESP32_" + String((uint32_t)(chipId >> 32), HEX) + 
                      String((uint32_t)chipId, HEX);
    deviceId.toUpperCase();
    return deviceId;
}
