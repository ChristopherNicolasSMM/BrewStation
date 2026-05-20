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


def _get_prefixed_model(model_class_name: str):
    """
    Obtém um modelo prefixado do registry.
    
    Args:
        model_class_name: Nome da classe do modelo (ex: 'BrewFatherRecipe')
        
    Returns:
        Classe do modelo prefixado ou None se não encontrado
    """
    prefixed_model = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed_model:
        return prefixed_model
    
    # Fallback: importar diretamente do plugin e aplicar prefixo se necessário
    try:
        from plugins.plugin_integ_bFather.model.brewfather import (
            BrewFatherBatch, BrewFatherInventory, BrewFatherRecipe,
            BrewFatherSync)
        from plugins.plugin_integ_bFather.model.calculo_envase import \
            CalculoEnvase
        from plugins.plugin_integ_bFather.model.config import Configuracao
        from plugins.plugin_integ_bFather.model.dispositivos import Dispositivo
        from plugins.plugin_integ_bFather.model.envase import (Embalagem,
                                                               Envase,
                                                               ItemEnvase,
                                                               TipoEmbalagem)
        from plugins.plugin_integ_bFather.model.estoque import (
            CustoProducao, EstoqueIngrediente, MovimentacaoEstoque)
        from plugins.plugin_integ_bFather.model.ingredientes import (
            CalculoPreco, IngredienteReceita, Levedura, Lupulo, Malte, Receita)
        from plugins.plugin_integ_bFather.model.sessao_brasagem import \
            SessaoBrasagem
        
        model_map = {
            # Ingredientes
            'Malte': Malte,
            'Lupulo': Lupulo,
            'Levedura': Levedura,
            'Receita': Receita,
            'IngredienteReceita': IngredienteReceita,
            'CalculoPreco': CalculoPreco,
            # Estoque
            'MovimentacaoEstoque': MovimentacaoEstoque,
            'EstoqueIngrediente': EstoqueIngrediente,
            'CustoProducao': CustoProducao,
            # BrewFather
            'BrewFatherRecipe': BrewFatherRecipe,
            'BrewFatherBatch': BrewFatherBatch,
            'BrewFatherInventory': BrewFatherInventory,
            'BrewFatherSync': BrewFatherSync,
            # Envase
            'Envase': Envase,
            'TipoEmbalagem': TipoEmbalagem,
            'Embalagem': Embalagem,
            'ItemEnvase': ItemEnvase,
            # Outros
            'CalculoEnvase': CalculoEnvase,
            'Configuracao': Configuracao,
            'Dispositivo': Dispositivo,
            'SessaoBrasagem': SessaoBrasagem,
        }
        
        model = model_map.get(model_class_name)
        if model and hasattr(current_app, 'plugin_manager'):
            # Verificar se o prefixo já foi aplicado
            tablename = getattr(model, '__tablename__', None)
            if tablename and not tablename.startswith('plugin_integ_bFather_'):
                # Aplicar prefixo se ainda não foi aplicado
                from core.plugin_db_helper import prefix_table_name
                plugin = current_app.plugin_manager.get_plugin(PLUGIN_NAME)
                if plugin:
                    plugin_dir_name = plugin.plugin_path.name if hasattr(plugin, 'plugin_path') and plugin.plugin_path else plugin.name
                    plugin_name_for_prefix = plugin_dir_name if plugin_dir_name else plugin.name
                    return prefix_table_name(model, plugin_name_for_prefix, plugin.table_prefix)
        
        return model
    except ImportError:
        # Fallback final: tentar importar de model.* (shims)
        try:
            from model.brewfather import (BrewFatherBatch, BrewFatherInventory,
                                          BrewFatherRecipe, BrewFatherSync)
            from model.calculo_envase import CalculoEnvase
            from model.config import Configuracao
            from model.dispositivos import Dispositivo
            from model.envase import Embalagem, Envase, TipoEmbalagem
            from model.estoque import (CustoProducao, EstoqueIngrediente,
                                       MovimentacaoEstoque)
            from model.ingredientes import (CalculoPreco, IngredienteReceita,
                                            Levedura, Lupulo, Malte, Receita)
            from model.sessao_brasagem import SessaoBrasagem
            
            model_map = {
                'Malte': Malte, 'Lupulo': Lupulo, 'Levedura': Levedura,
                'Receita': Receita, 'IngredienteReceita': IngredienteReceita, 'CalculoPreco': CalculoPreco,
                'MovimentacaoEstoque': MovimentacaoEstoque, 'EstoqueIngrediente': EstoqueIngrediente, 'CustoProducao': CustoProducao,
                'BrewFatherRecipe': BrewFatherRecipe, 'BrewFatherBatch': BrewFatherBatch,
                'BrewFatherInventory': BrewFatherInventory, 'BrewFatherSync': BrewFatherSync,
                'Envase': Envase, 'TipoEmbalagem': TipoEmbalagem, 'Embalagem': Embalagem, 'ItemEnvase': ItemEnvase,
                'CalculoEnvase': CalculoEnvase, 'Configuracao': Configuracao,
                'Dispositivo': Dispositivo, 'SessaoBrasagem': SessaoBrasagem,
            }
            return model_map.get(model_class_name)
        except ImportError:
            return None


# Exportar modelos diretamente para facilitar uso nas rotas
def get_models():
    """
    Retorna um dicionário com todos os modelos prefixados do plugin.
    Use este método para obter todos os modelos de uma vez.
    """
    model_names = [
        'Malte', 'Lupulo', 'Levedura', 'Receita', 'IngredienteReceita', 'CalculoPreco',
        'MovimentacaoEstoque', 'EstoqueIngrediente', 'CustoProducao',
        'BrewFatherRecipe', 'BrewFatherBatch', 'BrewFatherInventory', 'BrewFatherSync',
        'Envase', 'TipoEmbalagem', 'Embalagem', 'ItemEnvase',
        'CalculoEnvase', 'Configuracao', 'Dispositivo', 'SessaoBrasagem'
    ]
    
    return {name: _get_prefixed_model(name) for name in model_names}


# Funções helper para obter modelos prefixados
# Estas funções garantem que sempre retornem o modelo prefixado correto
def get_brewfather_recipe():
    """Obtém o modelo BrewFatherRecipe prefixado"""
    return _get_prefixed_model('BrewFatherRecipe') or _get_fallback_model('BrewFatherRecipe')

def get_brewfather_batch():
    """Obtém o modelo BrewFatherBatch prefixado"""
    return _get_prefixed_model('BrewFatherBatch') or _get_fallback_model('BrewFatherBatch')

def get_brewfather_inventory():
    """Obtém o modelo BrewFatherInventory prefixado"""
    return _get_prefixed_model('BrewFatherInventory') or _get_fallback_model('BrewFatherInventory')

def get_brewfather_sync():
    """Obtém o modelo BrewFatherSync prefixado"""
    return _get_prefixed_model('BrewFatherSync') or _get_fallback_model('BrewFatherSync')

def _get_fallback_model(model_class_name):
    """Fallback: importar diretamente do plugin"""
    try:
        from plugins.plugin_integ_bFather.model.brewfather import (
            BrewFatherBatch, BrewFatherInventory, BrewFatherRecipe,
            BrewFatherSync)
        model_map = {
            'BrewFatherRecipe': BrewFatherRecipe,
            'BrewFatherBatch': BrewFatherBatch,
            'BrewFatherInventory': BrewFatherInventory,
            'BrewFatherSync': BrewFatherSync,
        }
        return model_map.get(model_class_name)
    except ImportError:
        return None

# Importar modelos diretamente para uso nas rotas
# IMPORTANTE: Estes imports são feitos dinamicamente quando o módulo é importado
# mas podem não ter o prefixo aplicado ainda. Use as funções get_*() acima ou
# importe diretamente das rotas usando get_brewfather_recipe(), etc.

# Importar modelos base (serão prefixados quando o plugin for carregado)

# NOTA: Os modelos acima serão prefixados pelo plugin_manager quando o plugin for carregado.
# As rotas devem usar estes imports, que já estarão prefixados quando as rotas forem executadas.
