# Criação das pastas
$folders = @(
    "src/core",
    "src/interfaces",
    "src/sensors",
    "src/actuators",
    "config"
)

foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-Host "Pasta criada: $folder" -ForegroundColor Cyan
    }
}

# Definição dos arquivos e seus conteúdos iniciais (comentários)
$files = @{
    "src/core/config_manager.py"    = "# Lê e interpreta o arquivo .conf"
    "src/core/device_manager.py"    = "# Gerencia a interface com os GPIOs"
    "src/core/constants.py"         = "# Constantes do sistema (SENSOR_TEMP_MOSTURA, etc.)"
    "src/interfaces/mqtt_interface.py" = "# Gerencia a comunicação MQTT (cliente/broker)"
    "src/interfaces/rest_api.py"      = "# Servidor Flask com a REST API"
    "src/sensors/base_sensor.py"      = "# Classe base para todos os sensores"
    "src/sensors/dht_sensor.py"       = "# Implementação para DHT22/DHT11"
    "src/sensors/ds18b20_sensor.py"   = "# Implementação para DS18B20 (1-Wire)"
    "src/sensors/gpio_sensor.py"      = "# Sensor digital simples (booleano)"
    "src/actuators/base_actuator.py"  = "# Classe base para atuadores"
    "src/actuators/gpio_actuator.py"  = "# Controle digital de GPIO (on/off)"
    "config/device_manager.conf"      = "# Arquivo de configuração principal"
    "server.py"                       = "# Ponto de entrada principal"
}

# Criação dos arquivos
foreach ($file in $files.GetEnumerator()) {
    if (!(Test-Path $file.Key)) {
        $file.Value | Out-File -FilePath $file.Key -Encoding utf8
        Write-Host "Arquivo criado: $($file.Key)" -ForegroundColor Green
    } else {
        Write-Host "Arquivo já existe: $($file.Key)" -ForegroundColor Yellow
    }
}

Write-Host "`nEstrutura do Plugin Device Server gerada com sucesso!" -ForegroundColor White -BackgroundColor DarkGreen