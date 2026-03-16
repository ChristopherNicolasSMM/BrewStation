# Servidor Flask com a REST API
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rest_api.py
Interface REST API para o servidor de dispositivos.
Fornece endpoints HTTP para consultar sensores e controlar atuadores.
"""

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import logging
import threading
from typing import Dict, Any, Optional
from waitress import serve
from src.core.constants import STATE_ON, STATE_OFF

class RESTAPI:
    """
    Servidor REST API usando Flask.
    Fornece endpoints para monitoramento e controle dos dispositivos.
    """
    
    def __init__(self, config: Dict[str, Any], sensors: Dict, actuators: Dict):
        """
        Inicializa a REST API.
        
        Args:
            config: Dicionário com configurações HTTP
            sensors: Dicionário com instâncias dos sensores {nome: instancia}
            actuators: Dicionário com instâncias dos atuadores {nome: instancia}
        """
        self.config = config
        self.sensors = sensors
        self.actuators = actuators
        self.logger = logging.getLogger(__name__)
        
        # Configurações
        self.enabled = config.get('enabled', False)
        self.port = config.get('port', 5001)
        self.host = config.get('host', '127.0.0.1')
        self.api_key = config.get('api_key')
        self.cors_enabled = config.get('cors_enabled', False)
        self.debug = config.get('debug', False)
        
        # Flask app
        self.app = None
        self.server_thread = None
        
        if self.enabled:
            self._create_app()
    
    def _create_app(self):
        """Cria e configura a aplicação Flask."""
        self.app = Flask(__name__)
        
        # Configura CORS se habilitado
        if self.cors_enabled:
            CORS(self.app)
        
        # Configura rota raiz
        @self.app.route('/', methods=['GET'])
        def index():
            return jsonify({
                'name': 'BrewStation Device Server',
                'version': '1.0.0',
                'status': 'running',
                'endpoints': {
                    'sensors': '/api/sensors',
                    'sensor': '/api/sensors/<name>',
                    'actuators': '/api/actuators',
                    'actuator': '/api/actuators/<name>',
                    'actuator_control': '/api/actuators/<name>/<action>'
                }
            })
        
        # Rotas para sensores
        @self.app.route('/api/sensors', methods=['GET'])
        def list_sensors():
            """Lista todos os sensores disponíveis."""
            self._check_auth()
            sensor_list = []
            for name, sensor in self.sensors.items():
                sensor_list.append({
                    'name': name,
                    'type': sensor.config.get('type', 'unknown'),
                    'status': sensor.get_status()
                })
            return jsonify({'sensors': sensor_list})
        
        @self.app.route('/api/sensors/<name>', methods=['GET'])
        def get_sensor(name):
            """Obtém a leitura atual de um sensor específico."""
            self._check_auth()
            
            if name not in self.sensors:
                abort(404, description=f"Sensor '{name}' não encontrado")
            
            sensor = self.sensors[name]
            data = sensor.read()
            
            if data and data.get('status') == 'success':
                return jsonify(data)
            else:
                return jsonify({
                    'error': f"Falha na leitura do sensor {name}",
                    'details': data
                }), 500
        
        # Rotas para atuadores
        @self.app.route('/api/actuators', methods=['GET'])
        def list_actuators():
            """Lista todos os atuadores disponíveis."""
            self._check_auth()
            actuator_list = []
            for name, actuator in self.actuators.items():
                actuator_list.append({
                    'name': name,
                    'type': actuator.config.get('type', 'gpio_output'),
                    'state': actuator.get_state(),
                    'gpio_pin': actuator.gpio_pin
                })
            return jsonify({'actuators': actuator_list})
        
        @self.app.route('/api/actuators/<name>', methods=['GET'])
        def get_actuator(name):
            """Obtém o status de um atuador específico."""
            self._check_auth()
            
            if name not in self.actuators:
                abort(404, description=f"Atuador '{name}' não encontrado")
            
            actuator = self.actuators[name]
            return jsonify(actuator.get_status())
        
        @self.app.route('/api/actuators/<name>/<action>', methods=['POST'])
        def control_actuator(name, action):
            """Controla um atuador (on/off/toggle)."""
            self._check_auth()
            
            if name not in self.actuators:
                abort(404, description=f"Atuador '{name}' não encontrado")
            
            actuator = self.actuators[name]
            
            # Processa a ação
            if action == 'on':
                success = actuator.turn_on()
            elif action == 'off':
                success = actuator.turn_off()
            elif action == 'toggle':
                success = actuator.toggle()
            else:
                abort(400, description=f"Ação inválida: {action}. Use on/off/toggle")
            
            if success:
                return jsonify({
                    'name': name,
                    'action': action,
                    'state': actuator.get_state(),
                    'success': True
                })
            else:
                return jsonify({
                    'name': name,
                    'action': action,
                    'success': False,
                    'error': 'Falha ao executar ação'
                }), 500
        
        # Rotas para controle via JSON (alternativa)
        @self.app.route('/api/actuators/<name>', methods=['POST', 'PUT'])
        def control_actuator_json(name):
            """Controla atuador via JSON body."""
            self._check_auth()
            
            if name not in self.actuators:
                abort(404, description=f"Atuador '{name}' não encontrado")
            
            data = request.get_json()
            if not data or 'state' not in data:
                abort(400, description="Body JSON deve conter campo 'state'")
            
            state = data['state'].lower()
            if state not in [STATE_ON, STATE_OFF]:
                abort(400, description=f"Estado deve ser '{STATE_ON}' ou '{STATE_OFF}'")
            
            actuator = self.actuators[name]
            success = actuator.set_state(state)
            
            return jsonify({
                'name': name,
                'state': actuator.get_state(),
                'success': success
            })
        
        # Rota de saúde/healthcheck
        @self.app.route('/api/health', methods=['GET'])
        def health():
            """Endpoint de healthcheck."""
            return jsonify({
                'status': 'healthy',
                'sensors': len(self.sensors),
                'actuators': len(self.actuators),
                'timestamp': self._get_timestamp()
            })
        
        self.logger.info("Aplicação Flask configurada")
    
    def _check_auth(self):
        """Verifica autenticação se configurada."""
        if self.api_key:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                abort(401, description="Token de autenticação não fornecido")
            
            token = auth_header.split(' ')[1]
            if token != self.api_key:
                abort(403, description="Token de autenticação inválido")
    
    def _get_timestamp(self):
        """Retorna timestamp atual."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def start(self):
        """Inicia o servidor REST API em uma thread separada."""
        if not self.enabled or not self.app:
            self.logger.info("Interface HTTP desabilitada")
            return
        
        def run_server():
            self.logger.info(f"Iniciando servidor HTTP em {self.host}:{self.port}")
            
            if self.debug:
                # Modo debug (Flask development server)
                self.app.run(host=self.host, port=self.port, debug=self.debug, threaded=True)
            else:
                # Modo produção (Waitress)
                serve(self.app, host=self.host, port=self.port, threads=4)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.logger.info("Servidor HTTP iniciado em thread separada")
    
    def stop(self):
        """Para o servidor (nota: Flask não tem stop fácil)."""
        self.logger.info("Servidor HTTP não pode ser parado graciosamente via código")
        # Em produção, use gerenciamento de processos