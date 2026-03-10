from sqlalchemy import inspect, text
from db.database import db

_initialized = False


def _existing_table_name(inspector, candidates):
    for candidate in candidates:
        if candidate and inspector.has_table(candidate):
            return candidate
    return None


def ensure_storage_schema(force: bool = False):
    global _initialized
    if _initialized and not force:
        return

    engine = db.engine

    from plugins.plugin_yeast_bank.utils.model_loader import (
        get_yeast_storage_device,
        get_yeast_storage_reading,
        get_yeast_bank_item,
    )

    Device = get_yeast_storage_device()
    Reading = get_yeast_storage_reading()
    Item = get_yeast_bank_item()

    if Device is not None:
        Device.__table__.create(bind=engine, checkfirst=True)
    if Reading is not None:
        Reading.__table__.create(bind=engine, checkfirst=True)

    inspector = inspect(engine)

    # add machcode to existing storage tables when needed
    device_table = None
    if Device is not None:
        device_candidates = [
            getattr(getattr(Device, '__table__', None), 'name', None),
            getattr(Device, '__tablename__', None),
            'yeastbk_yeast_storage_device',
            'yeast_storage_device',
        ]
        device_table = _existing_table_name(inspector, device_candidates)
        if not device_table:
            for name in set(inspector.get_table_names()):
                if name.endswith('yeast_storage_device'):
                    device_table = name
                    break
        if device_table:
            dcols = {c['name'] for c in inspect(engine).get_columns(device_table)}
            if 'machcode' not in dcols:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {device_table} ADD COLUMN machcode VARCHAR(40)"))

    item_table = None
    if Item is not None:
        candidates = [
            getattr(getattr(Item, '__table__', None), 'name', None),
            getattr(Item, '__tablename__', None),
            'yeastbk_yeast_bank_item',
            'yeast_bank_item',
        ]
        item_table = _existing_table_name(inspector, candidates)

        if not item_table:
            all_tables = set(inspector.get_table_names())
            for name in all_tables:
                if name.endswith('yeast_bank_item'):
                    item_table = name
                    break

    if item_table:
        cols = {c['name'] for c in inspect(engine).get_columns(item_table)}
        stmts = []
        if 'storage_device_id' not in cols:
            stmts.append(f"ALTER TABLE {item_table} ADD COLUMN storage_device_id INTEGER")
        if 'storage_slot' not in cols:
            stmts.append(f"ALTER TABLE {item_table} ADD COLUMN storage_slot VARCHAR(120)")
        if stmts:
            with engine.begin() as conn:
                for stmt in stmts:
                    conn.execute(text(stmt))

        cols_after = {c['name'] for c in inspect(engine).get_columns(item_table)}
        if 'storage_device_id' in cols_after and 'storage_slot' in cols_after:
            _initialized = True
            return

    # ainda deixa inicializado se a tabela não existir (ambiente novo)
    _initialized = True
