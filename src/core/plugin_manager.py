"""
Plugin manager for BrewStation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from flask import Flask
from flask import Blueprint
from .plugin_loader import PluginLoader
from .plugin_base import PluginBase
from .template_loader import PluginTemplateLoader

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Gerenciador central de plugins.
    
    Responsável por descobrir, instalar, desinstalar, ativar e desativar plugins.
    """
    
    def __init__(self, app: Flask, plugins_dir: Path, config_file: Path):
        """
        Inicializa o gerenciador.
        
        Args:
            app: Instância da aplicação Flask
            plugins_dir: Diretório onde os plugins estão localizados
            config_file: Arquivo de configuração de plugins (plugins.json)
        """
        self.app = app
        self.plugins_dir = Path(plugins_dir)
        self.config_file = Path(config_file)
        self.loader = PluginLoader(self.plugins_dir)
        self.plugins: Dict[str, PluginBase] = {}
        self.active_plugins: List[str] = []
        self.installed_plugins: List[str] = []
        
        # Carregar configuração
        self._load_config()
        
        # Descobrir e carregar plugins
        self._discover_and_load()
    
    def _load_config(self):
        """Carrega a configuração de plugins do arquivo JSON."""
        if not self.config_file.exists():
            # Criar arquivo de configuração padrão
            self._save_config()
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.installed_plugins = config.get('installed_plugins', [])
            self.active_plugins = config.get('active_plugins', [])
            logger.info(f"Configuração de plugins carregada: {len(self.installed_plugins)} instalados")
        except Exception as e:
            logger.error(f"Erro ao carregar configuração de plugins: {e}")
            self.installed_plugins = []
            self.active_plugins = []
    
    def _save_config(self):
        """Salva a configuração de plugins no arquivo JSON."""
        config = {
            'installed_plugins': self.installed_plugins,
            'active_plugins': self.active_plugins,
            'plugin_configs': {}
        }
        
        # Adicionar configurações individuais dos plugins
        # Não salvar menu_config aqui, pois agora está em menu_config.json
        for plugin_name, plugin in self.plugins.items():
            if plugin_name in self.installed_plugins:
                config['plugin_configs'][plugin_name] = {
                    'version': plugin.version
                }
        
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.debug("Configuração de plugins salva")
        except Exception as e:
            logger.error(f"Erro ao salvar configuração de plugins: {e}")
    
    def _discover_and_load(self):
        """Descobre e carrega plugins disponíveis."""
        discovered = self.loader.discover_plugins()
        
        for plugin_name in discovered:
            plugin = self.loader.load_plugin(plugin_name)
            if plugin:
                self.plugins[plugin_name] = plugin
                
                # Marcar como instalado se estiver na lista
                if plugin_name in self.installed_plugins:
                    plugin.is_installed = True
                else:
                    # Se não está na lista mas é o plugin core (brewstation_core), instalar automaticamente
                    # Verificar pelo nome do plugin (do install.json) ou pelo nome do diretório
                    if plugin.name == 'brewstation_core' or plugin_name == 'plugin_integ_bFather':
                        plugin.is_installed = True
                        # Usar o nome do plugin (do install.json) para consistência
                        plugin_key = plugin.name if plugin.name else plugin_name
                        if plugin_key not in self.installed_plugins:
                            self.installed_plugins.append(plugin_key)
                
                # Ativar se estiver na lista de ativos
                # Verificar tanto pelo nome do plugin quanto pelo nome do diretório
                plugin_key = plugin.name if plugin.name else plugin_name
                if plugin_key in self.active_plugins or plugin_name in self.active_plugins:
                    plugin.activate()
                    self._register_plugin(plugin)
                elif (plugin.name == 'brewstation_core' or plugin_name == 'plugin_integ_bFather') and plugin.is_installed:
                    # Ativar automaticamente o plugin core se estiver instalado
                    plugin.activate()
                    if plugin_key not in self.active_plugins:
                        self.active_plugins.append(plugin_key)
                    self._register_plugin(plugin)
                    self._save_config()  # Salvar configuração atualizada
    
    def _register_plugin(self, plugin: PluginBase):
        """
        Registra um plugin na aplicação Flask.
        
        Este método registra automaticamente:
        - Rotas da pasta api/routes/ e controller/routes.py
        - Templates da pasta templates/
        - Static files da pasta static/
        - Menu do install.json
        
        Args:
            plugin: Instância do plugin
        """
        try:
            # Usar o sistema de instalação automática
            from .plugin_installer import PluginInstaller
            from .plugin_routes_helper import get_route_registry
            
            installer = PluginInstaller(plugin.plugin_path, plugin.config)
            route_registry = get_route_registry()
            
            # IMPORTANTE: Importar modelos do core PRIMEIRO para garantir que relacionamentos funcionem
            # Isso é necessário porque modelos de plugins podem ter relacionamentos com modelos do core
            # O User precisa estar no namespace antes de qualquer modelo de plugin ser importado
            try:
                from model.user import User  # Garantir que User está disponível para relacionamentos
                # Forçar registro do User no SQLAlchemy antes de importar modelos de plugins
                from db.database import db
                with self.app.app_context():
                    _ = User.__table__  # Força criação do Table do User, registrando no metadata
                logger.debug("Modelo User importado e registrado para relacionamentos de plugins")
            except ImportError as e:
                logger.warning(f"Não foi possível importar modelo User - relacionamentos podem falhar: {e}")
            except Exception as e:
                logger.warning(f"Erro ao registrar modelo User: {e}")
            
            # IMPORTANTE: Prefixar modelos ANTES de registrar rotas para garantir que
            # os modelos prefixados sejam usados nas rotas quando os módulos são importados
            models = plugin.register_models()
            if models:
                # Aplicar prefixo aos nomes das tabelas ANTES de importar rotas
                from .plugin_db_helper import prefix_models
                # Obter nome do diretório do plugin (ex: plugin_meu_plugin)
                plugin_dir_name = plugin.plugin_path.name if hasattr(plugin, 'plugin_path') and plugin.plugin_path else plugin.name
                # Usar nome do diretório do plugin ou nome do plugin como fallback
                plugin_name_for_prefix = plugin_dir_name if plugin_dir_name else plugin.name
                prefixed_models = prefix_models(models, plugin_name_for_prefix, plugin.table_prefix)
                logger.info(f"Modelos prefixados para plugin {plugin.name}: {len(prefixed_models)} (prefixo: {plugin.table_prefix or f'{plugin_name_for_prefix}_'})")
                
                # Garantir que os modelos prefixados sejam registrados no metadata do SQLAlchemy
                # IMPORTANTE: db.create_all() deve ser chamado dentro do app context
                try:
                    from db.database import db
                    
                    # Forçar criação dos objetos Table para cada modelo prefixado
                    # Isso garante que o SQLAlchemy registre os modelos no metadata com os nomes corretos
                    for model in prefixed_models:
                        tablename = getattr(model, '__tablename__', None)
                        if not tablename:
                            continue
                        
                        try:
                            # Acessar __table__ força criação do objeto Table com o __tablename__ atual (prefixado)
                            # O SQLAlchemy automaticamente registra no metadata quando o Table é criado
                            if not hasattr(model, '__table__') or model.__table__ is None:
                                _ = model.__table__  # Força criação
                            
                            # Se o Table já existe mas com nome diferente, atualizar
                            if hasattr(model, '__table__') and model.__table__ is not None:
                                if model.__table__.name != tablename:
                                    model.__table__.name = tablename
                                    logger.debug(f"Nome da tabela atualizado: {model.__table__.name} -> {tablename}")
                        except Exception as model_error:
                            logger.warning(f"Erro ao processar modelo {model.__name__}: {model_error}")
                    
                    # Criar tabelas dos modelos prefixados
                    # IMPORTANTE: Sempre usar app context para db.create_all()
                    with self.app.app_context():
                        db.create_all()
                        logger.info(f"Tabelas criadas/verificadas para modelos do plugin {plugin.name}")
                except Exception as e:
                    logger.error(f"Erro ao criar tabelas para plugin {plugin.name}: {e}", exc_info=True)
            
            # Descobrir todas as rotas de uma vez (após prefixar modelos)
            api_blueprints, web_bp = installer.discover_all_routes()
            
            # Registrar rotas API
            registered_api_count = 0
            for bp in api_blueprints:
                # Verificar se o blueprint já foi registrado para evitar duplicação
                if bp.name not in [b.name for b in self.app.blueprints.values()]:
                    # Determinar prefixo de URL baseado na configuração do plugin
                    url_prefix = self._get_api_url_prefix(plugin)
                    self.app.register_blueprint(bp, url_prefix=url_prefix)
                    
                    # Registrar no sistema de registro de rotas
                    route_registry.register_blueprint(plugin.name, bp)
                    
                    logger.info(f"Blueprint API registrado: {bp.name} com prefixo {url_prefix}")
                    registered_api_count += 1
                else:
                    logger.debug(f"Blueprint API {bp.name} já está registrado, pulando...")
            
            # Registrar rotas web
            if web_bp:
                # Verificar se o blueprint já foi registrado
                if web_bp.name not in [b.name for b in self.app.blueprints.values()]:
                    # Determinar prefixo de URL baseado na configuração do plugin
                    url_prefix = self._get_web_url_prefix(plugin)
                    self.app.register_blueprint(web_bp, url_prefix=url_prefix)
                    
                    # Registrar no sistema de registro de rotas
                    route_registry.register_blueprint(plugin.name, web_bp)
                    
                    logger.info(f"Blueprint web registrado: {web_bp.name} com prefixo {url_prefix or '(sem prefixo)'}")
                else:
                    logger.debug(f"Blueprint web {web_bp.name} já está registrado, pulando...")
            
            # Fallback: usar método register_routes do plugin se não encontrar automaticamente
            if not api_blueprints and not web_bp:
                logger.warning(f"Nenhum blueprint descoberto automaticamente para {plugin.name}, usando register_routes...")
                try:
                    blueprints = plugin.register_routes(self.app)
                    if blueprints:
                        for bp in blueprints:
                            # Verificar se o blueprint já foi registrado
                            if bp.name not in [b.name for b in self.app.blueprints.values()]:
                                url_prefix = self._determine_url_prefix(plugin, bp)
                                self.app.register_blueprint(bp, url_prefix=url_prefix)
                                
                                # Registrar no sistema de registro de rotas
                                route_registry.register_blueprint(plugin.name, bp)
                                
                                logger.info(f"Blueprint registrado via fallback: {bp.name} com prefixo {url_prefix or '(sem prefixo)'}")
                            else:
                                logger.debug(f"Blueprint {bp.name} já está registrado, pulando...")
                except Exception as e:
                    logger.error(f"Erro ao registrar rotas via fallback para {plugin.name}: {e}", exc_info=True)
            
            # Registrar static files se existir
            static_folder = installer.get_static_folder()
            if static_folder:
                # Registrar rota para static files do plugin
                static_url = f"/plugin/{plugin.name}/static"
                self.app.static_url_path = static_url
                logger.info(f"Static folder registrado para plugin {plugin.name}: {static_folder}")
            
            # Modelos já foram prefixados acima, antes de registrar rotas
            
            # Registrar template loader se necessário
            self._update_template_loader()
            
            logger.info(f"Plugin {plugin.name} registrado com sucesso: {registered_api_count} blueprints API, {'1' if web_bp else '0'} blueprint web")
            
        except Exception as e:
            logger.error(f"Erro ao registrar plugin {plugin.name}: {e}", exc_info=True)
    
    def _get_api_url_prefix(self, plugin: PluginBase) -> str:
        """
        Determina o prefixo de URL para rotas API do plugin.
        
        Args:
            plugin: Instância do plugin
            
        Returns:
            Prefixo de URL (padrão: /api)
        """
        # Verificar se há configuração específica no install.json
        route_config = plugin.config.get('routes', {})
        api_prefix = route_config.get('api_prefix', '/api')
        return api_prefix
    
    def _get_web_url_prefix(self, plugin: PluginBase) -> Optional[str]:
        """
        Determina o prefixo de URL para rotas web do plugin.
        
        Args:
            plugin: Instância do plugin
            
        Returns:
            Prefixo de URL ou None (sem prefixo)
        """
        # Verificar se há configuração específica no install.json
        route_config = plugin.config.get('routes', {})
        web_prefix = route_config.get('web_prefix')
        return web_prefix
    
    def _determine_url_prefix(self, plugin: PluginBase, blueprint: Blueprint) -> Optional[str]:
        """
        Determina o prefixo de URL baseado no nome do blueprint.
        
        Args:
            plugin: Instância do plugin
            blueprint: Blueprint a ser registrado
            
        Returns:
            Prefixo de URL ou None
        """
        bp_name_lower = blueprint.name.lower()
        
        # Blueprints de API geralmente têm nomes específicos
        api_keywords = ['api', 'ingredientes', 'receitas', 'calculos', 'upload', 
                       'dispositivos', 'notifications', 'brewfather', 'dashboard', 
                       'envase', 'estoque', 'config']
        
        if any(keyword in bp_name_lower for keyword in api_keywords):
            return self._get_api_url_prefix(plugin)
        
        # Rotas web podem ter prefixo ou não
        return self._get_web_url_prefix(plugin)
    
    def _update_template_loader(self):
        """Atualiza o template loader com os plugins ativos."""
        # Criar loader customizado
        plugin_loader = PluginTemplateLoader(self.plugins_dir, self.active_plugins)
        
        # Adicionar ao jinja_env
        # Jinja2 3.x usa uma lista de loaders
        if hasattr(self.app.jinja_env, 'loader'):
            # Se já tem um loader, criar um ChoiceLoader
            from jinja2 import ChoiceLoader
            existing_loader = self.app.jinja_env.loader
            self.app.jinja_env.loader = ChoiceLoader([plugin_loader, existing_loader])
        else:
            # Se não tem loader, usar apenas o plugin loader
            self.app.jinja_env.loader = plugin_loader
        
        logger.debug("Template loader de plugins atualizado")
    
    def install_plugin(self, plugin_name: str) -> bool:
        """
        Instala um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se instalado com sucesso
        """
        if plugin_name not in self.plugins:
            logger.error(f"Plugin não encontrado: {plugin_name}")
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Verificar dependências
        for dep in plugin.dependencies:
            if dep not in self.installed_plugins:
                logger.error(f"Dependência não instalada: {dep}")
                return False
        
        try:
            # Chamar método install do plugin
            if plugin.install():
                plugin.is_installed = True
                if plugin_name not in self.installed_plugins:
                    self.installed_plugins.append(plugin_name)
                self._save_config()
                logger.info(f"Plugin instalado: {plugin_name}")
                return True
        except Exception as e:
            logger.error(f"Erro ao instalar plugin {plugin_name}: {e}")
        
        return False
    
    def uninstall_plugin(self, plugin_name: str) -> bool:
        """
        Desinstala um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se desinstalado com sucesso
        """
        if plugin_name not in self.plugins:
            logger.error(f"Plugin não encontrado: {plugin_name}")
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Desativar antes de desinstalar
        if plugin_name in self.active_plugins:
            self.deactivate_plugin(plugin_name)
        
        try:
            # Chamar método uninstall do plugin
            if plugin.uninstall():
                plugin.is_installed = False
                if plugin_name in self.installed_plugins:
                    self.installed_plugins.remove(plugin_name)
                self._save_config()
                logger.info(f"Plugin desinstalado: {plugin_name}")
                return True
        except Exception as e:
            logger.error(f"Erro ao desinstalar plugin {plugin_name}: {e}")
        
        return False
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Ativa um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se ativado com sucesso
        """
        if plugin_name not in self.plugins:
            logger.error(f"Plugin não encontrado: {plugin_name}")
            return False
        
        plugin = self.plugins[plugin_name]
        
        if not plugin.is_installed:
            logger.error(f"Plugin não está instalado: {plugin_name}")
            return False
        
        try:
            if plugin.activate():
                if plugin_name not in self.active_plugins:
                    self.active_plugins.append(plugin_name)
                self._register_plugin(plugin)
                self._save_config()
                logger.info(f"Plugin ativado: {plugin_name}")
                return True
        except Exception as e:
            logger.error(f"Erro ao ativar plugin {plugin_name}: {e}")
        
        return False
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Desativa um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se desativado com sucesso
        """
        if plugin_name not in self.plugins:
            logger.error(f"Plugin não encontrado: {plugin_name}")
            return False
        
        plugin = self.plugins[plugin_name]
        
        try:
            if plugin.deactivate():
                if plugin_name in self.active_plugins:
                    self.active_plugins.remove(plugin_name)
                self._update_template_loader()
                self._save_config()
                logger.info(f"Plugin desativado: {plugin_name}")
                return True
        except Exception as e:
            logger.error(f"Erro ao desativar plugin {plugin_name}: {e}")
        
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """
        Obtém uma instância de plugin.
        
        Busca primeiro pelo nome do diretório, depois pelo nome do install.json.
        
        Args:
            plugin_name: Nome do plugin (diretório ou install.json)
            
        Returns:
            Instância do plugin ou None
        """
        # Tentar buscar pelo nome do diretório primeiro
        plugin = self.plugins.get(plugin_name)
        if plugin:
            return plugin
        
        # Se não encontrar, buscar pelo nome do install.json
        for p_name, p_instance in self.plugins.items():
            if p_instance.name == plugin_name:
                return p_instance
        
        return None
    
    def get_all_plugins(self) -> Dict[str, PluginBase]:
        """
        Retorna todos os plugins carregados.
        
        Returns:
            Dicionário de plugins
        """
        return self.plugins.copy()
    
    def get_active_plugins(self) -> List[str]:
        """
        Retorna lista de plugins ativos.
        
        Returns:
            Lista de nomes de plugins ativos
        """
        return self.active_plugins.copy()
    
    def get_menu_items(self) -> List[Dict]:
        """
        Retorna itens de menu de todos os plugins ativos.
        
        Estrutura o menu com o nome do plugin como item principal
        e os itens do menu_config.json como sub-itens.
        
        Returns:
            Lista de itens de menu formatados com estrutura:
            - Plugin (item principal)
              -- Item 1 (sub-item)
              -- Item 2 (sub-item)
        """
        menu_items = []
        
        # Usar um set para evitar processar o mesmo plugin duas vezes
        processed_plugins = set()
        
        for plugin_name in self.active_plugins:
            # Buscar plugin pelo nome do diretório ou pelo nome do install.json
            plugin = self.plugins.get(plugin_name)
            if not plugin:
                # Tentar buscar pelo nome do install.json
                for p_name, p_instance in self.plugins.items():
                    if p_instance.name == plugin_name:
                        plugin = p_instance
                        # Usar o nome do diretório como chave única
                        plugin_name = p_name
                        break
            
            if plugin:
                # Evitar processar o mesmo plugin duas vezes
                # Usar o nome do diretório como identificador único
                plugin_dir_name = None
                for p_name, p_instance in self.plugins.items():
                    if p_instance is plugin:
                        plugin_dir_name = p_name
                        break
                
                if plugin_dir_name and plugin_dir_name in processed_plugins:
                    continue  # Já processamos este plugin
                
                if plugin_dir_name:
                    processed_plugins.add(plugin_dir_name)
                
                # Carregar configuração de menu
                menu_config = plugin.get_menu_config()
                main_items = menu_config.get('main_items', [])
                
                if not main_items:
                    continue  # Plugin sem itens de menu
                
                # Criar item principal do plugin
                # Prioridade: label > name > nome do diretório formatado
                if plugin.label:
                    plugin_label = plugin.label
                elif plugin.name:
                    plugin_label = plugin.name
                else:
                    plugin_label = plugin_dir_name.replace('_', ' ').title()
                plugin_id = f"plugin_{plugin_dir_name}"
                
                # Criar item principal do plugin com todos os itens como children
                plugin_menu_item = {
                    'id': plugin_id,
                    'label': plugin_label,
                    'icon': 'bi bi-puzzle',  # Ícone padrão para plugins
                    'url': '',  # Plugin não tem URL própria
                    'children': []
                }
                
                # Adicionar todos os itens do menu como sub-itens do plugin
                for item in main_items:
                    formatted_item = {
                        'id': item.get('id', ''),
                        'label': item.get('label', ''),
                        'icon': item.get('icon', 'bi bi-circle'),
                        'url': item.get('url', ''),
                        'children': []
                    }
                    
                    # Processar children (submenu) se existir
                    if 'children' in item and item['children']:
                        for child in item['children']:
                            formatted_item['children'].append({
                                'label': child.get('label', ''),
                                'icon': child.get('icon', 'bi bi-circle'),
                                'url': child.get('url', '')
                            })
                    
                    plugin_menu_item['children'].append(formatted_item)
                
                # Adicionar item do plugin ao menu
                menu_items.append(plugin_menu_item)
        
        return menu_items

