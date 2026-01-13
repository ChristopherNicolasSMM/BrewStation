#include <Arduino.h>
#include "config_manager.h"
#include "wifi_config.h"
#include "web_server.h"
#include "mqtt_client.h"
#include "utils.h"

// Instâncias globais
ConfigManager configManager;
WiFiManager wifiManager(configManager);
WebConfigServer webServer(configManager, wifiManager);
WiFiClient wifiClient;
MQTTClientManager mqttClient(configManager, wifiClient);
StatusLED statusLED;

// Flag para reset de fábrica (botão BOOT)
#define BOOT_BUTTON_PIN 0
unsigned long bootButtonPressTime = 0;
const unsigned long FACTORY_RESET_TIME = 10000; // 10 segundos

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n\n=== ND_BrewStation ===");
    Serial.println("New Device Brew Station");
    Serial.println("=======================\n");
    
    // Inicializar LED de status
    statusLED.begin();
    statusLED.setConnecting();
    
    // Verificar reset de fábrica (botão BOOT durante boot)
    pinMode(BOOT_BUTTON_PIN, INPUT_PULLUP);
    if (digitalRead(BOOT_BUTTON_PIN) == LOW) {
        Serial.println("[Boot] Botão BOOT pressionado - verificando reset de fábrica...");
        unsigned long startTime = millis();
        while (digitalRead(BOOT_BUTTON_PIN) == LOW && (millis() - startTime < FACTORY_RESET_TIME)) {
            delay(100);
        }
        if (millis() - startTime >= FACTORY_RESET_TIME) {
            Serial.println("[Boot] RESET DE FÁBRICA - Limpando todas as configurações!");
            if (configManager.begin()) {
                configManager.resetAll();
                configManager.end();
            }
        }
    }
    
    // Inicializar gerenciador de configurações
    if (!configManager.begin()) {
        Serial.println("[Boot] ERRO: Não foi possível inicializar ConfigManager");
        statusLED.setError();
        return;
    }
    
    // Inicializar WiFi
    if (!wifiManager.begin()) {
        Serial.println("[Boot] ERRO: Não foi possível inicializar WiFiManager");
        statusLED.setError();
        return;
    }
    
    // Tentar carregar e conectar WiFi
    WiFiConfig wifiConfig;
    bool hasWiFiConfig = configManager.loadWiFiConfig(wifiConfig);
    
    if (hasWiFiConfig) {
        Serial.println("[Boot] Configuração WiFi encontrada, tentando conectar...");
        statusLED.setConnecting();
        
        if (wifiManager.connectToWiFi(wifiConfig)) {
            Serial.println("[Boot] WiFi conectado com sucesso!");
            statusLED.setConnected();
            wifiManager.stopAP();
        } else {
            Serial.println("[Boot] Falha ao conectar WiFi, iniciando modo AP...");
            statusLED.setAPMode();
            wifiManager.startAP();
        }
    } else {
        Serial.println("[Boot] Nenhuma configuração WiFi encontrada, iniciando modo AP...");
        statusLED.setAPMode();
        wifiManager.startAP();
    }
    
    // Inicializar servidor web (sempre ativo)
    if (!webServer.begin()) {
        Serial.println("[Boot] ERRO: Não foi possível inicializar WebServer");
        statusLED.setError();
        return;
    }
    
    Serial.println("[Boot] Servidor web iniciado");
    Serial.print("[Boot] Acesse: http://");
    Serial.println(wifiManager.getIP());
    
    // Inicializar MQTT (se configurado)
    if (configManager.hasMQTTConfig()) {
        Serial.println("[Boot] Configuração MQTT encontrada");
        if (mqttClient.begin()) {
            Serial.println("[Boot] Cliente MQTT inicializado");
            if (wifiManager.isConnected()) {
                mqttClient.connect();
            }
        }
    } else {
        Serial.println("[Boot] MQTT não configurado");
    }
    
    Serial.println("\n[Boot] Inicialização concluída!\n");
}

void loop() {
    // Atualizar LED de status
    statusLED.update();
    
    // Atualizar WiFi (verificar fallback)
    wifiManager.update();
    
    // Atualizar status do LED baseado no estado WiFi
    if (wifiManager.isAPMode()) {
        statusLED.setAPMode();
    } else if (wifiManager.isConnected()) {
        statusLED.setConnected();
        
        // Tentar conectar MQTT se não estiver conectado
        if (!mqttClient.isConnected() && configManager.hasMQTTConfig()) {
            mqttClient.connect();
        }
    } else {
        statusLED.setConnecting();
    }
    
    // Processar requisições web
    webServer.handleClient();
    
    // Loop MQTT
    mqttClient.loop();
    
    // Pequeno delay para evitar sobrecarga
    delay(10);
}
