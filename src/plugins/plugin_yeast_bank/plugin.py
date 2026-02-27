"""
Plugin YeaskBank.
Plugin gerado automaticamente pelo PluginGenerator.
"""

from pathlib import Path
from typing import List
from flask import Blueprint

from core.plugin_base import PluginBase
from db.database import db


class YeastBankPlugin(PluginBase):
    """
    Plugin YeaskBank.
    
    Este plugin foi gerado automaticamente. Edite este arquivo para personalizar
    o comportamento do plugin.
    
    IMPORTANTE sobre prefixos de tabelas:
    - O campo table_prefix no install.json controla o prefixo das tabelas
    - Se table_prefix for null, usa "plugin_yeast_bank_" como padrão
    - Modelos são prefixados automaticamente durante o registro
    - Use model_loader nas rotas API para garantir modelos prefixados corretos
    """
    
    def install(self) -> bool:
        """Instala o plugin."""
        try:
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
        # Este método é usado apenas como fallback se necessário
        return []
    
    def register_models(self) -> List:
        """
        Registra os modelos SQLAlchemy do plugin.
        
        IMPORTANTE:
        - Os modelos retornados serão automaticamente prefixados
        - O prefixo usado é definido em install.json (campo table_prefix)
        - Se table_prefix for null, usa "plugin_yeast_bank_" como padrão
        - Use model_loader nas rotas API para garantir que os modelos prefixados sejam usados
        
        Exemplo:
            from model.exemplo import YeastBankExemplo
            return [YeastBankExemplo]
        """
        from plugins.plugin_yeast_bank.model.yeast_bank_models import (
            YeastStrain,
            YeastBankItem,
            YeastStarterLog
        )
        
        # Modelo de exemplo (pode ser removido se não necessário)
        # Descomente para usar o modelo de exemplo:
        # from model.exemplo import YeastBankExemplo
        # models.append(YeastBankExemplo)
        
        # Adicionar seus próprios modelos aqui:
        # from model.meu_modelo import MeuModelo
        # models.append(MeuModelo)        
        return [YeastStrain, YeastBankItem, YeastStarterLog]
        

