# ImplementaÃ§Ã£o para DS18B20 (1-Wire)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ds18b20_sensor.py
Implementação para sensores DS18B20 (temperatura 1-Wire).
Estes sensores são muito comuns para medição de temperatura em brassagem.
"""

import glob
import os
import time

from src.core.constants import UNIT_CELSIUS
from src.sensors.base_sensor import BaseSensor


class DS18B20Sensor(BaseSensor):
    """
    Sensor de temperatura DS18B20 usando protocolo 1-Wire.
    """
    
    # Base directory para dispositivos 1-Wire no Raspberry Pi
    W1_DEVICE_BASE = "/sys/bus/w1/devices/"
    
    def __init__(self, name: str, config: dict, device_id: str):
        """
        Inicializa o sensor DS18B20.
        
        Args:
            name: Nome do sensor
            config: Configurações do sensor
            device_id: ID do dispositivo (ex: 28-000006d5a2e5)
        """
        super().__init__(name, config)
        
        self.device_id = device_id
        self.device_path = os.path.join(self.W1_DEVICE_BASE, device_id, "w1_slave")
        
        # Verifica se o dispositivo existe
        if not os.path.exists(self.device_path):
            self.logger.error(f"Dispositivo DS18B20 não encontrado: {self.device_path}")
            self.logger.info("Para encontrar dispositivos: ls /sys/bus/w1/devices/")
            raise FileNotFoundError(f"Dispositivo DS18B20 {device_id} não encontrado")
        
        self.logger.info(f"Sensor DS18B20 configurado: {device_id}")
    
    def read_raw(self) -> float:
        """
        Lê a temperatura do sensor DS18B20.
        
        Returns:
            Temperatura em Celsius
        
        Raises:
            IOError: Se houver erro na leitura do arquivo
            ValueError: Se o valor lido for inválido
        """
        try:
            with open(self.device_path, 'r') as f:
                lines = f.readlines()
            
            # Verifica se a leitura foi bem-sucedida (deve terminar com YES)
            if lines[0].strip()[-3:] != "YES":
                time.sleep(0.2)  # Pequena pausa e tenta novamente
                with open(self.device_path, 'r') as f:
                    lines = f.readlines()
                if lines[0].strip()[-3:] != "YES":
                    raise IOError("Leitura do DS18B20 falhou: CRC inválido")
            
            # Extrai a temperatura da segunda linha
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_celsius = float(temp_string) / 1000.0
                return round(temp_celsius, 2)
            else:
                raise ValueError("Formato de temperatura não encontrado")
                
        except Exception as e:
            self.logger.error(f"Erro na leitura do DS18B20: {e}")
            raise
    
    def _get_unit(self) -> str:
        """Retorna a unidade de medida (Celsius)."""
        return UNIT_CELSIUS
    
    @classmethod
    def list_devices(cls):
        """
        Lista todos os dispositivos DS18B20 encontrados no sistema.
        
        Returns:
            Lista de IDs dos dispositivos encontrados
        """
        devices = []
        device_folders = glob.glob(os.path.join(cls.W1_DEVICE_BASE, "28-*"))
        
        for folder in device_folders:
            device_id = os.path.basename(folder)
            devices.append(device_id)
        
        return devices