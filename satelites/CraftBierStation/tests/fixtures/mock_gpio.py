#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mock da biblioteca RPi.GPIO para testes sem hardware real."""
from typing import Dict, List
import time

class MockGPIO:
    BCM = "BCM"; BOARD = "BOARD"; OUT = "OUT"; IN = "IN"
    HIGH = 1; LOW = 0; PUD_UP = "PUD_UP"; PUD_DOWN = "PUD_DOWN"
    
    def __init__(self):
        self.mode = None
        self.pins: Dict[int, Dict] = {}
        self.history: List[Dict] = []
        
    def setmode(self, mode): self.mode = mode
        
    def setup(self, channel, direction, initial=0, pull_up_down=None):
        self.pins[channel] = {'direction': direction, 'value': initial}
        
    def output(self, channel, value):
        if channel in self.pins:
            self.pins[channel]['value'] = value
            self.history.append({'op': 'output', 'ch': channel, 'val': value})
            
    def input(self, channel):
        return self.pins[channel]['value'] if channel in self.pins else 0

    def cleanup(self, channel=None): self.pins.clear(); self.history.clear()

_gpio_mock = MockGPIO()
def setmode(m): _gpio_mock.setmode(m)
def setup(c, d, i=0, p=None): _gpio_mock.setup(c, d, i, p)
def output(c, v): _gpio_mock.output(c, v)
def input(c): return _gpio_mock.input(c)
def cleanup(c=None): _gpio_mock.cleanup(c)
def get_mock(): return _gpio_mock
