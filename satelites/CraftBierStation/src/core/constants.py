#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
constants.py
Definições de constantes do sistema para mapeamento de dispositivos.
Estas constantes devem ser usadas em todo o código para referenciar
sensores e atuadores de forma consistente.
"""

# =============================================================================
# CONSTANTES DE SENSORES
# =============================================================================
# Use estas constantes para referenciar sensores no código
# O ConfigManager fará o mapeamento para os pinos GPIO reais

# Sensores de temperatura
SENSOR_TEMP_MOSTURA = "SENSOR_TEMP_MOSTURA"      # Temperatura da mostura
SENSOR_TEMP_MASH = "SENSOR_TEMP_MASH"             # Temperatura do mash
SENSOR_TEMP_AMBIENTE = "SENSOR_TEMP_AMBIENTE"     # Temperatura ambiente
SENSOR_TEMP_CALDEIRA = "SENSOR_TEMP_CALDEIRA"     # Temperatura da caldeira
SENSOR_TEMP_FERMENTACAO = "SENSOR_TEMP_FERMENTACAO" # Temperatura de fermentação

# Sensores de nível e presença
SENSOR_NIVEL_TANQUE = "SENSOR_NIVEL_TANQUE"       # Nível do tanque
SENSOR_NIVEL_MOSTURA = "SENSOR_NIVEL_MOSTURA"     # Nível da mostura
SENSOR_PRESSAO = "SENSOR_PRESSAO"                  # Sensor de pressão
SENSOR_FLUXO = "SENSOR_FLUXO"                      # Sensor de fluxo
SENSOR_PH = "SENSOR_PH"                            # Sensor de pH

# =============================================================================
# CONSTANTES DE ATUADORES
# =============================================================================
# Atuadores controláveis pelo sistema

ATUADOR_AQUECEDOR = "ATUADOR_AQUECEDOR"           # Aquecedor principal
ATUADOR_BOMBA = "ATUADOR_BOMBA"                    # Bomba de recirculação
ATUADOR_VALVULA = "ATUADOR_VALVULA"                # Válvula solenoide
ATUADOR_RESISTENCIA = "ATUADOR_RESISTENCIA"        # Resistência elétrica
ATUADOR_AGITADOR = "ATUADOR_AGITADOR"              # Agitador mecânico
ATUADOR_RESFRIADOR = "ATUADOR_RESFRIADOR"          # Sistema de resfriamento

# =============================================================================
# ESTADOS DOS ATUADORES
# =============================================================================
STATE_ON = "on"                    # Atuador ligado
STATE_OFF = "off"                   # Atuador desligado
STATE_AUTO = "auto"                 # Modo automático
STATE_MANUAL = "manual"             # Modo manual

# =============================================================================
# TÓPICOS MQTT PADRÃO
# =============================================================================
MQTT_TOPIC_TEMPERATURA = "sensor/temperatura"
MQTT_TOPIC_UMIDADE = "sensor/umidade"
MQTT_TOPIC_NIVEL = "sensor/nivel"
MQTT_TOPIC_PRESSAO = "sensor/pressao"
MQTT_TOPIC_FLUXO = "sensor/fluxo"
MQTT_TOPIC_ATUADOR_SET = "atuador/set"
MQTT_TOPIC_ATUADOR_STATUS = "atuador/status"

# =============================================================================
# UNIDADES DE MEDIDA
# =============================================================================
UNIT_CELSIUS = "celsius"
UNIT_FAHRENHEIT = "fahrenheit"
UNIT_PERCENT = "percent"
UNIT_LITERS = "liters"
UNIT_LPM = "liters_per_minute"      # Litros por minuto (fluxo)
UNIT_BAR = "bar"                     # Pressão
UNIT_PH = "ph"                       # pH

# =============================================================================
# CÓDIGOS DE ERRO
# =============================================================================
ERROR_SENSOR_READ = "ERR_SENSOR_READ"       # Erro na leitura do sensor
ERROR_SENSOR_CONFIG = "ERR_SENSOR_CONFIG"    # Erro na configuração
ERROR_GPIO = "ERR_GPIO"                      # Erro no GPIO
ERROR_MQTT = "ERR_MQTT"                      # Erro no MQTT
ERROR_HTTP = "ERR_HTTP"                      # Erro no HTTP