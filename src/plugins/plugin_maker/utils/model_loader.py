"""Model loader do Maker.

O BrewStation prefixa tabelas de plugins. Para evitar problemas, as rotas devem
pegar os modelos via registry/prefixo, usando get_prefixed_model().
"""

from core.plugin_model_registry import get_prefixed_model

PLUGIN_NAME = "maker"

def _get(name: str):
    return get_prefixed_model(PLUGIN_NAME, name)

def get_maker_project(): return _get("MakerProject")
def get_maker_table(): return _get("MakerTable")
def get_maker_column(): return _get("MakerColumn")
def get_maker_relation(): return _get("MakerRelation")

def get_maker_screen(): return _get("MakerScreen")
def get_maker_tab_group(): return _get("MakerTabGroup")
def get_maker_tab(): return _get("MakerTab")
def get_maker_section(): return _get("MakerSection")
def get_maker_field_placement(): return _get("MakerFieldPlacement")

def get_maker_computed_field(): return _get("MakerComputedField")

def get_maker_grid_view(): return _get("MakerGridView")
def get_maker_grid_column(): return _get("MakerGridColumn")
def get_maker_grid_agg(): return _get("MakerGridAggregation")
def get_maker_grid_variant(): return _get("MakerGridVariant")

def get_maker_generation_run(): return _get("MakerGenerationRun")