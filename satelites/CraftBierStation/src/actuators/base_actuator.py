# Classe base para atuadores
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
base_actuator.py
Classe base abstrata para todos os atuadores.
Define a interface comum que todos os atuadores devem implementar,
seguindo o mesmo padrão da classe base de sensores.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from src.core.constants import STATE_OFF, STATE_ON


class BaseActuator(ABC):
    """
    Classe base abstrata para todos os atuadores.
    
    Fornece a estrutura comum e métodos que todos os atuadores
    devem implementar. Gerencia logging, timestamps e estatísticas
    de uso.
    
    Attributes:
        name (str): Nome único do atuador
        config (dict): Configurações específicas do atuador
        logger (Logger): Logger para o atuador
        state (str): Estado atual ('on' ou 'off')
        last_command_time (datetime): Timestamp do último comando
        command_count (int): Número total de comandos executados
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Inicializa o atuador base.
        
        Args:
            name: Nome único do atuador (ex: 'aquecedor', 'bomba')
            config: Dicionário com configurações específicas do atuador
                   Deve conter pelo menos 'type' e 'pin_logical'
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"actuator.{name}")
        
        # Estado e estatísticas
        self.state = STATE_OFF
        self.last_command_time = None
        self.command_count = 0
        self.error_count = 0
        self.max_errors = 3
        
        # Timestamp de criação
        self.created_at = datetime.now()
        
        self.logger.info(f"Atuador base '{name}' inicializado (tipo: {config.get('type', 'desconhecido')})")
    
    @abstractmethod
    def _physical_turn_on(self) -> bool:
        """
        Método abstrato que deve ser implementado por cada tipo de atuador.
        Realiza a operação física de ligar o dispositivo no hardware.
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
    
    @abstractmethod
    def _physical_turn_off(self) -> bool:
        """
        Método abstrato que deve ser implementado por cada tipo de atuador.
        Realiza a operação física de desligar o dispositivo no hardware.
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
    
    @abstractmethod
    def _physical_get_state(self) -> str:
        """
        Método abstrato que deve ser implementado por cada tipo de atuador.
        Obtém o estado físico real do dispositivo.
        
        Returns:
            'on' ou 'off' baseado no estado real do hardware
        """
    
    def turn_on(self) -> bool:
        """
        Liga o atuador.
        Método público com tratamento de erros e logging.
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            self.logger.info(f"Comando: LIGAR atuador '{self.name}'")
            
            # Executa comando físico
            success = self._physical_turn_on()
            
            if success:
                self.state = STATE_ON
                self.last_command_time = datetime.now()
                self.command_count += 1
                self.error_count = 0
                self.logger.info(f"Atuador '{self.name}' ligado com sucesso")
            else:
                self.error_count += 1
                self.logger.error(f"Falha ao ligar atuador '{self.name}'")
            
            return success
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Erro ao ligar atuador '{self.name}': {e}")
            return False
    
    def turn_off(self) -> bool:
        """
        Desliga o atuador.
        Método público com tratamento de erros e logging.
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            self.logger.info(f"Comando: DESLIGAR atuador '{self.name}'")
            
            # Executa comando físico
            success = self._physical_turn_off()
            
            if success:
                self.state = STATE_OFF
                self.last_command_time = datetime.now()
                self.command_count += 1
                self.error_count = 0
                self.logger.info(f"Atuador '{self.name}' desligado com sucesso")
            else:
                self.error_count += 1
                self.logger.error(f"Falha ao desligar atuador '{self.name}'")
            
            return success
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Erro ao desligar atuador '{self.name}': {e}")
            return False
    
    def set_state(self, state: str) -> bool:
        """
        Define o estado do atuador.
        
        Args:
            state: 'on' ou 'off'
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        state = state.lower()
        if state == STATE_ON:
            return self.turn_on()
        elif state == STATE_OFF:
            return self.turn_off()
        else:
            self.logger.error(f"Estado inválido para atuador '{self.name}': {state}")
            return False
    
    def get_state(self) -> str:
        """
        Retorna o estado atual do atuador.
        Pode consultar o hardware ou retornar o estado em cache.
        
        Returns:
            'on' ou 'off'
        """
        try:
            # Tenta obter estado real do hardware
            physical_state = self._physical_get_state()
            if physical_state in [STATE_ON, STATE_OFF]:
                # Atualiza cache se necessário
                if physical_state != self.state:
                    self.logger.debug(f"Estado físico diferente do cache: {physical_state} vs {self.state}")
                    self.state = physical_state
                return physical_state
        except Exception as e:
            self.logger.debug(f"Não foi possível ler estado físico: {e}")
        
        # Retorna estado em cache se leitura física falhar
        return self.state
    
    def toggle(self) -> bool:
        """
        Inverte o estado atual do atuador.
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        current = self.get_state()
        if current == STATE_ON:
            return self.turn_off()
        else:
            return self.turn_on()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna informações detalhadas do atuador.
        
        Returns:
            Dicionário com status completo do atuador
        """
        return {
            'name': self.name,
            'type': self.config.get('type', 'unknown'),
            'state': self.get_state(),
            'last_command': self.last_command_time.isoformat() if self.last_command_time else None,
            'command_count': self.command_count,
            'error_count': self.error_count,
            'active': self.error_count < self.max_errors,
            'created_at': self.created_at.isoformat(),
            'config': {
                'pin_logical': self.config.get('pin_logical'),
                'initial_state': self.config.get('initial_state', 'off')
            }
        }
    
    def reset_error_count(self):
        """Reseta o contador de erros."""
        self.error_count = 0
        self.logger.info(f"Contador de erros resetado para atuador '{self.name}'")
    
    def __repr__(self) -> str:
        """Representação string do atuador."""
        return f"<BaseActuator name='{self.name}' state='{self.state}'>"