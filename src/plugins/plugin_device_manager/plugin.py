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
        
        # Registrar modelo DeviceMetadata
        from plugins.plugin_device_manager.model.device_metadata import DeviceMetadata
        models.append(DeviceMetadata)
        
        return models
