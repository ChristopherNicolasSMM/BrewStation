from sqlalchemy import inspect, text
from db.database import db

_initialized = False


def _existing_table_name(inspector, candidates):
    for candidate in candidates:
        if candidate and inspector.has_table(candidate):
            return candidate
    return None


def _find_table(inspector, model, suffix):
    candidates = [
        getattr(getattr(model, '__table__', None), 'name', None),
        getattr(model, '__tablename__', None),
        suffix,
    ]
    table = _existing_table_name(inspector, candidates)
    if table:
        return table
    for name in set(inspector.get_table_names()):
        if name.endswith(suffix):
            return name
    return None


def _ensure_columns(engine, table_name, desired_columns):
    existing = {c['name'] for c in inspect(engine).get_columns(table_name)}
    stmts = []
    for col_name, ddl in desired_columns.items():
        if col_name not in existing:
            stmts.append(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {ddl}")
    if stmts:
        with engine.begin() as conn:
            for stmt in stmts:
                conn.execute(text(stmt))


def ensure_storage_schema(force: bool = False):
    """
    Bootstrap de esquema incremental.

    Esta função cria tabelas novas e adiciona colunas faltantes sem exigir uma
    migration externa. É intencionalmente conservadora: só adiciona o que estiver
    ausente, para reduzir risco em ambientes já em produção.
    """
    global _initialized
    if _initialized and not force:
        return

    engine = db.engine

    from plugins.plugin_yeast_bank.utils.model_loader import (
        get_yeast_storage_device,
        get_yeast_storage_reading,
        get_yeast_bank_item,
        get_yeast_strain,
        get_yeast_starter_log,
        get_yeast_count_history,
    )

    Device = get_yeast_storage_device()
    Reading = get_yeast_storage_reading()
    Item = get_yeast_bank_item()
    Strain = get_yeast_strain()
    Starter = get_yeast_starter_log()
    CountHistory = get_yeast_count_history()

    for model in (Device, Reading, Item, Strain, Starter, CountHistory):
        if model is not None:
            model.__table__.create(bind=engine, checkfirst=True)

    inspector = inspect(engine)

    if Device is not None:
        device_table = _find_table(inspector, Device, 'yeast_storage_device')
        if device_table:
            _ensure_columns(engine, device_table, {
                'machcode': 'VARCHAR(40)',
            })

    if Strain is not None:
        strain_table = _find_table(inspector, Strain, 'yeast_strain')
        if strain_table:
            _ensure_columns(engine, strain_table, {
                'viability_model': 'VARCHAR(50)',
                'daily_viability_loss_pct': 'FLOAT',
                'viability_correction_factor': 'FLOAT',
                'initial_reference_viability_pct': 'FLOAT',
                'viability_floor_pct': 'FLOAT',
                'status': "VARCHAR(20) DEFAULT 'active'",
            })

    if Item is not None:
        item_table = _find_table(inspector, Item, 'yeast_bank_item')
        if item_table:
            _ensure_columns(engine, item_table, {
                'storage_device_id': 'INTEGER',
                'storage_slot': 'VARCHAR(120)',
                'estimated_viability_pct': 'FLOAT',
                'estimated_viability_updated_at': 'DATETIME',
                'last_viability_reference_type': 'VARCHAR(30)',
                'last_viability_reference_date': 'DATE',
                'last_viability_reference_value': 'FLOAT',
            })

    if Starter is not None:
        starter_table = _find_table(inspector, Starter, 'yeast_starter_log')
        if starter_table:
            _ensure_columns(engine, starter_table, {
                'objective': 'VARCHAR(30)',
                'contamination_detected': 'BOOLEAN DEFAULT 0',
                'result_action': 'VARCHAR(30)',
            })

    _initialized = True
