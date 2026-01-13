"""
Helper para carregar modelos prefixados do plugin.

Este módulo garante que os modelos sejam sempre carregados com os prefixos
corretos aplicados às tabelas. Use este helper em vez de importar diretamente
de model.* para garantir que os modelos prefixados sejam usados.
"""

from flask import current_app
from core.plugin_model_registry import get_prefixed_model

# Nome do plugin
PLUGIN_NAME = "plugin_device_manager"


def _get_prefixed_model(model_class_name: str):
    """
    Obtém um modelo prefixado do registry.
    
    Args:
        model_class_name: Nome da classe do modelo (ex: 'DeviceMetadata')
        
    Returns:
        Classe do modelo prefixado ou None se não encontrado
    """
    prefixed_model = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed_model:
        return prefixed_model
    
    # Fallback: importar diretamente do plugin
    try:
        from plugins.plugin_device_manager.model.device_metadata import DeviceMetadata
        from plugins.plugin_device_manager.model.device_function import DeviceFunction
        from plugins.plugin_device_manager.model.device_actor import DeviceActor
        
        model_map = {
            'DeviceMetadata': DeviceMetadata,
            'DeviceFunction': DeviceFunction,
            'DeviceActor': DeviceActor,
        }
        
        return model_map.get(model_class_name)
    except ImportError:
        pass
    
    return None


# Funções helper para obter modelos específicos
def get_device_metadata():
    """Obtém o modelo DeviceMetadata prefixado"""
    return _get_prefixed_model('DeviceMetadata')


def get_device_function():
    """Obtém o modelo DeviceFunction prefixado"""
    return _get_prefixed_model('DeviceFunction')


def get_device_actor():
    """Obtém o modelo DeviceActor prefixado"""
    return _get_prefixed_model('DeviceActor')


# Exportar modelos diretamente para uso nas rotas
# NOTA: Os modelos abaixo serão prefixados pelo plugin_manager quando o plugin for carregado.
from plugins.plugin_device_manager.model.device_metadata import DeviceMetadata
from plugins.plugin_device_manager.model.device_function import DeviceFunction
from plugins.plugin_device_manager.model.device_actor import DeviceActor
