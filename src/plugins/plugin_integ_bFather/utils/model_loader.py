"""
Helper para carregar modelos prefixados do plugin.

Este módulo garante que os modelos sejam sempre carregados com os prefixos
corretos aplicados às tabelas. Use este helper em vez de importar diretamente
de model.* para garantir que os modelos prefixados sejam usados.
"""

from flask import current_app

from core.plugin_model_registry import get_prefixed_model

# Nome do plugin
PLUGIN_NAME = "plugin_integ_bFather"

# Cache de modelos já resolvidos
_model_cache = {}

# Lista de nomes de modelos disponíveis
MODEL_NAMES = [
    'Malte', 'Lupulo', 'Levedura', 'Receita', 'IngredienteReceita', 'CalculoPreco',
    'MovimentacaoEstoque', 'EstoqueIngrediente', 'CustoProducao',
    'BrewFatherRecipe', 'BrewFatherBatch', 'BrewFatherInventory', 'BrewFatherSync',
    'Envase', 'TipoEmbalagem', 'Embalagem', 'ItemEnvase',
    'CalculoEnvase', 'Configuracao', 'Dispositivo', 'SessaoBrasagem'
]


def _resolve_model(name):
    """Resolve um modelo pelo nome, com cache e fallback."""
    if name in _model_cache:
        return _model_cache[name]

    # Tentar resolver via registry de modelos prefixados
    model = get_prefixed_model(PLUGIN_NAME, name)

    # Fallback: importar diretamente dos módulos do plugin
    if model is None:
        model = _import_direct(name)

    if model is None:
        raise RuntimeError(
            f"Modelo '{name}' não encontrado. "
            f"Verifique se o plugin '{PLUGIN_NAME}' foi carregado corretamente."
        )

    _model_cache[name] = model
    return model


def _import_direct(name):
    """Tenta importar o modelo diretamente dos módulos do plugin."""
    module_map = {
        'Malte': 'model.ingredientes',
        'Lupulo': 'model.ingredientes',
        'Levedura': 'model.ingredientes',
        'Receita': 'model.ingredientes',
        'IngredienteReceita': 'model.ingredientes',
        'CalculoPreco': 'model.ingredientes',
        'MovimentacaoEstoque': 'model.estoque',
        'EstoqueIngrediente': 'model.estoque',
        'CustoProducao': 'model.estoque',
        'BrewFatherRecipe': 'model.brewfather',
        'BrewFatherBatch': 'model.brewfather',
        'BrewFatherInventory': 'model.brewfather',
        'BrewFatherSync': 'model.brewfather',
        'TipoEmbalagem': 'model.envase',
        'Embalagem': 'model.envase',
        'Envase': 'model.envase',
        'ItemEnvase': 'model.envase',
        'CalculoEnvase': 'model.calculo_envase',
        'Configuracao': 'model.config',
        'Dispositivo': 'model.dispositivos',
        'SessaoBrasagem': 'model.sessao_brasagem',
    }

    module_path = module_map.get(name)
    if not module_path:
        return None

    try:
        # Tentar importar do caminho completo do plugin primeiro
        from importlib import import_module
        full_path = f"plugins.plugin_integ_bFather.{module_path}"
        module = import_module(full_path)
        model = getattr(module, name, None)
        if model is not None:
            return model
    except (ImportError, AttributeError):
        pass

    try:
        # Fallback: importar sem prefixo do plugin
        from importlib import import_module
        module = import_module(module_path)
        model = getattr(module, name, None)
        if model is not None:
            return model
    except (ImportError, AttributeError):
        pass

    return None


def __getattr__(name):
    """
    Resolve modelos sob demanda quando importados via:
        from ...model_loader import Malte

    Retorna a classe real do modelo (não um proxy),
    resolvendo do registry de modelos prefixados ou via fallback.
    """
    if name.startswith('_') or name not in MODEL_NAMES:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    return _resolve_model(name)


def __dir__():
    """Lista os modelos disponíveis como atributos do módulo."""
    return sorted(MODEL_NAMES)
