"""
Registry para armazenar modelos prefixados de plugins.

Este módulo mantém um registro dos modelos prefixados para garantir que
os modelos corretos sejam sempre usados nas rotas dos plugins.
"""

import logging
from typing import Dict, Optional, Type

logger = logging.getLogger(__name__)

# Registry global para modelos prefixados por plugin
_prefixed_models_registry: Dict[str, Dict[str, Type]] = {}


def register_prefixed_model(plugin_name: str, model_class: Type, original_tablename: str):
    """
    Registra um modelo prefixado no registry.
    
    Args:
        plugin_name: Nome do plugin
        model_class: Classe do modelo já prefixado
        original_tablename: Nome original da tabela (antes do prefixo)
    """
    if plugin_name not in _prefixed_models_registry:
        _prefixed_models_registry[plugin_name] = {}
    
    # Usar nome da classe como chave
    class_name = model_class.__name__
    _prefixed_models_registry[plugin_name][class_name] = model_class
    logger.debug(f"Modelo {class_name} registrado para plugin {plugin_name} com tabela {model_class.__tablename__}")


def get_prefixed_model(plugin_name: str, model_class_name: str) -> Optional[Type]:
    """
    Obtém um modelo prefixado do registry.
    
    Args:
        plugin_name: Nome do plugin
        model_class_name: Nome da classe do modelo
        
    Returns:
        Classe do modelo prefixado ou None se não encontrado
    """
    if plugin_name in _prefixed_models_registry:
        return _prefixed_models_registry[plugin_name].get(model_class_name)
    return None


def get_all_prefixed_models(plugin_name: str) -> Dict[str, Type]:
    """
    Obtém todos os modelos prefixados de um plugin.
    
    Args:
        plugin_name: Nome do plugin
        
    Returns:
        Dicionário com nome da classe como chave e classe do modelo como valor
    """
    return _prefixed_models_registry.get(plugin_name, {})

