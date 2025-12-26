"""
Sistema de instalação automática de plugins para BrewStation.
Registra automaticamente rotas, templates, static files e menu baseado no install.json.
"""

import importlib.util
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
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
        # Garantir que o caminho seja absoluto para evitar problemas com resolve()
        self.plugin_path = Path(plugin_path).resolve()
        self.config = config
        self.name = config.get('name', '')
        
        # Calcular e garantir que src está no sys.path
        self._ensure_src_in_path()
    
    def _ensure_src_in_path(self):
        """Garante que o diretório src está no sys.path."""
        # Calcular caminho para src (plugin_path é src/plugins/plugin_name, então parent.parent é src)
        src_path = self.plugin_path.parent.parent.resolve()
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            logger.debug(f"Adicionado {src_path} ao sys.path")
        
    def discover_api_routes(self) -> List[Blueprint]:
        """
        Descobre e carrega blueprints da pasta api/routes/.
        
        Este método procura por:
        1. Arquivo __init__.py que exporta all_blueprints ou blueprints individuais
        2. Arquivos individuais de rotas (*_routes.py) que exportam blueprints
        
        Returns:
            Lista de blueprints encontrados
        """
        blueprints = []
        api_routes_path = self.plugin_path / 'api' / 'routes'
        
        if not api_routes_path.exists():
            logger.debug(f"Pasta api/routes não encontrada para plugin {self.name}")
            return blueprints
        
        # Método 1: Tentar carregar __init__.py que exporta os blueprints
        routes_init = api_routes_path / '__init__.py'
        if routes_init.exists():
            try:
                blueprints.extend(self._load_blueprints_from_module(routes_init))
            except Exception as e:
                logger.error(f"Erro ao carregar __init__.py do plugin {self.name}: {e}", exc_info=True)
        
        # Método 2: Procurar por arquivos individuais de rotas
        if not blueprints:
            route_files = list(api_routes_path.glob("*_routes.py"))
            for route_file in route_files:
                try:
                    file_blueprints = self._load_blueprints_from_module(route_file)
                    blueprints.extend(file_blueprints)
                except Exception as e:
                    logger.warning(f"Erro ao carregar {route_file.name} do plugin {self.name}: {e}")
        
        logger.info(f"Blueprints API descobertos para plugin {self.name}: {len(blueprints)}")
        if blueprints:
            logger.debug(f"Nomes dos blueprints encontrados: {[bp.name for bp in blueprints]}")
        
        return blueprints
    
    def _load_blueprints_from_module(self, module_path: Path) -> List[Blueprint]:
        """
        Carrega blueprints de um módulo Python.
        
        Args:
            module_path: Caminho para o arquivo Python
            
        Returns:
            Lista de blueprints encontrados
        """
        blueprints = []
        
        # Garantir que src está no sys.path antes de executar qualquer módulo
        self._ensure_src_in_path()
        
        # Usar caminho absoluto para garantir que __file__ seja definido corretamente
        module_path_abs = module_path.resolve()
        
        # Determinar nome do módulo baseado no caminho
        # De: src/plugins/plugin_name/api/routes/__init__.py
        # Para: plugins.plugin_name.api.routes
        # De: src/plugins/plugin_name/controller/routes.py
        # Para: plugins.plugin_name.controller.routes
        parts = module_path_abs.parts
        try:
            # Encontrar índice de 'plugins' ou 'src'
            if 'plugins' in parts:
                idx = parts.index('plugins')
                module_parts = list(parts[idx:-1])  # Excluir o nome do arquivo e converter para lista
                if module_path.name != '__init__.py':
                    module_parts.append(module_path.stem)  # Adicionar nome do arquivo sem extensão
                module_name = '.'.join(module_parts)
            else:
                # Fallback: usar nome baseado no caminho relativo
                # Determinar se é api/routes ou controller/routes
                if 'controller' in parts:
                    module_name = f"plugins.{self.plugin_path.name}.controller"
                else:
                    module_name = f"plugins.{self.plugin_path.name}.api.routes"
                if module_path.name != '__init__.py':
                    module_name += f".{module_path.stem}"
        except (ValueError, IndexError):
            # Fallback para nome genérico baseado no caminho
            if 'controller' in str(module_path):
                module_name = f"plugins.{self.plugin_path.name}.controller.routes"
            else:
                module_name = f"plugins.{self.plugin_path.name}.api.routes"
        
        spec = importlib.util.spec_from_file_location(module_name, module_path_abs)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Procurar por blueprints exportados
            # Prioridade 1: all_blueprints (lista)
            if hasattr(module, 'all_blueprints'):
                all_bps = module.all_blueprints
                if isinstance(all_bps, list):
                    blueprints.extend(all_bps)
                elif isinstance(all_bps, Blueprint):
                    blueprints.append(all_bps)
            
            # Prioridade 2: Procurar por atributos que são Blueprints
            # Ignorar atributos privados e especiais
            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    continue
                attr = getattr(module, attr_name)
                if isinstance(attr, Blueprint):
                    # Evitar duplicatas
                    if attr not in blueprints:
                        blueprints.append(attr)
                        logger.debug(f"Blueprint encontrado no módulo {module_name}: {attr_name} ({attr.name})")
        
        return blueprints
    
    def discover_web_routes(self) -> Optional[Blueprint]:
        """
        Descobre blueprint web da pasta controller/routes.py.
        
        Este método procura por:
        1. web_plugin_bp (padrão)
        2. Qualquer Blueprint exportado no módulo
        
        Returns:
            Blueprint web ou None
        """
        controller_routes = self.plugin_path / 'controller' / 'routes.py'
        
        if not controller_routes.exists():
            logger.debug(f"controller/routes.py não encontrado para plugin {self.name}")
            return None
        
        try:
            blueprints = self._load_blueprints_from_module(controller_routes)
            
            if blueprints:
                # Prioridade 1: web_plugin_bp
                for bp in blueprints:
                    if bp.name == 'web_plugin_bp' or 'web' in bp.name.lower():
                        logger.info(f"Blueprint web descoberto para plugin {self.name}: {bp.name}")
                        return bp
                
                # Prioridade 2: primeiro blueprint encontrado
                logger.info(f"Blueprint web descoberto para plugin {self.name}: {blueprints[0].name}")
                return blueprints[0]
        except Exception as e:
            logger.error(f"Erro ao carregar rotas web do plugin {self.name}: {e}", exc_info=True)
        
        return None
    
    def discover_all_routes(self) -> Tuple[List[Blueprint], Optional[Blueprint]]:
        """
        Descobre todas as rotas do plugin (API e Web).
        
        Returns:
            Tupla com (lista de blueprints API, blueprint web)
        """
        api_routes = self.discover_api_routes()
        web_routes = self.discover_web_routes()
        
        return api_routes, web_routes
    
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

