"""
Plugin manager for BrewStation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from flask import Flask
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
                plugin_key = plugin.name if plugin.name else plugin_name
                if plugin_key in self.active_plugins:
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
            installer = PluginInstaller(plugin.plugin_path, plugin.config)
            
            # Registrar rotas API
            api_blueprints = installer.discover_api_routes()
            for bp in api_blueprints:
                # Blueprints de API usam prefixo /api
                self.app.register_blueprint(bp, url_prefix="/api")
                logger.info(f"Blueprint API registrado: {bp.name} com prefixo /api")
            
            # Registrar rotas web
            web_bp = installer.discover_web_routes()
            if web_bp:
                # Rotas web do plugin são registradas sem prefixo
                # O blueprint já define as rotas diretamente (ex: /maltes, /lupulos)
                self.app.register_blueprint(web_bp)
                logger.info(f"Blueprint web registrado: {web_bp.name} (sem prefixo)")
            
            # Fallback: usar método register_routes do plugin se não encontrar automaticamente
            if not api_blueprints and not web_bp:
                blueprints = plugin.register_routes(self.app)
                if blueprints:
                    for bp in blueprints:
                        bp_name_lower = bp.name.lower()
                        if 'api' in bp_name_lower or bp_name_lower.startswith('ingredientes') or \
                           bp_name_lower.startswith('receitas') or bp_name_lower.startswith('calculos') or \
                           bp_name_lower.startswith('upload') or bp_name_lower.startswith('dispositivos') or \
                           bp_name_lower.startswith('notifications') or bp_name_lower.startswith('brewfather') or \
                           bp_name_lower.startswith('dashboard') or bp_name_lower.startswith('envase') or \
                           bp_name_lower.startswith('estoque') or bp_name_lower.startswith('config'):
                            url_prefix = "/api"
                        else:
                            url_prefix = f"/plugin/{plugin.name}"
                        self.app.register_blueprint(bp, url_prefix=url_prefix)
                        logger.info(f"Blueprint registrado: {bp.name} com prefixo {url_prefix}")
            
            # Registrar static files se existir
            static_folder = installer.get_static_folder()
            if static_folder:
                # Registrar rota para static files do plugin
                static_url = f"/plugin/{plugin.name}/static"
                self.app.static_url_path = static_url
                logger.info(f"Static folder registrado para plugin {plugin.name}: {static_folder}")
            
            # Registrar modelos
            models = plugin.register_models()
            if models:
                logger.info(f"Modelos registrados para plugin {plugin.name}: {len(models)}")
            
            # Registrar template loader se necessário
            self._update_template_loader()
            
        except Exception as e:
            logger.error(f"Erro ao registrar plugin {plugin.name}: {e}", exc_info=True)
    
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

