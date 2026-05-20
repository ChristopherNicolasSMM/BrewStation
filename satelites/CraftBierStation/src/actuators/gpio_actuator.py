#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gpio_actuator.py
Classe para controle de atuadores via GPIO (relés, bombas, válvulas).
Utiliza a biblioteca RPi.GPIO para controle digital.
"""

import logging
from datetime import datetime

import RPi.GPIO as GPIO

from src.core.constants import STATE_OFF, STATE_ON


class GPIOActuator:
    """
    Controlador para atuadores conectados a pinos GPIO.
    Suporta operações como ligar, desligar e obter status.
    """
    
    def __init__(self, name: str, config: dict, gpio_pin: int, initial_state: str = STATE_OFF):
        """
        Inicializa o atuador GPIO.
        
        Args:
            name: Nome único do atuador (ex: 'aquecedor')
            config: Configurações do atuador
            gpio_pin: Número do pino GPIO (BCM)
            initial_state: Estado inicial ('on' ou 'off')
        """
        self.name = name
        self.config = config
        self.gpio_pin = gpio_pin
        self.logger = logging.getLogger(f"actuator.{name}")
        
        # Configura o GPIO
        GPIO.setmode(GPIO.BCM)  # Usa numeração BCM
        GPIO.setup(gpio_pin, GPIO.OUT, initial=GPIO.LOW)
        
        # Define estado inicial
        self.state = STATE_OFF
        if initial_state.lower() == STATE_ON:
            self.turn_on()
        else:
            self.turn_off()
        
        self.last_command_time = datetime.now()
        self.command_count = 0
        
        self.logger.info(f"Atuador '{name}' configurado no GPIO {gpio_pin} (estado inicial: {self.state})")
    
    def turn_on(self) -> bool:
        """
        Liga o atuador (seta GPIO HIGH).
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            GPIO.output(self.gpio_pin, GPIO.HIGH)
            self.state = STATE_ON
            self.last_command_time = datetime.now()
            self.command_count += 1
            self.logger.info(f"Atuador '{self.name}' ligado")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao ligar atuador '{self.name}': {e}")
            return False
    
    def turn_off(self) -> bool:
        """
        Desliga o atuador (seta GPIO LOW).
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            GPIO.output(self.gpio_pin, GPIO.LOW)
            self.state = STATE_OFF
            self.last_command_time = datetime.now()
            self.command_count += 1
            self.logger.info(f"Atuador '{self.name}' desligado")
            return True
        except Exception as e:
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
        
        Returns:
            'on' ou 'off'
        """
        return self.state
    
    def toggle(self) -> bool:
        """
        Inverte o estado atual do atuador.
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        if self.state == STATE_ON:
            return self.turn_off()
        else:
            return self.turn_on()
    
    def get_status(self) -> dict:
        """
        Retorna informações detalhadas do atuador.
        
        Returns:
            Dicionário com status do atuador
        """
        return {
            'name': self.name,
            'type': self.config.get('type', 'gpio_output'),
            'gpio_pin': self.gpio_pin,
            'state': self.state,
            'last_command': self.last_command_time.isoformat() if self.last_command_time else None,
            'command_count': self.command_count
        }
    
    def __del__(self):
        """Destrutor: garante que o GPIO seja liberado."""
        try:
            # Não fazemos cleanup aqui para não afetar outros atuadores
            pass
        except:
            pass