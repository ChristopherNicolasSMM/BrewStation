from __future__ import annotations

"""Bootstrap/migração incremental do schema do plugin.

Este arquivo precisa ser conservador: ele deve criar o que falta sem quebrar uma
instalação já existente. Evite ALTERs destrutivos.
"""

from sqlalchemy import inspect, text

from db.database import db

_initialized = False


def _existing_table_name(inspector, candidates):
    for candidate in candidates:
        if candidate and inspector.has_table(candidate):
            return candidate
    return None


def _safe_add_columns(engine, table_name: str, required_columns: dict[str, str]):
    existing = {c['name'] for c in inspect(engine).get_columns(table_name)}
    with engine.begin() as conn:
        for col_name, ddl in required_columns.items():
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {ddl}"))


def ensure_storage_schema(force: bool = False):
    global _initialized
    if _initialized and not force:
        return

    engine = db.engine

    from plugins.plugin_yeast_bank.utils.model_loader import (
        get_yeast_bank_config, get_yeast_bank_event, get_yeast_bank_item,
        get_yeast_cell_count_history, get_yeast_starter_log,
        get_yeast_storage_device, get_yeast_storage_reading, get_yeast_strain)

    # 1) Garante criação das tabelas do ambiente novo.
    models = [
        get_yeast_strain(),
        get_yeast_bank_item(),
        get_yeast_starter_log(),
        get_yeast_bank_config(),
        get_yeast_storage_device(),
        get_yeast_storage_reading(),
        get_yeast_cell_count_history(),
        get_yeast_bank_event(),
    ]
    for Model in models:
        if Model is not None:
            Model.__table__.create(bind=engine, checkfirst=True)

    inspector = inspect(engine)

    # 2) Resolve nomes reais das tabelas (podem estar prefixadas pelo host).
    def resolve(Model, fallback_suffix):
        candidates = [
            getattr(getattr(Model, '__table__', None), 'name', None) if Model else None,
            getattr(Model, '__tablename__', None) if Model else None,
            fallback_suffix,
        ]
        table = _existing_table_name(inspector, candidates)
        if table:
            return table
        for name in set(inspector.get_table_names()):
            if name.endswith(fallback_suffix):
                return name
        return None

    strain_table = resolve(get_yeast_strain(), 'yeast_strain')
    item_table = resolve(get_yeast_bank_item(), 'yeast_bank_item')
    starter_table = resolve(get_yeast_starter_log(), 'yeast_starter_log')
    device_table = resolve(get_yeast_storage_device(), 'yeast_storage_device')

    if device_table:
        _safe_add_columns(engine, device_table, {
            'machcode': 'VARCHAR(40)',
        })

    if strain_table:
        _safe_add_columns(engine, strain_table, {
            'status': "VARCHAR(30) DEFAULT 'active'",
            'viability_model': "VARCHAR(50) DEFAULT 'linear_decay_default'",
            'daily_viability_loss_pct': 'FLOAT',
            'viability_correction_factor': 'FLOAT',
            'initial_reference_viability_pct': 'FLOAT',
            'viability_floor_pct': 'FLOAT',
            'viability_notes': 'TEXT',
        })

    if item_table:
        _safe_add_columns(engine, item_table, {
            'storage_device_id': 'INTEGER',
            'storage_slot': 'VARCHAR(120)',
            'estimated_viability_pct': 'FLOAT',
            'estimated_viability_updated_at': 'DATETIME',
            'last_viability_reference_type': 'VARCHAR(30)',
            'last_viability_reference_date': 'DATE',
            'last_viability_reference_value': 'FLOAT',
            'discarded_at': 'DATETIME',
            'discard_reason': 'TEXT',
        })

    if starter_table:
        _safe_add_columns(engine, starter_table, {
            'objective': 'VARCHAR(30)',
            'result_viability_percent': 'FLOAT',
            'contamination_detected': 'BOOLEAN DEFAULT 0',
            'action_on_bank_item': 'VARCHAR(30)',
        })

    _initialized = True
