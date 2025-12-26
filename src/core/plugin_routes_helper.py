"""
Helper para facilitar a criação e registro de rotas de plugins.

Este módulo fornece utilitários para criar rotas de plugins de forma padronizada
e facilitar a navegação entre rotas de diferentes plugins.
"""

from typing import List, Dict, Any, Optional, Callable
from flask import Blueprint, url_for
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class PluginRouteRegistry:
    """
    Registro centralizado de rotas de plugins.
    
    Mantém metadados sobre todas as rotas registradas pelos plugins,
    facilitando a navegação e descoberta de rotas.
    """
    
    def __init__(self):
        """Inicializa o registro."""
        self._routes: Dict[str, Dict[str, Any]] = {}
        self._blueprints: Dict[str, Blueprint] = {}
    
    def register_route(
        self,
        plugin_name: str,
        blueprint_name: str,
        route_path: str,
        endpoint: str,
        methods: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Registra uma rota no sistema.
        
        Args:
            plugin_name: Nome do plugin
            blueprint_name: Nome do blueprint
            route_path: Caminho da rota (ex: '/maltes')
            endpoint: Nome do endpoint (ex: 'ingredientes.get_maltes')
            methods: Métodos HTTP permitidos
            metadata: Metadados adicionais da rota
        """
        route_key = f"{plugin_name}:{endpoint}"
        self._routes[route_key] = {
            'plugin_name': plugin_name,
            'blueprint_name': blueprint_name,
            'route_path': route_path,
            'endpoint': endpoint,
            'methods': methods or ['GET'],
            'metadata': metadata or {}
        }
        logger.debug(f"Rota registrada: {route_key} -> {route_path}")
    
    def register_blueprint(self, plugin_name: str, blueprint: Blueprint):
        """
        Registra um blueprint no sistema.
        
        Args:
            plugin_name: Nome do plugin
            blueprint: Instância do Blueprint
        """
        self._blueprints[f"{plugin_name}:{blueprint.name}"] = blueprint
        logger.debug(f"Blueprint registrado: {plugin_name}:{blueprint.name}")
    
    def get_route(self, plugin_name: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações sobre uma rota específica.
        
        Args:
            plugin_name: Nome do plugin
            endpoint: Nome do endpoint
            
        Returns:
            Dicionário com informações da rota ou None
        """
        route_key = f"{plugin_name}:{endpoint}"
        return self._routes.get(route_key)
    
    def get_plugin_routes(self, plugin_name: str) -> List[Dict[str, Any]]:
        """
        Obtém todas as rotas de um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            Lista de rotas do plugin
        """
        return [
            route for route_key, route in self._routes.items()
            if route['plugin_name'] == plugin_name
        ]
    
    def get_all_routes(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtém todas as rotas registradas.
        
        Returns:
            Dicionário com todas as rotas
        """
        return self._routes.copy()
    
    def build_url(self, plugin_name: str, endpoint: str, **values) -> str:
        """
        Constrói URL para uma rota de plugin.
        
        Args:
            plugin_name: Nome do plugin
            endpoint: Nome do endpoint
            **values: Valores para a URL
            
        Returns:
            URL construída ou '#' se não encontrada
        """
        route = self.get_route(plugin_name, endpoint)
        if not route:
            logger.warning(f"Rota não encontrada: {plugin_name}:{endpoint}")
            return '#'
        
        try:
            return url_for(route['endpoint'], **values)
        except Exception as e:
            logger.debug(f"Erro ao construir URL para {plugin_name}:{endpoint}: {e}")
            return '#'


# Instância global do registro
_route_registry = PluginRouteRegistry()


def get_route_registry() -> PluginRouteRegistry:
    """
    Obtém a instância global do registro de rotas.
    
    Returns:
        Instância do PluginRouteRegistry
    """
    return _route_registry


def create_plugin_api_blueprint(
    plugin_name: str,
    blueprint_name: str,
    url_prefix: str = None,
    import_name: str = __name__
) -> Blueprint:
    """
    Cria um blueprint de API para um plugin.
    
    Args:
        plugin_name: Nome do plugin
        blueprint_name: Nome do blueprint (usado como identificador)
        url_prefix: Prefixo de URL (padrão: /api)
        import_name: Nome do módulo importador
        
    Returns:
        Blueprint configurado
    """
    if url_prefix is None:
        url_prefix = f"/api"
    
    bp = Blueprint(
        blueprint_name,
        import_name,
        url_prefix=url_prefix
    )
    
    # Registrar blueprint no registro
    _route_registry.register_blueprint(plugin_name, bp)
    
    logger.debug(f"Blueprint de API criado: {plugin_name}:{blueprint_name}")
    return bp


def create_plugin_web_blueprint(
    plugin_name: str,
    blueprint_name: str = None,
    url_prefix: str = None,
    import_name: str = __name__
) -> Blueprint:
    """
    Cria um blueprint web para um plugin.
    
    Args:
        plugin_name: Nome do plugin
        blueprint_name: Nome do blueprint (padrão: plugin_{plugin_name}_web)
        url_prefix: Prefixo de URL (padrão: sem prefixo)
        import_name: Nome do módulo importador
        
    Returns:
        Blueprint configurado
    """
    if blueprint_name is None:
        blueprint_name = f"plugin_{plugin_name}_web"
    
    bp = Blueprint(
        blueprint_name,
        import_name,
        url_prefix=url_prefix
    )
    
    # Registrar blueprint no registro
    _route_registry.register_blueprint(plugin_name, bp)
    
    logger.debug(f"Blueprint web criado: {plugin_name}:{blueprint_name}")
    return bp


def register_plugin_route(
    blueprint: Blueprint,
    plugin_name: str,
    route_path: str,
    methods: List[str] = None,
    metadata: Dict[str, Any] = None
):
    """
    Decorator para registrar rotas de plugin de forma padronizada.
    
    Args:
        blueprint: Blueprint onde a rota será registrada
        plugin_name: Nome do plugin
        route_path: Caminho da rota
        methods: Métodos HTTP permitidos
        metadata: Metadados adicionais da rota
        
    Returns:
        Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        
        # Registrar rota no blueprint
        endpoint = f"{blueprint.name}.{f.__name__}"
        blueprint.add_url_rule(
            route_path,
            endpoint=f.__name__,
            view_func=wrapper,
            methods=methods or ['GET']
        )
        
        # Registrar no sistema de registro
        _route_registry.register_route(
            plugin_name=plugin_name,
            blueprint_name=blueprint.name,
            route_path=route_path,
            endpoint=endpoint,
            methods=methods or ['GET'],
            metadata=metadata or {}
        )
        
        logger.debug(f"Rota registrada: {plugin_name} -> {endpoint} ({route_path})")
        return wrapper
    
    return decorator


def plugin_route(
    blueprint: Blueprint,
    plugin_name: str,
    route_path: str,
    methods: List[str] = None,
    **metadata
):
    """
    Decorator simplificado para registrar rotas de plugin.
    
    Uso:
        @plugin_route(bp, 'meu_plugin', '/maltes', methods=['GET'])
        def get_maltes():
            ...
    
    Args:
        blueprint: Blueprint onde a rota será registrada
        plugin_name: Nome do plugin
        route_path: Caminho da rota
        methods: Métodos HTTP permitidos
        **metadata: Metadados adicionais da rota
        
    Returns:
        Decorator function
    """
    return register_plugin_route(blueprint, plugin_name, route_path, methods, metadata)

