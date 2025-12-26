"""
Plugin Meu Plugin.
Plugin gerado automaticamente pelo PluginGenerator.
"""

from pathlib import Path
from typing import List
from flask import Blueprint

from core.plugin_base import PluginBase
from db.database import db


class MeuPluginPlugin(PluginBase):
    """
    Plugin Meu Plugin.
    """
    
    def install(self) -> bool:
        """Instala o plugin."""
        try:
            # Registrar modelos no banco
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
            return True
        except Exception as e:
            print(f"Erro ao instalar plugin {self.name}: {e}")
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
        return []
    
    def register_models(self) -> List:
        """Registra os modelos SQLAlchemy do plugin."""
        # Adicionar modelos aqui quando necessário
        return []
