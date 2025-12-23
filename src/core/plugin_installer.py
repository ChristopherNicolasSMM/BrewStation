"""
Sistema de instalação automática de plugins para BrewStation.
Registra automaticamente rotas, templates, static files e menu baseado no install.json.
"""

import importlib.util
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from flask import Blueprint
import logging

logger = logging.getLogger(__name__)


class PluginInstaller:
    """
    Instalador automático de plugins.
    
    Responsável por descobrir e registrar automaticamente:
    - Rotas da pasta api/routes/
    - Templates da pasta templates/
    - Static files da pasta static/
    - Menu do install.json
    """
    
    def __init__(self, plugin_path: Path, config: Dict[str, Any]):
        """
        Inicializa o instalador.
        
        Args:
            plugin_path: Caminho do diretório do plugin
            config: Configuração do plugin (install.json)
        """
        self.plugin_path = Path(plugin_path)
        self.config = config
        self.name = config.get('name', '')
        
    def discover_api_routes(self) -> List[Blueprint]:
        """
        Descobre e carrega blueprints da pasta api/routes/.
        
        Returns:
            Lista de blueprints encontrados
        """
        blueprints = []
        api_routes_path = self.plugin_path / 'api' / 'routes'
        
        if not api_routes_path.exists():
            logger.debug(f"Pasta api/routes não encontrada para plugin {self.name}")
            return blueprints
        
        # Tentar carregar __init__.py que exporta os blueprints
        routes_init = api_routes_path / '__init__.py'
        if routes_init.exists():
            try:
                # Adicionar src ao path se necessário
                src_path = self.plugin_path.parent.parent
                if str(src_path) not in sys.path:
                    sys.path.insert(0, str(src_path))
                
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{self.plugin_path.name}.api.routes",
                    routes_init
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Procurar por blueprints exportados
                    # Geralmente em all_blueprints ou como atributos do módulo
                    if hasattr(module, 'all_blueprints'):
                        blueprints.extend(module.all_blueprints)
                    else:
                        # Procurar por atributos que são Blueprints
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, Blueprint):
                                blueprints.append(attr)
                    
                    logger.info(f"Blueprints API descobertos para plugin {self.name}: {len(blueprints)}")
            except Exception as e:
                logger.error(f"Erro ao carregar rotas API do plugin {self.name}: {e}")
        
        return blueprints
    
    def discover_web_routes(self) -> Optional[Blueprint]:
        """
        Descobre blueprint web da pasta controller/routes.py.
        
        Returns:
            Blueprint web ou None
        """
        controller_routes = self.plugin_path / 'controller' / 'routes.py'
        
        if not controller_routes.exists():
            logger.debug(f"controller/routes.py não encontrado para plugin {self.name}")
            return None
        
        try:
            # Adicionar src ao path se necessário
            src_path = self.plugin_path.parent.parent
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))
            
            spec = importlib.util.spec_from_file_location(
                f"plugins.{self.plugin_path.name}.controller.routes",
                controller_routes
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Procurar por web_plugin_bp ou blueprint similar
                if hasattr(module, 'web_plugin_bp'):
                    return module.web_plugin_bp
                else:
                    # Procurar por qualquer Blueprint
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, Blueprint):
                            return attr
                
                logger.info(f"Blueprint web descoberto para plugin {self.name}")
        except Exception as e:
            logger.error(f"Erro ao carregar rotas web do plugin {self.name}: {e}")
        
        return None
    
    def get_menu_items(self) -> List[Dict[str, Any]]:
        """
        Extrai itens de menu do install.json.
        
        Returns:
            Lista de itens de menu formatados
        """
        menu_config = self.config.get('menu', {})
        main_items = menu_config.get('main_items', [])
        
        # Formatar itens de menu para uso no template
        formatted_items = []
        for item in main_items:
            formatted_item = {
                'id': item.get('id', ''),
                'label': item.get('label', ''),
                'icon': item.get('icon', 'bi bi-circle'),
                'url': item.get('url', ''),
                'children': []
            }
            
            # Processar children (submenu)
            if 'children' in item:
                for child in item['children']:
                    formatted_item['children'].append({
                        'label': child.get('label', ''),
                        'icon': child.get('icon', 'bi bi-circle'),
                        'url': child.get('url', '')
                    })
            
            formatted_items.append(formatted_item)
        
        return formatted_items
    
    def get_static_folder(self) -> Optional[Path]:
        """
        Retorna o caminho da pasta static do plugin.
        
        Returns:
            Path da pasta static ou None
        """
        static_path = self.plugin_path / 'static'
        if static_path.exists() and static_path.is_dir():
            return static_path
        return None
    
    def get_templates_folder(self) -> Optional[Path]:
        """
        Retorna o caminho da pasta templates do plugin.
        
        Returns:
            Path da pasta templates ou None
        """
        templates_path = self.plugin_path / 'templates'
        if templates_path.exists() and templates_path.is_dir():
            return templates_path
        return None

