"""
Exemplo de como usar o sistema de rotas de plugins.

Este arquivo demonstra como criar rotas de plugins usando o novo sistema
de registro de rotas.
"""

from flask import jsonify, render_template
from flask_login import login_required

from .plugin_routes_helper import (create_plugin_api_blueprint,
                                   create_plugin_web_blueprint,
                                   get_route_registry, plugin_route)

# Exemplo 1: Criar blueprint de API para um plugin
# =================================================

def create_example_api_routes(plugin_name: str):
    """
    Exemplo de criação de rotas API para um plugin.
    
    Args:
        plugin_name: Nome do plugin (ex: 'meu_plugin')
    """
    # Criar blueprint de API
    api_bp = create_plugin_api_blueprint(
        plugin_name=plugin_name,
        blueprint_name='exemplo_api',
        url_prefix='/api'  # Opcional, padrão é /api
    )
    
    # Registrar rotas usando o decorator simplificado
    @plugin_route(api_bp, plugin_name, '/exemplo/maltes', methods=['GET'])
    @login_required
    def get_maltes():
        """Obter lista de maltes"""
        # Sua lógica aqui
        return jsonify({'maltes': []}), 200
    
    @plugin_route(api_bp, plugin_name, '/exemplo/maltes', methods=['POST'])
    @login_required
    def create_malte():
        """Criar novo malte"""
        # Sua lógica aqui
        return jsonify({'message': 'Malte criado'}), 201
    
    return api_bp


# Exemplo 2: Criar blueprint web para um plugin
# =============================================

def create_example_web_routes(plugin_name: str):
    """
    Exemplo de criação de rotas web para um plugin.
    
    Args:
        plugin_name: Nome do plugin (ex: 'meu_plugin')
    """
    # Criar blueprint web
    web_bp = create_plugin_web_blueprint(
        plugin_name=plugin_name,
        blueprint_name=f'plugin_{plugin_name}_web',
        url_prefix=None  # Sem prefixo, rotas diretas como /maltes
    )
    
    # Registrar rotas usando o decorator simplificado
    @plugin_route(web_bp, plugin_name, '/maltes', methods=['GET'])
    @login_required
    def maltes_page():
        """Página de maltes"""
        # Renderizar template do plugin
        return render_template('maltes.html')
    
    @plugin_route(web_bp, plugin_name, '/lupulos', methods=['GET'])
    @login_required
    def lupulos_page():
        """Página de lúpulos"""
        return render_template('lupulos.html')
    
    return web_bp


# Exemplo 3: Usar o registro de rotas para navegação
# ===================================================

def exemplo_navegacao():
    """
    Exemplo de como usar o registro de rotas para construir URLs.
    """
    route_registry = get_route_registry()
    
    # Obter todas as rotas de um plugin
    plugin_routes = route_registry.get_plugin_routes('meu_plugin')
    print(f"Rotas do plugin: {plugin_routes}")
    
    # Construir URL para uma rota específica
    url = route_registry.build_url('meu_plugin', 'exemplo_api.get_maltes')
    print(f"URL da rota: {url}")
    
    # Obter informações sobre uma rota específica
    route_info = route_registry.get_route('meu_plugin', 'exemplo_api.get_maltes')
    if route_info:
        print(f"Informações da rota: {route_info}")


# Exemplo 4: Estrutura completa de um arquivo de rotas de plugin
# ===============================================================

"""
# Em seu arquivo: plugins/meu_plugin/api/routes/__init__.py

from flask import Blueprint
from core.plugin_routes_helper import create_plugin_api_blueprint, plugin_route
from flask_login import login_required
from flask import jsonify

# Criar blueprint
api_bp = create_plugin_api_blueprint(
    plugin_name='meu_plugin',
    blueprint_name='meu_plugin_api'
)

# Registrar rotas
@plugin_route(api_bp, 'meu_plugin', '/maltes', methods=['GET'])
@login_required
def get_maltes():
    return jsonify({'maltes': []}), 200

# Exportar blueprint
all_blueprints = [api_bp]
"""

