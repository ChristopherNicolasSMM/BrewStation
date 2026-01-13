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
    
    Também atualiza ForeignKeys que referenciam outras tabelas do mesmo plugin
    para garantir que apontem para as tabelas prefixadas corretas.
    
    Args:
        models: Lista de classes de modelos SQLAlchemy
        plugin_name: Nome do plugin
        table_prefix: Prefixo customizado (opcional)
        
    Returns:
        Lista de modelos com prefixos aplicados
    """
    from .plugin_model_registry import register_prefixed_model
    from sqlalchemy import ForeignKey
    
    # Determinar prefixo
    if table_prefix is None:
        prefix = f"{plugin_name}_"
    else:
        prefix = table_prefix if table_prefix.endswith('_') else f"{table_prefix}_"
    
    # Primeiro, aplicar prefixos e criar um mapa de nomes antigos -> novos
    name_map = {}
    prefixed_models = []
    
    for model in models:
        try:
            # Obter nome original da tabela antes de aplicar prefixo
            original_tablename = getattr(model, '__tablename__', None)
            
            # Aplicar prefixo
            prefixed_model = prefix_table_name(model, plugin_name, table_prefix)
            prefixed_models.append(prefixed_model)
            
            # Mapear nome antigo -> novo
            if original_tablename:
                new_tablename = getattr(prefixed_model, '__tablename__', None)
                if new_tablename:
                    name_map[original_tablename] = new_tablename
                    register_prefixed_model(plugin_name, prefixed_model, original_tablename)
        except Exception as e:
            logger.error(f"Erro ao aplicar prefixo ao modelo {model}: {e}")
            # Adicionar mesmo assim para não quebrar o fluxo
            prefixed_models.append(model)
    
    # Atualizar ForeignKeys que referenciam outras tabelas do mesmo plugin
    # Isso é necessário porque as ForeignKeys podem estar usando nomes sem prefixo
    # Percorrer todos os modelos e atualizar ForeignKeys nas definições das colunas
    # antes que o SQLAlchemy crie o __table__
    for model in prefixed_models:
        try:
            # Percorrer todos os atributos da classe do modelo
            for attr_name in dir(model):
                # Ignorar atributos privados e métodos
                if attr_name.startswith('_'):
                    continue
                
                try:
                    attr = getattr(model, attr_name)
                    
                    # Verificar se é uma Column do SQLAlchemy
                    from sqlalchemy import Column
                    if isinstance(attr, Column):
                        # Verificar se a coluna tem ForeignKey definida
                        if hasattr(attr, 'foreign_keys') and attr.foreign_keys:
                            # Atualizar ForeignKeys
                            for fk in list(attr.foreign_keys):
                                # Tentar obter o nome da tabela referenciada do argumento da ForeignKey
                                fk_target = None
                                fk_col_name = 'id'
                                
                                try:
                                    # Tentar obter do _colspec (argumento original da ForeignKey)
                                    if hasattr(fk, '_colspec'):
                                        fk_spec = fk._colspec
                                        if isinstance(fk_spec, str) and '.' in fk_spec:
                                            parts = fk_spec.split('.')
                                            fk_target = parts[0]
                                            fk_col_name = parts[1] if len(parts) > 1 else 'id'
                                except Exception:
                                    pass
                                
                                # Se encontrou a tabela referenciada e ela está no name_map, atualizar
                                if fk_target and fk_target in name_map:
                                    new_tablename = name_map[fk_target]
                                    
                                    # Criar nova ForeignKey com nome prefixado
                                    new_fk = ForeignKey(f"{new_tablename}.{fk_col_name}")
                                    
                                    # Remover ForeignKey antiga e adicionar nova
                                    attr.foreign_keys.discard(fk)
                                    attr.foreign_keys.add(new_fk)
                                    logger.debug(f"ForeignKey atualizada em {model.__name__}.{attr_name}: {fk_target} -> {new_tablename}")
                except Exception as e:
                    # Ignorar erros ao acessar atributos
                    pass
        except Exception as e:
            logger.debug(f"Erro ao atualizar ForeignKeys do modelo {model.__name__}: {e}")
            # Continuar com outros modelos mesmo se houver erro
    
    return prefixed_models


def update_foreign_keys(model_class: Type, old_tablename: str, new_tablename: str):
    """
    Atualiza referências de ForeignKey que apontam para tabelas que mudaram de nome.
    
    Args:
        model_class: Classe do modelo
        old_tablename: Nome antigo da tabela
        new_tablename: Nome novo da tabela
    """
    from sqlalchemy import ForeignKey
    
    # Atualizar ForeignKeys nas colunas do modelo
    for column in model_class.__table__.columns:
        if hasattr(column, 'foreign_keys') and column.foreign_keys:
            for fk in column.foreign_keys:
                # Se a ForeignKey referencia a tabela antiga, atualizar
                if fk.column.table.name == old_tablename:
                    # Criar nova ForeignKey com o nome correto
                    fk_col_name = fk.column.name
                    new_fk = ForeignKey(f"{new_tablename}.{fk_col_name}")
                    # Substituir a ForeignKey na coluna
                    column.foreign_keys.clear()
                    column.foreign_keys.add(new_fk)
                    logger.debug(f"ForeignKey atualizada: {old_tablename}.{fk_col_name} -> {new_tablename}.{fk_col_name}")
    
    logger.debug(f"Tabela {old_tablename} renomeada para {new_tablename}")

