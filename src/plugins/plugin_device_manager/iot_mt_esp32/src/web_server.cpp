#include "web_server.h"
#include <FS.h>

WebConfigServer::WebConfigServer(ConfigManager& configManager, WiFiManager& wifiManager)
    : configManager(configManager), wifiManager(wifiManager), server(80) {
}

bool WebConfigServer::begin() {
    // Inicializar SPIFFS
    if (!SPIFFS.begin(true)) {
        Serial.println("[WebServer] Erro ao montar SPIFFS");
        return false;
    }
    
    // Configurar rotas
    server.on("/", HTTP_GET, [this]() { this->handleRoot(); });
    server.on("/config", HTTP_POST, [this]() { this->handleConfig(); });
    server.on("/status", HTTP_GET, [this]() { this->handleStatus(); });
    server.on("/reset", HTTP_GET, [this]() { this->handleReset(); });
    server.onNotFound([this]() { this->handleNotFound(); });
    
    server.begin();
    Serial.println("[WebServer] Servidor iniciado na porta 80");
    
    return true;
}

void WebConfigServer::handleClient() {
    server.handleClient();
}

void WebConfigServer::handleRoot() {
    if (handleFileRead("/index.html")) {
        return;
    }
    
    // Se não encontrar arquivo, enviar página HTML inline
    String html = F("<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>ND_BrewStation - Configuração</title><style>body{font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f5f5f5}form{background:white;padding:20px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}.form-group{margin-bottom:15px}label{display:block;margin-bottom:5px;font-weight:bold}input,select{width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;box-sizing:border-box}button{background:#007bff;color:white;padding:10px 20px;border:none;border-radius:4px;cursor:pointer;margin-right:10px}button:hover{background:#0056b3}.btn-danger{background:#dc3545}.btn-danger:hover{background:#c82333}.status{margin-top:20px;padding:15px;border-radius:4px;background:#d4edda;border:1px solid #c3e6cb}</style></head><body><h1>Configuração ND_BrewStation</h1><form id='configForm'><h2>WiFi</h2><div class='form-group'><label>SSID:</label><input type='text' name='wifi_ssid' required></div><div class='form-group'><label>Senha:</label><input type='password' name='wifi_password'></div><div class='form-group'><label><input type='checkbox' id='use_static' onchange='toggleStatic()'> Usar IP Estático</label></div><div id='static_ip' style='display:none'><div class='form-group'><label>IP:</label><input type='text' name='wifi_ip' placeholder='192.168.1.100'></div><div class='form-group'><label>Gateway:</label><input type='text' name='wifi_gateway' placeholder='192.168.1.1'></div><div class='form-group'><label>Máscara:</label><input type='text' name='wifi_subnet' placeholder='255.255.255.0'></div><div class='form-group'><label>DNS:</label><input type='text' name='wifi_dns' placeholder='8.8.8.8'></div></div><h2>MQTT (Opcional)</h2><div class='form-group'><label><input type='checkbox' id='mqtt_enabled' onchange='toggleMQTT()'> Habilitar MQTT</label></div><div id='mqtt_config' style='display:none'><div class='form-group'><label>Host:</label><input type='text' name='mqtt_host'></div><div class='form-group'><label>Porta:</label><input type='number' name='mqtt_port' value='1883'></div><div class='form-group'><label>Usuário:</label><input type='text' name='mqtt_username'></div><div class='form-group'><label>Senha:</label><input type='password' name='mqtt_password'></div><div class='form-group'><label>Device ID:</label><input type='text' name='mqtt_device_id' placeholder='Auto-gerado se vazio'></div><div class='form-group'><label>Tópico Base:</label><input type='text' name='mqtt_topic_base' value='brewstation/devices'></div></div><button type='submit'>Salvar</button><button type='button' class='btn-danger' onclick='resetConfig()'>Resetar</button></form><div id='status'></div><script>function toggleStatic(){document.getElementById('static_ip').style.display=document.getElementById('use_static').checked?'block':'none'}function toggleMQTT(){document.getElementById('mqtt_config').style.display=document.getElementById('mqtt_enabled').checked?'block':'none'}function resetConfig(){if(confirm('Resetar todas as configurações?')){fetch('/reset').then(r=>r.json()).then(d=>{alert(d.message);location.reload()})}}document.getElementById('configForm').addEventListener('submit',function(e){e.preventDefault();const formData=new FormData(this);fetch('/config',{method:'POST',body:formData}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<div class=\"status\">'+d.message+'</div>';if(d.success)setTimeout(()=>location.reload(),2000)})})</script></body></html>");
    server.send(200, "text/html", html);
}

void WebConfigServer::handleConfig() {
    Serial.println("[WebServer] Recebendo configuração...");
    
    WiFiConfig wifiConfig = {};
    MQTTConfig mqttConfig = {};
    
    // WiFi
    String ssid = server.arg("wifi_ssid");
    String password = server.arg("wifi_password");
    
    if (ssid.length() > 0) {
        ssid.toCharArray(wifiConfig.ssid, sizeof(wifiConfig.ssid));
        password.toCharArray(wifiConfig.password, sizeof(wifiConfig.password));
        
        wifiConfig.useStaticIP = server.hasArg("use_static");
        
        if (wifiConfig.useStaticIP) {
            parseIPAddress(server.arg("wifi_ip"), wifiConfig.ip);
            parseIPAddress(server.arg("wifi_gateway"), wifiConfig.gateway);
            parseIPAddress(server.arg("wifi_subnet"), wifiConfig.subnet);
            parseIPAddress(server.arg("wifi_dns"), wifiConfig.dns1);
        }
        
        if (!configManager.saveWiFiConfig(wifiConfig)) {
            sendError("Erro ao salvar configuração WiFi");
            return;
        }
    }
    
    // MQTT
    mqttConfig.enabled = server.hasArg("mqtt_enabled");
    
    if (mqttConfig.enabled) {
        String host = server.arg("mqtt_host");
        if (host.length() > 0) {
            host.toCharArray(mqttConfig.host, sizeof(mqttConfig.host));
            mqttConfig.port = server.arg("mqtt_port").toInt();
            if (mqttConfig.port == 0) mqttConfig.port = 1883;
            
            server.arg("mqtt_username").toCharArray(mqttConfig.username, sizeof(mqttConfig.username));
            server.arg("mqtt_password").toCharArray(mqttConfig.password, sizeof(mqttConfig.password));
            
            String deviceId = server.arg("mqtt_device_id");
            if (deviceId.length() == 0) {
                deviceId = configManager.generateDeviceId();
            }
            deviceId.toCharArray(mqttConfig.deviceId, sizeof(mqttConfig.deviceId));
            
            String topicBase = server.arg("mqtt_topic_base");
            if (topicBase.length() == 0) {
                topicBase = "brewstation/devices";
            }
            topicBase.toCharArray(mqttConfig.topicBase, sizeof(mqttConfig.topicBase));
            
            if (!configManager.saveMQTTConfig(mqttConfig)) {
                sendError("Erro ao salvar configuração MQTT");
                return;
            }
        }
    } else {
        configManager.resetMQTT();
    }
    
    StaticJsonDocument<200> doc;
    doc["success"] = true;
    doc["message"] = "Configuração salva! Reiniciando...";
    sendJSON(200, doc);
    
    delay(1000);
    ESP.restart();
}

void WebConfigServer::handleStatus() {
    StaticJsonDocument<512> doc;
    
    doc["wifi"]["connected"] = wifiManager.isConnected();
    doc["wifi"]["ssid"] = wifiManager.getSSID();
    doc["wifi"]["ip"] = IPAddressToString(wifiManager.getIP());
    doc["wifi"]["rssi"] = wifiManager.getRSSI();
    doc["wifi"]["ap_mode"] = wifiManager.isAPMode();
    
    MQTTConfig mqttConfig;
    doc["mqtt"]["enabled"] = configManager.hasMQTTConfig();
    if (configManager.loadMQTTConfig(mqttConfig)) {
        doc["mqtt"]["host"] = mqttConfig.host;
        doc["mqtt"]["port"] = mqttConfig.port;
        doc["mqtt"]["device_id"] = mqttConfig.deviceId;
    }
    
    sendJSON(200, doc);
}

void WebConfigServer::handleReset() {
    configManager.resetAll();
    
    StaticJsonDocument<200> doc;
    doc["success"] = true;
    doc["message"] = "Configurações resetadas! Reiniciando...";
    sendJSON(200, doc);
    
    delay(1000);
    ESP.restart();
}

void WebConfigServer::handleNotFound() {
    if (handleFileRead(server.uri())) {
        return;
    }
    
    String message = "Arquivo não encontrado\n\n";
    message += "URI: ";
    message += server.uri();
    message += "\nMethod: ";
    message += (server.method() == HTTP_GET) ? "GET" : "POST";
    message += "\nArguments: ";
    message += server.args();
    message += "\n";
    
    for (uint8_t i = 0; i < server.args(); i++) {
        message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
    }
    
    server.send(404, "text/plain", message);
}

String WebConfigServer::getContentType(String filename) {
    if (filename.endsWith(".html")) return "text/html";
    else if (filename.endsWith(".css")) return "text/css";
    else if (filename.endsWith(".js")) return "application/javascript";
    else if (filename.endsWith(".png")) return "image/png";
    else if (filename.endsWith(".jpg")) return "image/jpeg";
    else if (filename.endsWith(".gif")) return "image/gif";
    else if (filename.endsWith(".ico")) return "image/x-icon";
    return "text/plain";
}

bool WebConfigServer::handleFileRead(String path) {
    if (path.endsWith("/")) {
        path += "index.html";
    }
    
    String contentType = getContentType(path);
    String pathWithGz = path + ".gz";
    
    if (SPIFFS.exists(pathWithGz) || SPIFFS.exists(path)) {
        if (SPIFFS.exists(pathWithGz)) {
            path = pathWithGz;
        }
        
        File file = SPIFFS.open(path, "r");
        server.streamFile(file, contentType);
        file.close();
        return true;
    }
    
    return false;
}

void WebConfigServer::sendJSON(int code, const JsonDocument& doc) {
    String response;
    serializeJson(doc, response);
    server.send(code, "application/json", response);
}

void WebConfigServer::sendError(const String& message) {
    StaticJsonDocument<200> doc;
    doc["success"] = false;
    doc["message"] = message;
    sendJSON(400, doc);
}

void WebConfigServer::parseIPAddress(const String& ipStr, IPAddress& ip) {
    int parts[4];
    int partIndex = 0;
    String part = "";
    
    for (int i = 0; i < ipStr.length(); i++) {
        if (ipStr[i] == '.' || i == ipStr.length() - 1) {
            if (i == ipStr.length() - 1) {
                part += ipStr[i];
            }
            parts[partIndex++] = part.toInt();
            part = "";
            if (partIndex >= 4) break;
        } else {
            part += ipStr[i];
        }
    }
    
    if (partIndex == 4) {
        ip = IPAddress(parts[0], parts[1], parts[2], parts[3]);
    }
}

String WebConfigServer::IPAddressToString(const IPAddress& ip) {
    return String(ip[0]) + "." + String(ip[1]) + "." + String(ip[2]) + "." + String(ip[3]);
}
