"""
Helper para adicionar imports necessários nos arquivos de rotas do plugin.
Este arquivo será usado para garantir que os imports funcionem corretamente.
"""
import sys
from pathlib import Path


def setup_plugin_imports():
    """Configura os imports para o plugin"""
    src_path = Path(__file__).parent.parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

