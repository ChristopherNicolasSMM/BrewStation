from flask import Blueprint, request, jsonify, Response
from flask_login import login_required
from db.database import db
from datetime import date, timedelta, datetime
import csv
import io

from plugins.plugin_yeast_bank.utils.model_loader import (
    get_yeast_strain,
    get_yeast_bank_item,
    get_yeast_starter_log,
    get_yeast_bank_config,
    get_yeast_storage_device,
    get_yeast_storage_reading,
)
from plugins.plugin_yeast_bank.utils.schema import ensure_storage_schema

yeast_bank_bp = Blueprint("yeast_bank", __name__)


@yeast_bank_bp.before_request
def _bootstrap_schema():
    ensure_storage_schema()


def _json_error(msg, status=400):
    return jsonify({"ok": False, "error": msg}), status


def _parse_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _parse_datetime(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


DEFAULT_CONFIG = {
    "expiry_master_days": 365,
    "expiry_work_days": 180,
    "expiry_plate_days": 30,
    "expiry_saline_days": 90,
}


def _merge_config(db_cfg: dict | None):
    cfg = DEFAULT_CONFIG.copy()
    if db_cfg:
        for k in cfg.keys():
            v = db_cfg.get(k)
            if isinstance(v, int) and v > 0:
                cfg[k] = v
    return cfg


EXPIRY_RULES_DAYS = {
    "slant_master_a": 365,
    "slant_master_b": 365,
    "slant_work": 180,
    "plate": 30,
    "saline": 90,
}


# -------------------------
# Strains
# -------------------------
@yeast_bank_bp.get("/strains")
@login_required
def list_strains():
    YeastStrain = get_yeast_strain()
    strains = YeastStrain.query.order_by(YeastStrain.created_at.desc()).all()
    return jsonify({"ok": True, "items": [s.to_dict() for s in strains]})


@yeast_bank_bp.post("/strains")
@login_required
def create_strain():
    YeastStrain = get_yeast_strain()
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _json_error("Campo 'name' é obrigatório")

    strain = YeastStrain(
        code=(data.get("code") or None),
        name=name,
        family=(data.get("family") or None),
        supplier=(data.get("supplier") or None),
        notes=(data.get("notes") or None),
    )
    db.session.add(strain)
    db.session.commit()
    return jsonify({"ok": True, "item": strain.to_dict()})


@yeast_bank_bp.put("/strains/<int:strain_id>")
@login_required
def update_strain(strain_id: int):
    YeastStrain = get_yeast_strain()
    strain = YeastStrain.query.get(strain_id)
    if not strain:
        return _json_error("Cepa não encontrada", 404)

    data = request.get_json(force=True, silent=True) or {}
    for field in ("code", "name", "family", "supplier", "notes"):
        if field in data:
            setattr(strain, field, data.get(field))
    db.session.commit()
    return jsonify({"ok": True, "item": strain.to_dict()})


@yeast_bank_bp.delete("/strains/<int:strain_id>")
@login_required
def delete_strain(strain_id: int):
    YeastStrain = get_yeast_strain()
    YeastBankItem = get_yeast_bank_item()
    strain = YeastStrain.query.get(strain_id)
    if not strain:
        return _json_error("Cepa não encontrada", 404)
    if YeastBankItem.query.filter_by(strain_id=strain_id).count() > 0:
        return _json_error("Não é possível excluir: existem itens do banco vinculados a esta cepa", 409)
    db.session.delete(strain)
    db.session.commit()
    return jsonify({"ok": True})


# -------------------------
# Storage devices
# -------------------------
@yeast_bank_bp.get("/storage/devices")
@login_required
def list_storage_devices():
    Device = get_yeast_storage_device()
    devices = Device.query.order_by(Device.is_active.desc(), Device.name.asc()).all()
    return jsonify({"ok": True, "items": [d.to_dict() for d in devices]})


@yeast_bank_bp.post("/storage/devices")
@login_required
def create_storage_device():
    Device = get_yeast_storage_device()
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _json_error("name é obrigatório")
    device = Device(
        name=name,
        device_type=(data.get("device_type") or "freezer").strip(),
        status=(data.get("status") or "active").strip(),
        description=data.get("description"),
        brand=data.get("brand"),
        model=data.get("model"),
        serial_number=data.get("serial_number"),
        physical_location=data.get("physical_location"),
        virtual_address=data.get("virtual_address"),
        target_temperature_c=data.get("target_temperature_c"),
        temperature_min_c=data.get("temperature_min_c"),
        temperature_max_c=data.get("temperature_max_c"),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(device)
    db.session.commit()
    return jsonify({"ok": True, "item": device.to_dict()})


@yeast_bank_bp.put("/storage/devices/<int:device_id>")
@login_required
def update_storage_device(device_id: int):
    Device = get_yeast_storage_device()
    device = Device.query.get(device_id)
    if not device:
        return _json_error("Equipamento não encontrado", 404)
    data = request.get_json(force=True, silent=True) or {}
    for field in (
        "name", "device_type", "status", "description", "brand", "model", "serial_number",
        "physical_location", "virtual_address", "target_temperature_c", "temperature_min_c", "temperature_max_c"
    ):
        if field in data:
            setattr(device, field, data.get(field))
    if "is_active" in data:
        device.is_active = bool(data.get("is_active"))
    device.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True, "item": device.to_dict()})


@yeast_bank_bp.delete("/storage/devices/<int:device_id>")
@login_required
def deactivate_storage_device(device_id: int):
    Device = get_yeast_storage_device()
    device = Device.query.get(device_id)
    if not device:
        return _json_error("Equipamento não encontrado", 404)
    device.is_active = False
    device.status = "inactive"
    device.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True, "item": device.to_dict()})


@yeast_bank_bp.get("/storage/devices/<int:device_id>/readings")
@login_required
def list_storage_readings(device_id: int):
    Device = get_yeast_storage_device()
    Reading = get_yeast_storage_reading()
    device = Device.query.get(device_id)
    if not device:
        return _json_error("Equipamento não encontrado", 404)
    limit = min(max(int(request.args.get("limit", 50)), 1), 500)
    items = Reading.query.filter_by(device_id=device_id).order_by(Reading.recorded_at.desc()).limit(limit).all()
    return jsonify({"ok": True, "device": device.to_dict(), "items": [r.to_dict() for r in reversed(items)]})


@yeast_bank_bp.get("/storage/devices/<int:device_id>/items")
@login_required
def list_device_items(device_id: int):
    Device = get_yeast_storage_device()
    Item = get_yeast_bank_item()
    device = Device.query.get(device_id)
    if not device:
        return _json_error("Equipamento não encontrado", 404)
    items = Item.query.filter_by(storage_device_id=device_id).order_by(Item.created_at.desc()).all()
    return jsonify({"ok": True, "device": device.to_dict(), "items": [i.to_dict() for i in items]})


@yeast_bank_bp.post("/storage/readings")
@login_required
def create_storage_reading():
    Device = get_yeast_storage_device()
    Reading = get_yeast_storage_reading()
    data = request.get_json(force=True, silent=True) or {}
    device_id = data.get("device_id")
    device = Device.query.get(device_id) if device_id else None
    if not device:
        return _json_error("device_id inválido")
    try:
        temperature_c = float(data.get("temperature_c"))
    except Exception:
        return _json_error("temperature_c inválido")
    reading = Reading(
        device_id=device_id,
        recorded_at=_parse_datetime(data.get("recorded_at")) or datetime.utcnow(),
        temperature_c=temperature_c,
        humidity_percent=data.get("humidity_percent"),
        source_type=(data.get("source_type") or "manual").strip(),
        source_ref=data.get("source_ref"),
        notes=data.get("notes"),
    )
    db.session.add(reading)
    device.current_temperature_c = reading.temperature_c
    device.last_temperature_at = reading.recorded_at
    if device.is_active and device.status == "inactive":
        device.status = "active"
    device.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True, "item": reading.to_dict(), "device": device.to_dict()})


# -------------------------
# Bank Items
# -------------------------
@yeast_bank_bp.get("/items")
@login_required

def list_bank_items():
    Item = get_yeast_bank_item()
    items = Item.query.order_by(Item.created_at.desc()).all()
    return jsonify({"ok": True, "items": [i.to_dict() for i in items]})


@yeast_bank_bp.post("/items")
@login_required
def create_bank_item():
    Item = get_yeast_bank_item()
    Strain = get_yeast_strain()
    Device = get_yeast_storage_device()
    data = request.get_json(force=True, silent=True) or {}

    strain_id = data.get("strain_id")
    if not strain_id or not Strain.query.get(strain_id):
        return _json_error("strain_id inválido")
    storage_type = (data.get("storage_type") or "").strip()
    if not storage_type:
        return _json_error("storage_type é obrigatório")

    device_id = data.get("storage_device_id")
    if device_id and not Device.query.get(device_id):
        return _json_error("storage_device_id inválido")

    cfg_row = get_yeast_bank_config().query.order_by(get_yeast_bank_config().id.desc()).first()
    merged_cfg = _merge_config(cfg_row.to_dict() if cfg_row else {})
    prepared = _parse_date(data.get("prepared_date"))
    expiry = _parse_date(data.get("expiry_date"))
    if expiry is None and prepared is not None:
        st = storage_type
        if st in ("slant_master_a", "slant_master_b"):
            days = merged_cfg["expiry_master_days"]
        elif st == "slant_work":
            days = merged_cfg["expiry_work_days"]
        elif st == "plate":
            days = merged_cfg["expiry_plate_days"]
        elif st == "saline":
            days = merged_cfg["expiry_saline_days"]
        else:
            days = None
        if days:
            expiry = prepared + timedelta(days=days)

    item = Item(
        strain_id=strain_id,
        storage_type=storage_type,
        location=data.get("location"),
        storage_device_id=device_id,
        storage_slot=data.get("storage_slot"),
        label=data.get("label"),
        prepared_date=prepared,
        expiry_date=expiry,
        status=data.get("status") or "ok",
        last_checked=_parse_date(data.get("last_checked")),
        viability_notes=data.get("viability_notes"),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"ok": True, "item": item.to_dict()})


@yeast_bank_bp.put("/items/<int:item_id>")
@login_required
def update_bank_item(item_id: int):
    Item = get_yeast_bank_item()
    Device = get_yeast_storage_device()
    item = Item.query.get(item_id)
    if not item:
        return _json_error("Item não encontrado", 404)
    data = request.get_json(force=True, silent=True) or {}
    if "storage_device_id" in data:
        device_id = data.get("storage_device_id")
        if device_id and not Device.query.get(device_id):
            return _json_error("storage_device_id inválido")
        item.storage_device_id = device_id
    for field in ("storage_type", "location", "storage_slot", "label", "status", "viability_notes"):
        if field in data:
            setattr(item, field, data.get(field))
    if "prepared_date" in data:
        item.prepared_date = _parse_date(data.get("prepared_date"))
    if "expiry_date" in data:
        item.expiry_date = _parse_date(data.get("expiry_date"))
    if "last_checked" in data:
        item.last_checked = _parse_date(data.get("last_checked"))
    db.session.commit()
    return jsonify({"ok": True, "item": item.to_dict()})


@yeast_bank_bp.delete("/items/<int:item_id>")
@login_required
def delete_bank_item(item_id: int):
    Item = get_yeast_bank_item()
    Starter = get_yeast_starter_log()
    item = Item.query.get(item_id)
    if not item:
        return _json_error("Item não encontrado", 404)
    linked = Starter.query.filter_by(bank_item_id=item_id).count()
    if linked > 0:
        return _json_error(f"Não é possível excluir: existem {linked} starter(s) vinculados a este item.", 409)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"ok": True})


# -------------------------
# Starters
# -------------------------
@yeast_bank_bp.get("/starters")
@login_required
def list_starters():
    Starter = get_yeast_starter_log()
    items = Starter.query.order_by(Starter.created_at.desc()).all()
    return jsonify({"ok": True, "items": [s.to_dict() for s in items]})


@yeast_bank_bp.post("/starters")
@login_required
def create_starter():
    Starter = get_yeast_starter_log()
    Item = get_yeast_bank_item()
    data = request.get_json(force=True, silent=True) or {}
    bank_item_id = data.get("bank_item_id")
    if not bank_item_id or not Item.query.get(bank_item_id):
        return _json_error("bank_item_id inválido")
    brew = _parse_date(data.get("brew_date"))
    start = _parse_date(data.get("start_date"))
    starter = Starter(
        bank_item_id=bank_item_id,
        brew_date=brew,
        start_date=start,
        target_volume_l=data.get("target_volume_l"),
        notes=data.get("notes"),
        status=data.get("status") or "planned",
    )
    db.session.add(starter)
    db.session.commit()
    return jsonify({"ok": True, "item": starter.to_dict()})


@yeast_bank_bp.put("/starters/<int:starter_id>")
@login_required
def update_starter(starter_id: int):
    Starter = get_yeast_starter_log()
    Item = get_yeast_bank_item()
    starter = Starter.query.get(starter_id)
    if not starter:
        return _json_error("Starter não encontrado", 404)
    data = request.get_json(force=True, silent=True) or {}
    if "bank_item_id" in data:
        bid = data.get("bank_item_id")
        if not bid or not Item.query.get(bid):
            return _json_error("bank_item_id inválido")
        starter.bank_item_id = bid
    for field in ("target_volume_l", "notes", "status"):
        if field in data:
            setattr(starter, field, data.get(field))
    if "brew_date" in data:
        starter.brew_date = _parse_date(data.get("brew_date"))
    if "start_date" in data:
        starter.start_date = _parse_date(data.get("start_date"))
    db.session.commit()
    return jsonify({"ok": True, "item": starter.to_dict()})


@yeast_bank_bp.delete("/starters/<int:starter_id>")
@login_required
def delete_starter(starter_id: int):
    Starter = get_yeast_starter_log()
    starter = Starter.query.get(starter_id)
    if not starter:
        return _json_error("Starter não encontrado", 404)
    db.session.delete(starter)
    db.session.commit()
    return jsonify({"ok": True})


# -------------------------
# Dashboard
# -------------------------
@yeast_bank_bp.get("/dashboard")
@login_required
def dashboard_summary():
    Strain = get_yeast_strain()
    Item = get_yeast_bank_item()
    Starter = get_yeast_starter_log()
    Device = get_yeast_storage_device()
    Reading = get_yeast_storage_reading()
    today = date.today()
    soon = today + timedelta(days=30)

    expiring_list = Item.query.filter(Item.expiry_date.isnot(None), Item.expiry_date <= soon).order_by(Item.expiry_date.asc()).limit(10).all()
    upcoming_starters = Starter.query.filter(Starter.status.in_(["planned", "running"]), Starter.brew_date.isnot(None), Starter.brew_date >= today).order_by(Starter.brew_date.asc()).limit(10).all()

    devices = Device.query.order_by(Device.is_active.desc(), Device.name.asc()).limit(6).all()
    storage_cards = []
    alerts = 0
    stale_cutoff = datetime.utcnow() - timedelta(hours=12)
    for d in devices:
        recent = Reading.query.filter_by(device_id=d.id).order_by(Reading.recorded_at.desc()).limit(20).all()
        recent = list(reversed(recent))
        status = d.status_badge() if hasattr(d, 'status_badge') else 'ok'
        if status.startswith('alert') or (d.last_temperature_at and d.last_temperature_at < stale_cutoff):
            alerts += 1
            if d.last_temperature_at and d.last_temperature_at < stale_cutoff:
                status = 'stale'
        storage_cards.append({
            'id': d.id,
            'name': d.name,
            'device_type': d.device_type,
            'is_active': d.is_active,
            'status': status,
            'current_temperature_c': d.current_temperature_c,
            'target_temperature_c': d.target_temperature_c,
            'temperature_min_c': d.temperature_min_c,
            'temperature_max_c': d.temperature_max_c,
            'last_temperature_at': d.last_temperature_at.isoformat() if d.last_temperature_at else None,
            'recent_temps': [r.temperature_c for r in recent],
            'recent_labels': [r.recorded_at.strftime('%d/%m %H:%M') if r.recorded_at else '' for r in recent],
        })

    return jsonify({
        'ok': True,
        'kpis': {
            'strains_count': Strain.query.count(),
            'items_total': Item.query.count(),
            'items_expired': Item.query.filter(Item.expiry_date.isnot(None), Item.expiry_date < today).count(),
            'items_renew_soon': Item.query.filter(Item.expiry_date.isnot(None), Item.expiry_date >= today, Item.expiry_date <= soon).count(),
            'masters_count': Item.query.filter(Item.storage_type.in_(['slant_master_a', 'slant_master_b'])).count(),
            'work_count': Item.query.filter(Item.storage_type == 'slant_work').count(),
            'plate_count': Item.query.filter(Item.storage_type == 'plate').count(),
            'saline_count': Item.query.filter(Item.storage_type == 'saline').count(),
            'storage_active_count': Device.query.filter_by(is_active=True).count(),
            'storage_alert_count': alerts,
        },
        'expiring_items': [i.to_dict() for i in expiring_list],
        'upcoming_starters': [s.to_dict() for s in upcoming_starters],
        'storage_cards': storage_cards,
        'meta': {'today': today.isoformat(), 'renew_window_days': 30},
    })


# -------------------------
# Config
# -------------------------
@yeast_bank_bp.get('/config')
@login_required
def get_config():
    Cfg = get_yeast_bank_config()
    cfg_row = Cfg.query.order_by(Cfg.id.desc()).first()
    db_cfg = cfg_row.to_dict() if cfg_row else {}
    return jsonify({'ok': True, 'config': _merge_config(db_cfg)})


@yeast_bank_bp.put('/config')
@login_required
def update_config():
    Cfg = get_yeast_bank_config()
    data = request.get_json(force=True, silent=True) or {}
    cfg_row = Cfg.query.order_by(Cfg.id.desc()).first()
    if not cfg_row:
        cfg_row = Cfg()
        db.session.add(cfg_row)

    def _to_pos_int(v):
        try:
            iv = int(v)
            return iv if iv > 0 else None
        except Exception:
            return None

    for field in ('expiry_master_days', 'expiry_work_days', 'expiry_plate_days', 'expiry_saline_days'):
        if field in data:
            setattr(cfg_row, field, _to_pos_int(data.get(field)))
    cfg_row.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True, 'config': _merge_config(cfg_row.to_dict())})
