"""
Plugin Mash Control.
Plugin de automação de processos de brassagem com dashboard visual interativo.
"""

import logging
from pathlib import Path
from typing import List, Optional
from flask import Blueprint

from core.plugin_base import PluginBase
from db.database import db

logger = logging.getLogger(__name__)


class MashControlPlugin(PluginBase):
    """
    Plugin Mash Control.
    
    Plugin de automação de processos de brassagem com dashboard visual interativo,
    controle automático/manual, editor de receitas e integração com device_manager.
    
    IMPORTANTE sobre prefixos de tabelas:
    - O campo table_prefix no install.json controla o prefixo das tabelas
    - Prefixo atual: "mash_ctrl_" (definido em install.json)
    - Modelos são prefixados automaticamente durante o registro
    - Use model_loader nas rotas API para garantir modelos prefixados corretos
    """
    
    def install(self) -> bool:
        """Instala o plugin e cria estrutura de pastas."""
        try:
            # Criar estrutura de pastas data/
            plugin_data_path = self.plugin_path / "data"
            recipes_path = plugin_data_path / "recipes"
            dashboards_path = plugin_data_path / "dashboards"
            sessions_path = plugin_data_path / "sessions"
            
            recipes_path.mkdir(parents=True, exist_ok=True)
            dashboards_path.mkdir(parents=True, exist_ok=True)
            sessions_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Estrutura de pastas criada para plugin {self.name}")
            
            # IMPORTANTE: Importar modelo User antes de criar tabelas para garantir ForeignKeys
            try:
                from model.user import User
                # Forçar registro do User no SQLAlchemy metadata
                _ = User.__table__
                logger.debug("Modelo User importado e registrado para ForeignKeys")
            except ImportError as e:
                logger.warning(f"Não foi possível importar modelo User: {e}")
            except Exception as e:
                logger.warning(f"Erro ao registrar modelo User: {e}")
            
            # Registrar modelos no banco
            models = self.register_models()
            if models:
                # Aplicar prefixos aos modelos antes de criar tabelas
                from core.plugin_db_helper import prefix_models
                plugin_dir_name = self.plugin_path.name if hasattr(self, 'plugin_path') and self.plugin_path else self.name
                plugin_name_for_prefix = plugin_dir_name if plugin_dir_name else self.name
                prefixed_models = prefix_models(models, plugin_name_for_prefix, self.table_prefix)
                
                # Atualizar ForeignKey de BrewSession para mash_recipe após prefixo
                # Encontrar o nome prefixado da tabela MashRecipe
                recipe_table_name = None
                for model in prefixed_models:
                    if model.__name__ == 'MashRecipe':
                        recipe_table_name = getattr(model, '__tablename__', None)
                        break
                
                # Atualizar ForeignKey recipe_id se encontramos a tabela MashRecipe
                if recipe_table_name:
                    # Atualizar a ForeignKey diretamente no modelo antes de criar as tabelas
                    from plugins.plugin_mash_control.model.mash_models import BrewSession
                    from sqlalchemy import ForeignKey
                    
                    try:
                        # Forçar criação do Table para poder atualizar a ForeignKey
                        if not hasattr(BrewSession, '__table__'):
                            try:
                                _ = BrewSession.__table__  # Força criação
                            except:
                                pass  # Table será criado quando necessário
                        
                        # Atualizar ForeignKey na coluna recipe_id
                        if hasattr(BrewSession, '__table__'):
                            try:
                                table = BrewSession.__table__
                                if table is not None:
                                    recipe_id_col = table.columns.get('recipe_id')
                                    if recipe_id_col:
                                        # Atualizar ForeignKey
                                        recipe_id_col.foreign_keys.clear()
                                        new_fk = ForeignKey(f"{recipe_table_name}.id")
                                        recipe_id_col.foreign_keys.add(new_fk)
                                        logger.debug(f"ForeignKey recipe_id atualizada para {recipe_table_name}.id")
                            except Exception as table_error:
                                logger.debug(f"Table ainda não criado ou erro ao acessar: {table_error}")
                    except Exception as e:
                        logger.debug(f"Não foi possível atualizar ForeignKey recipe_id: {e}")
                        logger.info("ForeignKey será resolvida automaticamente quando as tabelas forem criadas")
                
                # Criar tabelas após prefixos aplicados
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
    
    def activate(self) -> bool:
        """Ativa o plugin e verifica dependências."""
        try:
            # Verificar se device_manager está instalado e ativo
            # Tentar acessar plugin_manager através do current_app se disponível
            try:
                from flask import current_app
                if hasattr(current_app, 'plugin_manager'):
                    plugin_manager = current_app.plugin_manager
                    # Tentar buscar pelo nome do diretório primeiro
                    device_manager_plugin = plugin_manager.get_plugin('plugin_device_manager')
                    if not device_manager_plugin:
                        # Tentar pelo nome do plugin
                        device_manager_plugin = plugin_manager.get_plugin('device_manager')
                    
                    if not device_manager_plugin or not device_manager_plugin.is_active:
                        logger.warning(f"Plugin {self.name} requer device_manager instalado e ativo")
                        # Não falhar a ativação, apenas avisar
                        # A verificação será feita quando o plugin tentar usar device_manager
                        logger.info(f"Plugin {self.name} ativado (device_manager pode não estar disponível ainda)")
                        return True
                else:
                    # Se plugin_manager não estiver disponível, apenas logar
                    logger.debug("plugin_manager não disponível no contexto atual - ativando plugin mesmo assim")
            except RuntimeError:
                # Não há contexto de aplicação (CLI), verificar dependência via banco de dados
                logger.debug("Sem contexto de aplicação - verificando dependência via banco de dados")
                try:
                    from model.plugin import Plugin as PluginModel
                    device_manager_db = PluginModel.query.filter_by(name='device_manager').first()
                    if not device_manager_db or not device_manager_db.is_installed:
                        logger.warning(f"Plugin {self.name} requer device_manager instalado")
                        # Não falhar a ativação, apenas avisar
                        logger.info(f"Plugin {self.name} ativado (device_manager pode não estar instalado)")
                        return True
                except Exception as db_error:
                    logger.debug(f"Erro ao verificar dependência via banco: {db_error}")
            
            logger.info(f"Plugin {self.name} ativado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao ativar plugin {self.name}: {e}", exc_info=True)
            # Não falhar a ativação por causa de erro na verificação de dependência
            logger.warning("Ativando plugin mesmo assim - dependências serão verificadas em tempo de execução")
            return True
    
    def deactivate(self) -> bool:
        """Desativa o plugin e para sessões ativas."""
        try:
            # Parar todas as sessões ativas
            from plugins.plugin_mash_control.utils.model_loader import get_brew_session
            BrewSession = get_brew_session()
            
            if BrewSession:
                active_sessions = BrewSession.query.filter_by(status='running').all()
                for session in active_sessions:
                    session.status = 'paused'
                    db.session.commit()
                    logger.info(f"Sessão {session.id} pausada durante desativação do plugin")
            
            logger.info(f"Plugin {self.name} desativado")
            return True
        except Exception as e:
            logger.error(f"Erro ao desativar plugin {self.name}: {e}", exc_info=True)
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
            
            logger.info(f"Plugin {self.name} desinstalado")
            return True
        except Exception as e:
            logger.error(f"Erro ao desinstalar plugin {self.name}: {e}", exc_info=True)
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
        - Prefixo atual: "mash_ctrl_" (será aplicado automaticamente)
        - Use model_loader nas rotas API para garantir que os modelos prefixados sejam usados
        """
        models = []
        
        # Registrar modelos do plugin
        from plugins.plugin_mash_control.model.mash_models import (
            MashRecipe, BrewSession, DashboardLayout, Plant
        )
        
        models.append(MashRecipe)
        models.append(BrewSession)
        models.append(DashboardLayout)
        models.append(Plant)
        
        return models
