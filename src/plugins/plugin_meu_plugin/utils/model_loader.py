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
PLUGIN_NAME = "plugin_meu_plugin"


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
    # Adicione seus modelos aqui quando criar
    try:
        # Exemplo (descomente e ajuste quando criar modelos):
        # from plugins.plugin_meu_plugin.model.meu_modelo import MeuModelo
        # model_map = {'MeuModelo': MeuModelo}
        # return model_map.get(model_class_name)
        pass
    except ImportError:
        pass
    
    return None


# Funções helper para obter modelos específicos
# Adicione funções aqui quando criar modelos:
# def get_meu_modelo():
#     """Obtém o modelo MeuModelo prefixado"""
#     return _get_prefixed_model('MeuModelo')


# Exportar modelos diretamente para uso nas rotas
# NOTA: Os modelos abaixo serão prefixados pelo plugin_manager quando o plugin for carregado.
# Adicione imports aqui quando criar modelos:
# from plugins.plugin_meu_plugin.model.meu_modelo import MeuModelo
