"""
Helper para gerenciar nomes de tabelas de modelos de plugins.

Este módulo fornece utilitários para aplicar prefixos configuráveis aos nomes
de tabelas dos modelos SQLAlchemy de plugins, permitindo isolamento e organização.
"""

from typing import List, Optional, Type
from sqlalchemy.ext.declarative import DeclarativeMeta
import logging

logger = logging.getLogger(__name__)


def prefix_table_name(model_class: Type, plugin_name: str, table_prefix: Optional[str] = None) -> Type:
    """
    Aplica prefixo ao nome da tabela de um modelo.
    
    Se o modelo já tem um __tablename__ definido, adiciona o prefixo.
    Se não tem, gera um nome baseado no nome da classe com o prefixo.
    
    Args:
        model_class: Classe do modelo SQLAlchemy
        plugin_name: Nome do plugin (usado como fallback se table_prefix não for fornecido)
        table_prefix: Prefixo customizado (opcional). Se None, usa f"{plugin_name}_"
        
    Returns:
        A mesma classe com __tablename__ modificado
    """
    if not isinstance(model_class, type) or not hasattr(model_class, '__tablename__'):
        logger.warning(f"Classe {model_class} não parece ser um modelo SQLAlchemy válido")
        return model_class
    
    # Determinar prefixo
    if table_prefix is None:
        prefix = f"{plugin_name}_"
    else:
        prefix = table_prefix if table_prefix.endswith('_') else f"{table_prefix}_"
    
    # Obter nome atual da tabela
    current_tablename = getattr(model_class, '__tablename__', None)
    
    if current_tablename:
        # Se já tem prefixo do plugin, não adicionar novamente
        if current_tablename.startswith(prefix):
            logger.debug(f"Tabela {current_tablename} já tem prefixo {prefix}, mantendo como está")
            return model_class
        
        # Aplicar prefixo
        new_tablename = f"{prefix}{current_tablename}"
    else:
        # Gerar nome baseado no nome da classe
        class_name = model_class.__name__
        # Converter CamelCase para snake_case
        import re
        snake_case = re.sub('([A-Z])', r'_\1', class_name).lower().lstrip('_')
        new_tablename = f"{prefix}{snake_case}"
    
    # Modificar o __tablename__ da classe de forma permanente
    # Usar setattr para garantir que a modificação seja persistida
    setattr(model_class, '__tablename__', new_tablename)
    
    # Atualizar o objeto Table se já foi criado
    # NOTA: Não podemos modificar db.metadata.tables diretamente (é imutável no Flask-SQLAlchemy)
    # Apenas modificamos o __tablename__ e o nome do Table, o SQLAlchemy gerencia o metadata
    try:
        # Se o objeto Table já foi criado, atualizar seu nome
        if hasattr(model_class, '__table__') and model_class.__table__ is not None:
            # Atualizar o nome da tabela no objeto Table
            model_class.__table__.name = new_tablename
            logger.debug(f"Nome da tabela atualizado no objeto Table: {new_tablename}")
    except Exception as e:
        # Se houver erro, apenas logar - o __tablename__ já está correto
        logger.debug(f"Erro ao atualizar objeto Table (pode ser normal se ainda não foi criado): {e}")
    
    logger.debug(f"Prefixo aplicado: {current_tablename or 'N/A'} -> {new_tablename}")
    
    return model_class


def prefix_models(models: List[Type], plugin_name: str, table_prefix: Optional[str] = None) -> List[Type]:
    """
    Aplica prefixo a uma lista de modelos e registra no registry.
    
    Args:
        models: Lista de classes de modelos SQLAlchemy
        plugin_name: Nome do plugin
        table_prefix: Prefixo customizado (opcional)
        
    Returns:
        Lista de modelos com prefixos aplicados
    """
    from .plugin_model_registry import register_prefixed_model
    
    prefixed_models = []
    
    for model in models:
        try:
            # Obter nome original da tabela antes de aplicar prefixo
            original_tablename = getattr(model, '__tablename__', None)
            
            # Aplicar prefixo
            prefixed_model = prefix_table_name(model, plugin_name, table_prefix)
            prefixed_models.append(prefixed_model)
            
            # Registrar no registry para uso posterior
            if original_tablename:
                register_prefixed_model(plugin_name, prefixed_model, original_tablename)
        except Exception as e:
            logger.error(f"Erro ao aplicar prefixo ao modelo {model}: {e}")
            # Adicionar mesmo assim para não quebrar o fluxo
            prefixed_models.append(model)
    
    return prefixed_models


def update_foreign_keys(model_class: Type, old_tablename: str, new_tablename: str):
    """
    Atualiza referências de ForeignKey que apontam para tabelas que mudaram de nome.
    
    Nota: Esta função é uma tentativa de atualizar ForeignKeys, mas pode não ser
    completamente confiável devido à complexidade do SQLAlchemy. É recomendado
    que os desenvolvedores de plugins definam ForeignKeys usando strings com o
    prefixo correto.
    
    Args:
        model_class: Classe do modelo
        old_tablename: Nome antigo da tabela
        new_tablename: Nome novo da tabela
    """
    # Esta é uma implementação básica
    # ForeignKeys são complexas e podem referenciar outras tabelas
    # Por enquanto, apenas logamos a mudança
    logger.debug(f"Tabela {old_tablename} renomeada para {new_tablename}")
    logger.info("Nota: Verifique manualmente se há ForeignKeys que precisam ser atualizadas")

