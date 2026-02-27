from flask import Blueprint, request, jsonify
from flask_login import login_required
from db.database import db
from datetime import date, timedelta

from plugins.plugin_yeast_bank.utils.model_loader import (
    get_yeast_strain,
    get_yeast_bank_item,
    get_yeast_starter_log,
    get_yeast_bank_config
)
   
yeast_bank_bp = Blueprint("yeast_bank", __name__)

def _json_error(msg, status=400):
    return jsonify({"ok": False, "error": msg}), status

def _parse_date(value):
    """
    Aceita:
      - None / "" -> None
      - 'YYYY-MM-DD' -> datetime.date
      - date -> date
    """
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


DEFAULT_CONFIG = {
    "expiry_master_days": 365,
    "expiry_work_days": 180,
    "expiry_plate_days": 30,
    "expiry_saline_days": 90
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

def _calc_expiry(prepared: date | None, storage_type: str | None):
    if not prepared or not storage_type:
        return None
    days = EXPIRY_RULES_DAYS.get(storage_type)
    if not days:
        return None
    return prepared + timedelta(days=days)

# -------------------------
# Strains (Cepas)
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
    if "code" in data: strain.code = data.get("code")
    if "name" in data: strain.name = data.get("name")
    if "family" in data: strain.family = data.get("family")
    if "supplier" in data: strain.supplier = data.get("supplier")
    if "notes" in data: strain.notes = data.get("notes")

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

    # bloquear se houver itens no banco
    count_items = YeastBankItem.query.filter_by(strain_id=strain_id).count()
    if count_items > 0:
        return _json_error("Não é possível excluir: existem itens do banco vinculados a esta cepa", 409)

    db.session.delete(strain)
    db.session.commit()
    return jsonify({"ok": True})


# -------------------------
# Bank Items (Tubo/placa/salina)
# -------------------------
@yeast_bank_bp.get("/items")
@login_required
def list_bank_items():
    YeastBankItem = get_yeast_bank_item()
    items = YeastBankItem.query.order_by(YeastBankItem.created_at.desc()).all()
    return jsonify({"ok": True, "items": [i.to_dict() for i in items]})


@yeast_bank_bp.post("/items")
@login_required
def create_bank_item():
    YeastBankItem = get_yeast_bank_item()
    YeastStrain = get_yeast_strain()

    data = request.get_json(force=True, silent=True) or {}

    strain_id = data.get("strain_id")
    if not strain_id or not YeastStrain.query.get(strain_id):
        return _json_error("strain_id inválido")

    storage_type = (data.get("storage_type") or "").strip()
    if not storage_type:
        return _json_error("storage_type é obrigatório")


    YeastBankConfig = get_yeast_bank_config()
    cfg_row = YeastBankConfig.query.order_by(YeastBankConfig.id.desc()).first()
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


    item = YeastBankItem(
        strain_id=strain_id,
        storage_type=storage_type,
        location=data.get("location"),
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
    YeastBankItem = get_yeast_bank_item()
    item = YeastBankItem.query.get(item_id)
    if not item:
        return _json_error("Item não encontrado", 404)

    data = request.get_json(force=True, silent=True) or {}
    if "storage_type" in data: item.storage_type = data.get("storage_type")
    if "location" in data: item.location = data.get("location")
    if "label" in data: item.label = data.get("label")
    if "prepared_date" in data: item.prepared_date = _parse_date(data.get("prepared_date"))
    if "expiry_date" in data: item.expiry_date = _parse_date(data.get("expiry_date"))
    if "status" in data: item.status = data.get("status")
    if "last_checked" in data: item.last_checked = _parse_date(data.get("last_checked"))
    if "viability_notes" in data: item.viability_notes = data.get("viability_notes")

    db.session.commit()
    return jsonify({"ok": True, "item": item.to_dict()})


@yeast_bank_bp.delete("/items/<int:item_id>")
@login_required
def delete_bank_item(item_id: int):
    YeastBankItem = get_yeast_bank_item()
    item = YeastBankItem.query.get(item_id)
    if not item:
        return _json_error("Item não encontrado", 404)

    db.session.delete(item)
    db.session.commit()
    return jsonify({"ok": True})


# -------------------------
# Starters
# -------------------------
@yeast_bank_bp.get("/starters")
@login_required
def list_starters():
    YeastStarterLog = get_yeast_starter_log()
    items = YeastStarterLog.query.order_by(YeastStarterLog.created_at.desc()).all()
    return jsonify({"ok": True, "items": [s.to_dict() for s in items]})


@yeast_bank_bp.post("/starters")
@login_required
def create_starter():
    YeastStarterLog = get_yeast_starter_log()
    YeastBankItem = get_yeast_bank_item()

    data = request.get_json(force=True, silent=True) or {}

    bank_item_id = data.get("bank_item_id")
    if not bank_item_id or not YeastBankItem.query.get(bank_item_id):
        return _json_error("bank_item_id inválido")

    starter = YeastStarterLog(
        bank_item_id=bank_item_id,
        brew_date=data.get("brew_date"),
        start_date=data.get("start_date"),
        target_volume_l=data.get("target_volume_l"),
        notes=data.get("notes"),
        status=data.get("status") or "planned",
    )
    db.session.add(starter)
    db.session.commit()
    return jsonify({"ok": True, "item": starter.to_dict()})




# -------------------------
# Config
# -------------------------

@yeast_bank_bp.get("/config")
def get_config():
    YeastBankConfig = get_yeast_bank_config()
    cfg_row = YeastBankConfig.query.order_by(YeastBankConfig.id.desc()).first()
    db_cfg = cfg_row.to_dict() if cfg_row else {}
    merged = _merge_config(db_cfg)
    return jsonify({"ok": True, "config": merged})


@yeast_bank_bp.put("/config")
def update_config():
    YeastBankConfig = get_yeast_bank_config()
    data = request.get_json(force=True, silent=True) or {}

    # pega ou cria 1 registro
    cfg_row = YeastBankConfig.query.order_by(YeastBankConfig.id.desc()).first()
    if not cfg_row:
        cfg_row = YeastBankConfig()
        db.session.add(cfg_row)

    def _to_pos_int(v):
        try:
            iv = int(v)
            return iv if iv > 0 else None
        except Exception:
            return None

    if "expiry_master_days" in data: cfg_row.expiry_master_days = _to_pos_int(data.get("expiry_master_days"))
    if "expiry_work_days" in data: cfg_row.expiry_work_days = _to_pos_int(data.get("expiry_work_days"))
    if "expiry_plate_days" in data: cfg_row.expiry_plate_days = _to_pos_int(data.get("expiry_plate_days"))
    if "expiry_saline_days" in data: cfg_row.expiry_saline_days = _to_pos_int(data.get("expiry_saline_days"))

    cfg_row.updated_at = datetime.utcnow()
    db.session.commit()

    merged = _merge_config(cfg_row.to_dict())
    return jsonify({"ok": True, "config": merged})