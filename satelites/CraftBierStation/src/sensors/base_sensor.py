# Classe base para todos os sensores
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
base_sensor.py
Classe base abstrata para todos os sensores.
Define a interface comum que todos os sensores devem implementar.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

class BaseSensor(ABC):
    """
    Classe base abstrata para todos os sensores.
    
    Fornece a estrutura comum e métodos que todos os sensores
    devem implementar. Também gerencia logging e timestamp.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Inicializa o sensor base.
        
        Args:
            name: Nome único do sensor (ex: 'temp_mostura')
            config: Dicionário com configurações específicas do sensor
                   Deve conter pelo menos 'type' e 'pin_logical'
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"sensor.{name}")
        self.last_read_time = 0
        self.last_value = None
        self.error_count = 0
        self.max_errors = 3  # Número máximo de erros consecutivos antes de desabilitar
        
        self.logger.info(f"Sensor '{name}' inicializado (tipo: {config.get('type', 'desconhecido')})")
    
    @abstractmethod
    def read_raw(self) -> Any:
        """
        Método abstrato que deve ser implementado por cada tipo de sensor.
        Realiza a leitura bruta do hardware.
        
        Returns:
            Valor bruto lido do sensor
        
        Raises:
            Exception: Se houver erro na leitura
        """
        pass
    
    def read(self) -> Optional[Dict[str, Any]]:
        """
        Método público para leitura do sensor com tratamento de erros.
        Formata a leitura para o formato padrão do sistema.
        
        Returns:
            Dicionário com os dados formatados ou None em caso de erro
            Formato: {
                'sensor': nome,
                'value': valor_processado,
                'unit': unidade,
                'timestamp': timestamp_iso,
                'status': 'success'|'error'
            }
        """
        try:
            # Verifica intervalo mínimo entre leituras (anti-flood)
            current_time = time.time()
            min_interval = self.config.get('interval', 1)  # mínimo 1 segundo
            
            if current_time - self.last_read_time < min_interval:
                # Retorna último valor válido se a leitura for muito frequente
                if self.last_value:
                    return self.last_value
                time.sleep(0.1)  # Pequena pausa
            
            # Tenta ler o sensor
            raw_value = self.read_raw()
            
            # Processa o valor (converte, formata, etc)
            processed_value = self._process_value(raw_value)
            
            # Prepara resultado padronizado
            result = {
                'sensor': self.name,
                'value': processed_value,
                'unit': self._get_unit(),
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            # Atualiza cache
            self.last_value = result
            self.last_read_time = current_time
            self.error_count = 0  # Reseta contador de erros
            
            self.logger.debug(f"Leitura bem-sucedida: {processed_value} {self._get_unit()}")
            return result
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Erro na leitura do sensor {self.name}: {e}")
            
            if self.error_count >= self.max_errors:
                self.logger.critical(f"Sensor {self.name} desabilitado após {self.max_errors} erros consecutivos")
                return {
                    'sensor': self.name,
                    'error': str(e),
                    'error_code': 'ERR_SENSOR_DISABLED',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error'
                }
            
            return {
                'sensor': self.name,
                'error': str(e),
                'error_code': 'ERR_SENSOR_READ',
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }
    
    def _process_value(self, raw_value: Any) -> Any:
        """
        Processa o valor bruto do sensor.
        Pode ser sobrescrito por sensores específicos.
        
        Args:
            raw_value: Valor bruto lido do hardware
            
        Returns:
            Valor processado
        """
        return raw_value
    
    def _get_unit(self) -> str:
        """
        Retorna a unidade de medida do sensor.
        Deve ser sobrescrito por sensores específicos.
        
        Returns:
            String com a unidade (ex: 'celsius', 'percent')
        """
        return 'unknown'
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna o status atual do sensor.
        
        Returns:
            Dicionário com informações de status
        """
        return {
            'name': self.name,
            'type': self.config.get('type'),
            'last_read': self.last_read_time,
            'error_count': self.error_count,
            'active': self.error_count < self.max_errors
        }