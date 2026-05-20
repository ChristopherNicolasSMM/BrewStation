# Sensor digital simples (booleano)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gpio_sensor.py
Implementação para sensores digitais simples conectados diretamente ao GPIO.
Útil para sensores de contato, boias, sensores de presença, etc.
"""

import time
from typing import Any, Dict, Optional

import RPi.GPIO as GPIO

from src.sensors.base_sensor import BaseSensor


class GPIOSensor(BaseSensor):
    """
    Sensor digital simples conectado a um pino GPIO.
    
    Útil para:
    - Sensores de contato (boias, chaves fim de curso)
    - Sensores de presença (PIR)
    - Sensores ópticos simples
    - Botões e interruptores
    
    O sensor retorna valores booleanos (True/False) ou pode ser configurado
    para retornar 'aberto'/'fechado', 'presente'/'ausente', etc.
    """
    
    # Modos de interpretação do sinal
    MODE_BOOLEAN = "boolean"      # Retorna True/False
    MODE_BINARY = "binary"         # Retorna 1/0
    MODE_STATE = "state"           # Retorna 'on'/'off' ou personalizado
    MODE_CONTACT = "contact"       # Retorna 'aberto'/'fechado'
    MODE_PRESENCE = "presence"     # Retorna 'presente'/'ausente'
    
    def __init__(self, name: str, config: dict, gpio_pin: int):
        """
        Inicializa o sensor GPIO.
        
        Args:
            name: Nome do sensor
            config: Configurações do sensor
            gpio_pin: Número do pino GPIO (BCM)
        """
        super().__init__(name, config)
        
        self.gpio_pin = gpio_pin
        
        # Configurações adicionais
        self.mode = config.get('gpio_mode', self.MODE_BOOLEAN)
        self.pull_up_down = config.get('pull_up_down', 'up')  # 'up' ou 'down'
        self.invert = config.get('invert', False)  # Inverter lógica
        self.debounce_ms = config.get('debounce', 50)  # Debounce em ms
        self.custom_map = config.get('value_map', {})  # Mapeamento personalizado
        
        # Configura o GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Configura resistor de pull-up/down
        pud = GPIO.PUD_UP if self.pull_up_down.lower() == 'up' else GPIO.PUD_DOWN
        GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=pud)
        
        # Para debounce, podemos usar detecção de borda
        if self.debounce_ms > 0:
            GPIO.add_event_detect(
                gpio_pin, 
                GPIO.BOTH, 
                callback=self._gpio_callback,
                bouncetime=self.debounce_ms
            )
        
        self.last_raw_value = None
        self.callback_count = 0
        
        self.logger.info(f"Sensor GPIO configurado no pino {gpio_pin} (modo: {self.mode})")
    
    def _gpio_callback(self, channel):
        """
        Callback para interrupções GPIO.
        Útil para sensores que precisam de resposta rápida.
        """
        self.callback_count += 1
        value = GPIO.input(self.gpio_pin)
        self.logger.debug(f"Interrupção GPIO {channel}: valor {value}")
        
        # Opcional: notificar sobre mudança imediata
        # self.notify_change(value)
    
    def read_raw(self) -> int:
        """
        Lê o valor bruto do pino GPIO.
        
        Returns:
            0 ou 1 (LOW ou HIGH)
        """
        # Pequeno delay para estabilização se necessário
        if self.debounce_ms > 0:
            time.sleep(self.debounce_ms / 1000.0)
        
        value = GPIO.input(self.gpio_pin)
        self.last_raw_value = value
        
        self.logger.debug(f"Leitura GPIO {self.gpio_pin}: {value}")
        return value
    
    def _process_value(self, raw_value: int) -> Any:
        """
        Processa o valor bruto conforme o modo configurado.
        
        Args:
            raw_value: 0 ou 1 do GPIO
            
        Returns:
            Valor processado conforme o modo
        """
        # Aplica inversão se necessário
        if self.invert:
            raw_value = 1 - raw_value
        
        # Processa conforme o modo
        if self.mode == self.MODE_BOOLEAN:
            return bool(raw_value)
            
        elif self.mode == self.MODE_BINARY:
            return raw_value
            
        elif self.mode == self.MODE_STATE:
            return 'on' if raw_value == 1 else 'off'
            
        elif self.mode == self.MODE_CONTACT:
            return 'fechado' if raw_value == 1 else 'aberto'
            
        elif self.mode == self.MODE_PRESENCE:
            return 'presente' if raw_value == 1 else 'ausente'
            
        elif self.mode == 'custom' and self.custom_map:
            # Mapeamento personalizado
            return self.custom_map.get(str(raw_value), raw_value)
            
        else:
            # Modo desconhecido, retorna raw
            return raw_value
    
    def _get_unit(self) -> str:
        """
        Retorna a unidade de medida.
        Para sensores GPIO, geralmente não há unidade física.
        """
        if self.mode == self.MODE_BINARY:
            return 'binary'
        elif self.mode == self.MODE_CONTACT:
            return 'contact'
        elif self.mode == self.MODE_PRESENCE:
            return 'presence'
        else:
            return 'state'
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status detalhado do sensor GPIO.
        """
        status = super().get_status()
        status.update({
            'gpio_pin': self.gpio_pin,
            'mode': self.mode,
            'pull_up_down': self.pull_up_down,
            'invert': self.invert,
            'debounce_ms': self.debounce_ms,
            'last_raw_value': self.last_raw_value,
            'callback_count': self.callback_count
        })
        return status
    
    def wait_for_edge(self, edge='both', timeout=None) -> Optional[int]:
        """
        Aguarda por uma borda no sinal.
        Útil para sensores que precisam de detecção de eventos.
        
        Args:
            edge: 'rising', 'falling', ou 'both'
            timeout: Tempo máximo de espera em ms
            
        Returns:
            O pino que gerou o evento ou None se timeout
        """
        edge_map = {
            'rising': GPIO.RISING,
            'falling': GPIO.FALLING,
            'both': GPIO.BOTH
        }
        
        gpio_edge = edge_map.get(edge, GPIO.BOTH)
        
        if timeout:
            # Timeout em ms
            evento = GPIO.wait_for_edge(
                self.gpio_pin, 
                gpio_edge, 
                timeout=timeout
            )
            return evento
        else:
            # Aguarda indefinidamente
            evento = GPIO.wait_for_edge(self.gpio_pin, gpio_edge)
            return evento
    
    def __del__(self):
        """Destrutor: remove event detection."""
        try:
            GPIO.remove_event_detect(self.gpio_pin)
        except:
            pass


class ButtonSensor(GPIOSensor):
    """
    Sensor especializado para botões.
    Inclui detecção de pressionamento, soltura e segurar.
    """
    
    def __init__(self, name: str, config: dict, gpio_pin: int):
        super().__init__(name, config, gpio_pin)
        
        self.mode = self.MODE_STATE  # Força modo state
        self.press_time = 0
        self.long_press_threshold = config.get('long_press_ms', 1000)
        
    def read(self) -> Optional[Dict[str, Any]]:
        """Leitura especializada para botões."""
        data = super().read()
        
        if data and data['status'] == 'success':
            current_state = data['value']
            current_time = time.time() * 1000  # em ms
            
            if current_state == 'on':  # Pressionado
                if self.press_time == 0:
                    self.press_time = current_time
                    data['event'] = 'press_start'
                else:
                    # Verifica se é press longo
                    if current_time - self.press_time > self.long_press_threshold:
                        data['event'] = 'long_press'
            else:  # Solto
                if self.press_time > 0:
                    press_duration = current_time - self.press_time
                    if press_duration < self.long_press_threshold:
                        data['event'] = 'short_press'
                    else:
                        data['event'] = 'long_press_end'
                    self.press_time = 0
                else:
                    data['event'] = 'release'
        
        return data


class FlowSensor(GPIOSensor):
    """
    Sensor de fluxo baseado em pulsos (como o YF-S201).
    """
    
    def __init__(self, name: str, config: dict, gpio_pin: int):
        super().__init__(name, config, gpio_pin)
        
        self.mode = self.MODE_BINARY
        self.pulse_count = 0
        self.last_reset = time.time()
        self.factor = config.get('factor', 7.5)  # Pulsos por litro (típico YF-S201)
        
        # Configura callback para contar pulsos
        GPIO.add_event_detect(
            gpio_pin,
            GPIO.RISING,
            callback=self._count_pulse,
            bouncetime=10
        )
    
    def _count_pulse(self, channel):
        """Callback para contar pulsos."""
        self.pulse_count += 1
    
    def read_raw(self):
        """Leitura especializada para fluxo."""
        elapsed = time.time() - self.last_reset
        
        if elapsed > 0:
            # Frequência em Hz
            freq_hz = self.pulse_count / elapsed
            
            # Converte para L/min (depende do sensor)
            flow_l_min = freq_hz / self.factor
            
            # Reseta contadores
            self.pulse_count = 0
            self.last_reset = time.time()
            
            return round(flow_l_min, 2)
        
        return 0.0
    
    def _get_unit(self):
        return 'liters_per_minute'