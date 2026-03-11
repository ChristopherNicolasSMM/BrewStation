from flask import Blueprint, request, jsonify, Response
from flask_login import login_required
from db.database import db
from datetime import date, timedelta, datetime
import csv
import io
import json

from plugins.plugin_yeast_bank.utils.model_loader import (
    get_yeast_strain,
    get_yeast_bank_item,
    get_yeast_starter_log,
    get_yeast_count_history,
    get_yeast_bank_config,
    get_yeast_storage_device,
    get_yeast_storage_reading,
)
from plugins.plugin_yeast_bank.utils.schema import ensure_storage_schema
from plugins.plugin_yeast_bank.utils.calc_engine import load_calc_catalog, run_method

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
        viability_model=(data.get("viability_model") or "linear_decay_default"),
        daily_viability_loss_pct=data.get("daily_viability_loss_pct"),
        viability_correction_factor=data.get("viability_correction_factor"),
        initial_reference_viability_pct=data.get("initial_reference_viability_pct"),
        viability_floor_pct=data.get("viability_floor_pct"),
        status=(data.get("status") or "active"),
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
    for field in ("code", "name", "family", "supplier", "notes", "viability_model", "daily_viability_loss_pct", "viability_correction_factor", "initial_reference_viability_pct", "viability_floor_pct", "status"):
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
        machcode=(data.get("machcode") or None),
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
        "name", "machcode", "device_type", "status", "description", "brand", "model", "serial_number",
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
    for field in ("storage_type", "location", "storage_slot", "label", "status", "viability_notes", "estimated_viability_pct", "last_viability_reference_type", "last_viability_reference_value"):
        if field in data:
            setattr(item, field, data.get(field))
    if "prepared_date" in data:
        item.prepared_date = _parse_date(data.get("prepared_date"))
    if "expiry_date" in data:
        item.expiry_date = _parse_date(data.get("expiry_date"))
    if "last_checked" in data:
        item.last_checked = _parse_date(data.get("last_checked"))
    if "last_viability_reference_date" in data:
        item.last_viability_reference_date = _parse_date(data.get("last_viability_reference_date"))
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
        objective=data.get("objective"),
        notes=data.get("notes"),
        contamination_detected=bool(data.get("contamination_detected", False)),
        result_action=data.get("result_action"),
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
    for field in ("target_volume_l", "objective", "notes", "result_action", "status"):
        if field in data:
            setattr(starter, field, data.get(field))
    if "brew_date" in data:
        starter.brew_date = _parse_date(data.get("brew_date"))
    if "start_date" in data:
        starter.start_date = _parse_date(data.get("start_date"))
    if "contamination_detected" in data:
        starter.contamination_detected = bool(data.get("contamination_detected"))
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
# Ferramentas / Contagem / Viabilidade
# -------------------------
@yeast_bank_bp.get("/tools/calcs")
@login_required
def tools_calcs():
    return jsonify({"ok": True, "catalog": load_calc_catalog()})


@yeast_bank_bp.post("/tools/run")
@login_required
def tools_run():
    data = request.get_json(force=True, silent=True) or {}
    catalog = load_calc_catalog()
    kind = (data.get("kind") or "").strip()
    calc_id = (data.get("calc_id") or "").strip()
    inputs = data.get("inputs") or {}

    key_map = {
        "cell_count": "cell_count_methods",
        "viability": "viability_methods",
        "viability_model": "viability_models",
    }
    catalog_key = key_map.get(kind)
    if not catalog_key:
        return _json_error("kind inválido")

    method = next((m for m in (catalog.get(catalog_key) or []) if m.get("id") == calc_id), None)
    if not method:
        return _json_error("Método não encontrado", 404)

    try:
        result = run_method(method, inputs)
        return jsonify({"ok": True, "result": result})
    except Exception as exc:
        return _json_error(f"Erro ao executar cálculo: {exc}")


@yeast_bank_bp.get("/tools/history")
@login_required
def list_tools_history():
    Hist = get_yeast_count_history()
    q = Hist.query

    strain_id = request.args.get("strain_id", type=int)
    bank_item_id = request.args.get("bank_item_id", type=int)
    lot_code = (request.args.get("lot_code") or "").strip()
    calc_method_id = (request.args.get("calc_method_id") or "").strip()
    starter_id = request.args.get("starter_id", type=int)

    if strain_id:
        q = q.filter(Hist.strain_id == strain_id)
    if bank_item_id:
        q = q.filter(Hist.bank_item_id == bank_item_id)
    if starter_id:
        q = q.filter(Hist.starter_id == starter_id)
    if lot_code:
        q = q.filter(Hist.lot_code == lot_code)
    if calc_method_id:
        q = q.filter(Hist.calc_method_id == calc_method_id)

    items = q.order_by(Hist.sample_date.asc(), Hist.created_at.asc()).all()
    return jsonify({"ok": True, "items": [i.to_dict() for i in items]})


@yeast_bank_bp.post("/tools/history")
@login_required
def create_tools_history():
    Hist = get_yeast_count_history()
    Strain = get_yeast_strain()
    Item = get_yeast_bank_item()
    Starter = get_yeast_starter_log()

    data = request.get_json(force=True, silent=True) or {}
    strain_id = data.get("strain_id")
    bank_item_id = data.get("bank_item_id")
    starter_id = data.get("starter_id")

    if not strain_id or not Strain.query.get(strain_id):
        return _json_error("strain_id inválido")
    if bank_item_id and not Item.query.get(bank_item_id):
        return _json_error("bank_item_id inválido")
    if starter_id and not Starter.query.get(starter_id):
        return _json_error("starter_id inválido")

    sample_date = _parse_date(data.get("sample_date"))
    if not sample_date:
        return _json_error("sample_date inválida")

    hist = Hist(
        strain_id=strain_id,
        bank_item_id=bank_item_id,
        starter_id=starter_id,
        lot_code=data.get("lot_code"),
        sample_date=sample_date,
        calc_method_id=data.get("calc_method_id"),
        cells_per_ml=data.get("cells_per_ml"),
        viability_percent=data.get("viability_percent"),
        viable_cells_per_ml=data.get("viable_cells_per_ml"),
        estimated_viability_percent=data.get("estimated_viability_percent"),
        contamination_detected=bool(data.get("contamination_detected", False)),
        notes=data.get("notes"),
        raw_inputs_json=json.dumps(data.get("raw_inputs") or {}, ensure_ascii=False),
    )
    db.session.add(hist)

    item = Item.query.get(bank_item_id) if bank_item_id else None
    if item:
        if data.get("estimated_viability_percent") is not None:
            item.estimated_viability_pct = data.get("estimated_viability_percent")
            item.estimated_viability_updated_at = datetime.utcnow()
        if data.get("viability_percent") is not None:
            item.last_viability_reference_type = "count_history"
            item.last_viability_reference_date = sample_date
            item.last_viability_reference_value = data.get("viability_percent")
        if bool(data.get("contamination_detected", False)):
            item.status = "contaminated"
            if item.strain and getattr(item.strain, 'status', None) == 'active':
                item.strain.status = 'watch'

    starter = Starter.query.get(starter_id) if starter_id else None
    if starter and bool(data.get("contamination_detected", False)):
        starter.contamination_detected = True
        starter.status = "contaminated"

    db.session.commit()
    return jsonify({"ok": True, "item": hist.to_dict()})


def _apply_item_viability(item, reference_date, reference_value, reference_type):
    strain = item.strain
    if not reference_date or reference_value is None:
        return False
    days = max(0, (date.today() - reference_date).days)
    loss_per_day = float(getattr(strain, 'daily_viability_loss_pct', 0.35) or 0.35)
    corr = float(getattr(strain, 'viability_correction_factor', 1.0) or 1.0)
    floor = float(getattr(strain, 'viability_floor_pct', 0.0) or 0.0)
    est = max(floor, (float(reference_value) - (days * loss_per_day)) * corr)
    est = max(0.0, min(100.0, est))
    item.estimated_viability_pct = est
    item.estimated_viability_updated_at = datetime.utcnow()
    item.last_viability_reference_type = reference_type
    item.last_viability_reference_date = reference_date
    item.last_viability_reference_value = reference_value
    return True


@yeast_bank_bp.post("/viability/recalculate")
@login_required
def recalculate_viability():
    Item = get_yeast_bank_item()
    Hist = get_yeast_count_history()
    Starter = get_yeast_starter_log()

    processed = updated = skipped = items_without_reference = 0
    for item in Item.query.order_by(Item.id.asc()).all():
        processed += 1
        if item.status in ("discarded", "retired"):
            skipped += 1
            continue

        hist = Hist.query.filter(Hist.bank_item_id == item.id, Hist.viability_percent.isnot(None)).order_by(Hist.sample_date.desc(), Hist.created_at.desc()).first()
        starter = Starter.query.filter(Starter.bank_item_id == item.id, Starter.start_date.isnot(None)).order_by(Starter.start_date.desc(), Starter.created_at.desc()).first()

        if hist:
            ok = _apply_item_viability(item, hist.sample_date, hist.viability_percent, "count_history")
        elif starter:
            ref = getattr(item.strain, 'initial_reference_viability_pct', 96.0) or 96.0
            ok = _apply_item_viability(item, starter.start_date, ref, "starter")
        elif item.prepared_date:
            ref = getattr(item.strain, 'initial_reference_viability_pct', 96.0) or 96.0
            ok = _apply_item_viability(item, item.prepared_date, ref, "prepared_date")
        else:
            ok = False

        if ok:
            updated += 1
        else:
            items_without_reference += 1

    db.session.commit()
    return jsonify({
        "ok": True,
        "processed": processed,
        "updated": updated,
        "skipped": skipped,
        "items_without_reference": items_without_reference,
    })


@yeast_bank_bp.get("/starters/export/json")
@login_required
def export_starters_json():
    Starter = get_yeast_starter_log()
    items = Starter.query.order_by(Starter.created_at.desc()).all()
    return jsonify({"ok": True, "items": [s.to_dict() for s in items]})


@yeast_bank_bp.get("/starters/export/csv")
@login_required
def export_starters_csv():
    Starter = get_yeast_starter_log()
    rows = Starter.query.order_by(Starter.created_at.desc()).all()
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(["id", "bank_item_id", "brew_date", "start_date", "target_volume_l", "objective", "status", "contamination_detected", "result_action", "notes"])
    for s in rows:
        writer.writerow([s.id, s.bank_item_id, s.brew_date or "", s.start_date or "", s.target_volume_l or "", s.objective or "", s.status or "", int(bool(getattr(s, 'contamination_detected', False))), s.result_action or "", s.notes or ""])
    return Response(
        sio.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=yeast_bank_starters.csv"},
    )


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
