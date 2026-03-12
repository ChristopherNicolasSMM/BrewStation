"""
Helper para carregar modelos prefixados do plugin.

Este módulo garante que os modelos sejam sempre carregados com os prefixos
corretos aplicados às tabelas. Use este helper em vez de importar diretamente
de model.* para garantir que os modelos prefixados sejam usados.

IMPORTANTE: Se você criar modelos em model/, atualize este arquivo para
incluir funções helper para cada modelo.
"""

from flask import current_app
from core.plugin_model_registry import get_prefixed_model

# Nome do plugin (ajuste se necessário)
PLUGIN_NAME = "plugin_mash_control"


def _get_prefixed_model(model_class_name: str):
    """
    Obtém um modelo prefixado do registry.
    
    Args:
        model_class_name: Nome da classe do modelo (ex: 'MeuModelo')
        
    Returns:
        Classe do modelo prefixado ou None se não encontrado
    """
    prefixed_model = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed_model:
        return prefixed_model
    
    # Fallback: importar diretamente do plugin
    try:
        from plugins.plugin_mash_control.model.mash_models import (
            MashRecipe, BrewSession, DashboardLayout, Plant
        )
        
        model_map = {
            'MashRecipe': MashRecipe,
            'BrewSession': BrewSession,
            'DashboardLayout': DashboardLayout,
            'Plant': Plant
        }
        
        return model_map.get(model_class_name)
    except ImportError:
        pass
    
    return None


# Funções helper para obter modelos específicos
def get_mash_recipe():
    """Obtém o modelo MashRecipe prefixado"""
    return _get_prefixed_model('MashRecipe')


def get_brew_session():
    """Obtém o modelo BrewSession prefixado"""
    return _get_prefixed_model('BrewSession')


def get_dashboard_layout():
    """Obtém o modelo DashboardLayout prefixado"""
    return _get_prefixed_model('DashboardLayout')


def get_plant():
    """Obtém o modelo Plant prefixado"""
    return _get_prefixed_model('Plant')


# Exportar modelos diretamente para uso nas rotas
# NOTA: Os modelos abaixo serão prefixados pelo plugin_manager quando o plugin for carregado.
from plugins.plugin_mash_control.model.mash_models import (
    MashRecipe, BrewSession, DashboardLayout, Plant
)
