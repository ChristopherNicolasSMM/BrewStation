"""
Plugin Device Manager.
Gerenciador de dispositivos IoT com servidor MQTT embutido.
"""

from pathlib import Path
from typing import List
from flask import Blueprint
import logging

from core.plugin_base import PluginBase
from db.database import db

logger = logging.getLogger(__name__)


class DeviceManagerPlugin(PluginBase):
    """
    Plugin Device Manager.
    
    Este plugin foi gerado automaticamente. Edite este arquivo para personalizar
    o comportamento do plugin.
    
    IMPORTANTE sobre prefixos de tabelas:
    - O campo table_prefix no install.json controla o prefixo das tabelas
    - Se table_prefix for null, usa "plugin_device_manager_" como padrão
    - Modelos são prefixados automaticamente durante o registro
    - Use model_loader nas rotas API para garantir modelos prefixados corretos
    """
    
    def install(self) -> bool:
        """
        Instala o plugin e cria estrutura de pastas necessária.
        """
        try:
            # Criar estrutura de pastas data/ dentro do plugin
            plugin_data_path = self.plugin_path / "data"
            devices_configs_path = plugin_data_path / "devices" / "configs"
            devices_states_path = plugin_data_path / "devices" / "states"
            
            # Criar diretórios se não existirem
            devices_configs_path.mkdir(parents=True, exist_ok=True)
            devices_states_path.mkdir(parents=True, exist_ok=True)
            
            # Criar arquivo de configuração padrão do broker MQTT se não existir
            broker_config_path = plugin_data_path / "mqtt_broker.json"
            if not broker_config_path.exists():
                import json
                default_broker_config = {
                    "enabled": True,
                    "host": "0.0.0.0",
                    "port": 1883,
                    "authentication": {
                        "enabled": False,
                        "username": None,
                        "password": None
                    },
                    "topics": {
                        "base": "brewstation/devices",
                        "allowed_patterns": ["brewstation/devices/+/+"]
                    },
                    "ssl": {
                        "enabled": False,
                        "cert_file": None,
                        "key_file": None
                    }
                }
                with open(broker_config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_broker_config, f, indent=2, ensure_ascii=False)
            
            # Registrar modelos no banco
            # Os modelos serão prefixados automaticamente pelo sistema
            models = self.register_models()
            if models:
                db.create_all()
            
            # Inicializar funções pré-definidas
            self._initialize_predefined_functions()
            
            # Salvar no banco de dados
            from model.plugin import Plugin as PluginModel
            
            plugin_db = PluginModel.query.filter_by(name=self.name).first()
            if not plugin_db:
                plugin_db = PluginModel(
                    name=self.name,
                    version=self.version,
                    description=self.description,
                    author=self.author,
                    is_installed=True,
                    is_active=False,
                    dependencies=self.dependencies,
                    config_json=self.config
                )
                db.session.add(plugin_db)
            else:
                plugin_db.is_installed = True
                plugin_db.version = self.version
                plugin_db.description = self.description
                plugin_db.author = self.author
            
            db.session.commit()
            logger.info(f"Plugin {self.name} instalado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao instalar plugin {self.name}: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def uninstall(self) -> bool:
        """Desinstala o plugin."""
        try:
            from model.plugin import Plugin as PluginModel
            
            plugin_db = PluginModel.query.filter_by(name=self.name).first()
            if plugin_db:
                plugin_db.is_installed = False
                plugin_db.is_active = False
                db.session.commit()
            
            return True
        except Exception as e:
            print(f"Erro ao desinstalar plugin {self.name}: {e}")
            db.session.rollback()
            return False
    
    def register_routes(self, app) -> List[Blueprint]:
        """Registra as rotas do plugin."""
        # O sistema descobre automaticamente rotas em api/routes/ e controller/routes.py
        # Este método é usado apenas como fallback se necessário
        return []
    
    def register_models(self) -> List:
        """
        Registra os modelos SQLAlchemy do plugin.
        
        IMPORTANTE:
        - Os modelos retornados serão automaticamente prefixados
        - O prefixo usado é definido em install.json (campo table_prefix)
        - Prefixo atual: "dvmanage_" (será aplicado automaticamente)
        - Use model_loader nas rotas API para garantir que os modelos prefixados sejam usados
        """
        models = []
        
        # Registrar modelos
        from plugins.plugin_device_manager.model.device_metadata import DeviceMetadata
        from plugins.plugin_device_manager.model.device_function import DeviceFunction
        from plugins.plugin_device_manager.model.device_actor import DeviceActor
        
        models.extend([DeviceMetadata, DeviceFunction, DeviceActor])
        
        return models
    
    def _initialize_predefined_functions(self):
        """
        Cria funções pré-definidas do sistema.
        
        Funções pré-definidas são criadas apenas se não existirem.
        """
        from plugins.plugin_device_manager.model.device_function import DeviceFunction
        
        predefined_functions = [
            {
                'name': 'temperature',
                'display_name': 'Temperatura',
                'description': 'Sensor de temperatura',
                'category': 'sensor',
                'unit': '°C',
                'data_type': 'float',
                'min_value': -50.0,
                'max_value': 150.0,
                'icon': 'bi bi-thermometer-half'
            },
            {
                'name': 'humidity',
                'display_name': 'Umidade',
                'description': 'Sensor de umidade relativa',
                'category': 'sensor',
                'unit': '%',
                'data_type': 'float',
                'min_value': 0.0,
                'max_value': 100.0,
                'icon': 'bi bi-moisture'
            },
            {
                'name': 'pressure',
                'display_name': 'Pressão',
                'description': 'Sensor de pressão',
                'category': 'sensor',
                'unit': 'bar',
                'data_type': 'float',
                'min_value': 0.0,
                'max_value': 10.0,
                'icon': 'bi bi-speedometer2'
            },
            {
                'name': 'relay',
                'display_name': 'Relé',
                'description': 'Relé digital (liga/desliga)',
                'category': 'actuator',
                'unit': None,
                'data_type': 'bool',
                'min_value': None,
                'max_value': None,
                'icon': 'bi bi-toggle-on'
            },
            {
                'name': 'pwm',
                'display_name': 'PWM',
                'description': 'Modulação por largura de pulso',
                'category': 'actuator',
                'unit': '%',
                'data_type': 'int',
                'min_value': 0.0,
                'max_value': 100.0,
                'icon': 'bi bi-sliders'
            },
            {
                'name': 'adc',
                'display_name': 'ADC',
                'description': 'Conversor analógico-digital',
                'category': 'sensor',
                'unit': None,
                'data_type': 'int',
                'min_value': 0.0,
                'max_value': 4095.0,
                'icon': 'bi bi-graph-up'
            },
            {
                'name': 'gpio_digital',
                'display_name': 'GPIO Digital',
                'description': 'Entrada/saída digital GPIO',
                'category': 'hybrid',
                'unit': None,
                'data_type': 'bool',
                'min_value': None,
                'max_value': None,
                'icon': 'bi bi-toggle-off'
            }
        ]
        
        for func_data in predefined_functions:
            # Verificar se função já existe
            existing = DeviceFunction.query.filter_by(name=func_data['name']).first()
            if not existing:
                func_data['is_predefined'] = True
                function = DeviceFunction(**func_data)
                db.session.add(function)
                logger.info(f"Função pré-definida criada: {func_data['name']}")
        
        db.session.commit()

