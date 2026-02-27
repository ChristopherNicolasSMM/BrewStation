from flask import Blueprint, request, jsonify
from flask_login import login_required
from db.database import db

from plugins.plugin_yeast_bank.utils.model_loader import (
    get_yeast_strain,
    get_yeast_bank_item,
    get_yeast_starter_log
)

yeast_bank_bp = Blueprint("yeast_bank_bp", __name__)

def _json_error(msg, status=400):
    return jsonify({"ok": False, "error": msg}), status


# -------------------------
# Strains (Cepas)
# -------------------------
@yeast_bank_bp.get("/yeast_bank/strains")
@login_required
def list_strains():
    YeastStrain = get_yeast_strain()
    strains = YeastStrain.query.order_by(YeastStrain.created_at.desc()).all()
    return jsonify({"ok": True, "items": [s.to_dict() for s in strains]})


@yeast_bank_bp.post("/yeast_bank/strains")
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


@yeast_bank_bp.put("/yeast_bank/strains/<int:strain_id>")
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


@yeast_bank_bp.delete("/yeast_bank/strains/<int:strain_id>")
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
@yeast_bank_bp.get("/yeast_bank/items")
@login_required
def list_bank_items():
    YeastBankItem = get_yeast_bank_item()
    items = YeastBankItem.query.order_by(YeastBankItem.created_at.desc()).all()
    return jsonify({"ok": True, "items": [i.to_dict() for i in items]})


@yeast_bank_bp.post("/yeast_bank/items")
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

    item = YeastBankItem(
        strain_id=strain_id,
        storage_type=storage_type,
        location=data.get("location"),
        label=data.get("label"),
        prepared_date=data.get("prepared_date"),
        expiry_date=data.get("expiry_date"),
        status=data.get("status") or "ok",
        last_checked=data.get("last_checked"),
        viability_notes=data.get("viability_notes"),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"ok": True, "item": item.to_dict()})


@yeast_bank_bp.put("/yeast_bank/items/<int:item_id>")
@login_required
def update_bank_item(item_id: int):
    YeastBankItem = get_yeast_bank_item()
    item = YeastBankItem.query.get(item_id)
    if not item:
        return _json_error("Item não encontrado", 404)

    data = request.get_json(force=True, silent=True) or {}
    for field in [
        "storage_type", "location", "label",
        "prepared_date", "expiry_date",
        "status", "last_checked", "viability_notes"
    ]:
        if field in data:
            setattr(item, field, data.get(field))

    db.session.commit()
    return jsonify({"ok": True, "item": item.to_dict()})


@yeast_bank_bp.delete("/yeast_bank/items/<int:item_id>")
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
@yeast_bank_bp.get("/yeast_bank/starters")
@login_required
def list_starters():
    YeastStarterLog = get_yeast_starter_log()
    items = YeastStarterLog.query.order_by(YeastStarterLog.created_at.desc()).all()
    return jsonify({"ok": True, "items": [s.to_dict() for s in items]})


@yeast_bank_bp.post("/yeast_bank/starters")
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



