#include "wifi_config.h"

const char* WiFiManager::AP_SSID = "ND_BrewStation";
const IPAddress WiFiManager::AP_IP(192, 168, 4, 1);
const IPAddress WiFiManager::AP_SUBNET(255, 255, 255, 0);

WiFiManager::WiFiManager(ConfigManager& configManager) 
    : configManager(configManager), apMode(false), 
      lastConnectionAttempt(0), lastStatusCheck(0) {
}

bool WiFiManager::begin() {
    WiFi.mode(WIFI_AP_STA);
    return true;
}

void WiFiManager::update() {
    unsigned long now = millis();
    
    // Se não está em modo AP e não está conectado, verificar fallback
    if (!apMode && !isConnected()) {
        if (shouldFallbackToAP()) {
            handleFallback();
        }
    }
    
    // Verificar status periodicamente
    if (now - lastStatusCheck > STATUS_CHECK_INTERVAL) {
        lastStatusCheck = now;
        if (!apMode && !isConnected() && shouldFallbackToAP()) {
            handleFallback();
        }
    }
}

bool WiFiManager::startAP() {
    if (apMode) {
        return true;
    }
    
    Serial.println("[WiFi] Iniciando modo AP...");
    
    if (!WiFi.softAP(AP_SSID, "", 1, 0, 4)) {
        Serial.println("[WiFi] Erro ao iniciar AP");
        return false;
    }
    
    delay(100);
    
    if (!WiFi.softAPConfig(AP_IP, AP_IP, AP_SUBNET)) {
        Serial.println("[WiFi] Erro ao configurar AP");
        return false;
    }
    
    apMode = true;
    Serial.print("[WiFi] AP iniciado: ");
    Serial.print(AP_SSID);
    Serial.print(" - IP: ");
    Serial.println(AP_IP);
    
    return true;
}

void WiFiManager::stopAP() {
    if (!apMode) {
        return;
    }
    
    Serial.println("[WiFi] Parando modo AP...");
    WiFi.softAPdisconnect(true);
    apMode = false;
}

bool WiFiManager::isAPMode() {
    return apMode;
}

bool WiFiManager::connectToWiFi(const WiFiConfig& config) {
    if (config.ssid[0] == '\0') {
        Serial.println("[WiFi] SSID vazio");
        return false;
    }
    
    Serial.print("[WiFi] Conectando a: ");
    Serial.println(config.ssid);
    
    lastConnectionAttempt = millis();
    
    // Configurar IP estático se necessário
    if (config.useStaticIP) {
        if (!WiFi.config(config.ip, config.gateway, config.subnet, config.dns1, config.dns2)) {
            Serial.println("[WiFi] Erro ao configurar IP estático");
            return false;
        }
    } else {
        WiFi.config(INADDR_NONE, INADDR_NONE, INADDR_NONE);
    }
    
    // Conectar
    WiFi.begin(config.ssid, config.password);
    
    return tryConnect(config);
}

bool WiFiManager::tryConnect(const WiFiConfig& config) {
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(1000);
        Serial.print(".");
        attempts++;
        
        // Timeout
        if (millis() - lastConnectionAttempt > CONNECTION_TIMEOUT) {
            Serial.println("\n[WiFi] Timeout de conexão");
            WiFi.disconnect();
            return false;
        }
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[WiFi] Conectado!");
        Serial.print("[WiFi] IP: ");
        Serial.println(WiFi.localIP());
        Serial.print("[WiFi] RSSI: ");
        Serial.println(WiFi.RSSI());
        return true;
    }
    
    Serial.println("\n[WiFi] Falha na conexão");
    WiFi.disconnect();
    return false;
}

bool WiFiManager::isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

IPAddress WiFiManager::getIP() {
    if (apMode) {
        return AP_IP;
    }
    return WiFi.localIP();
}

String WiFiManager::getSSID() {
    if (apMode) {
        return String(AP_SSID);
    }
    return WiFi.SSID();
}

int WiFiManager::getRSSI() {
    if (apMode) {
        return 0;
    }
    return WiFi.RSSI();
}

bool WiFiManager::shouldFallbackToAP() {
    // Se passou o timeout desde a última tentativa de conexão
    if (millis() - lastConnectionAttempt > CONNECTION_TIMEOUT) {
        return true;
    }
    return false;
}

void WiFiManager::handleFallback() {
    if (apMode) {
        return;
    }
    
    Serial.println("[WiFi] Fallback para modo AP");
    WiFi.disconnect();
    delay(500);
    startAP();
}

wl_status_t WiFiManager::getStatus() {
    return WiFi.status();
}
