# ImplementaÃ§Ã£o para DHT22/DHT11
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dht_sensor.py
Implementação para sensores DHT11/DHT22 (temperatura e umidade).
Utiliza a biblioteca Adafruit_DHT.
"""

import Adafruit_DHT

from src.core.constants import UNIT_CELSIUS, UNIT_PERCENT
from src.sensors.base_sensor import BaseSensor


class DHTSensor(BaseSensor):
    """
    Sensor DHT22/DHT11 para temperatura e umidade.
    """
    
    # Mapeamento de tipos de sensor para constantes da biblioteca
    SENSOR_TYPES = {
        'dht11': Adafruit_DHT.DHT11,
        'dht22': Adafruit_DHT.DHT22
    }
    
    def __init__(self, name: str, config: dict, gpio_pin: int):
        """
        Inicializa o sensor DHT.
        
        Args:
            name: Nome do sensor
            config: Configurações do sensor
            gpio_pin: Número do pino GPIO (BCM)
        """
        super().__init__(name, config)
        
        self.gpio_pin = gpio_pin
        sensor_type = config.get('type', 'dht22').lower()
        
        # Seleciona o tipo de sensor
        if sensor_type in self.SENSOR_TYPES:
            self.dht_type = self.SENSOR_TYPES[sensor_type]
        else:
            self.logger.warning(f"Tipo de sensor '{sensor_type}' não reconhecido, usando DHT22")
            self.dht_type = Adafruit_DHT.DHT22
        
        self.logger.info(f"Sensor DHT configurado no GPIO {gpio_pin} (tipo: {sensor_type})")
    
    def read_raw(self):
        """
        Lê o sensor DHT.
        
        Returns:
            Tupla (umidade, temperatura) ou None em caso de erro
        """
        umidade, temperatura = Adafruit_DHT.read_retry(self.dht_type, self.gpio_pin)
        
        if umidade is None or temperatura is None:
            raise ValueError("Falha na leitura do sensor DHT")
        
        # Arredonda para 1 casa decimal
        return {
            'temperature': round(temperatura, 1),
            'humidity': round(umidade, 1)
        }
    
    def _process_value(self, raw_value):
        """
        Processa o valor para o formato padrão.
        O DHT retorna dois valores (temp e umidade).
        """
        return {
            'temperature': raw_value['temperature'],
            'humidity': raw_value['humidity']
        }
    
    def _get_unit(self):
        """Retorna as unidades de medida."""
        return {
            'temperature': UNIT_CELSIUS,
            'humidity': UNIT_PERCENT
        }