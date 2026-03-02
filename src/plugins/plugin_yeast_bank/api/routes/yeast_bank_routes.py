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


@yeast_bank_bp.get("/strains/export/json")
def export_strains_json():
    YeastStrain = get_yeast_strain()
    items = YeastStrain.query.order_by(YeastStrain.id.asc()).all()
    return jsonify({"ok": True, "items": [s.to_dict() for s in items]})


@yeast_bank_bp.get("/strains/export/csv")
def export_strains_csv():
    YeastStrain = get_yeast_strain()
    items = YeastStrain.query.order_by(YeastStrain.id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["id", "code", "name", "family", "supplier", "notes", "created_at"])

    for s in items:
        writer.writerow([
            s.id,
            s.code or "",
            s.name or "",
            s.family or "",
            s.supplier or "",
            (s.notes or "").replace("\n", " ").replace("\r", " "),
            s.created_at.isoformat() if s.created_at else ""
        ])

    csv_text = output.getvalue()
    output.close()

    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="yeast_bank_strains.csv"'}
    )



    
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
    YeastStarterLog = get_yeast_starter_log()

    item = YeastBankItem.query.get(item_id)
    if not item:
        return _json_error("Item não encontrado", 404)

    # ✅ BLOQUEIO: se houver starter vinculado, NÃO delete.
    linked = YeastStarterLog.query.filter_by(bank_item_id=item_id).count()
    if linked > 0:
        return _json_error(
            f"Não é possível excluir: existem {linked} starter(s) vinculados a este item. "
            f"Exclua os starters primeiro ou marque o item como 'retired'.",
            409
        )

    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return _json_error(f"Erro ao excluir item: {str(e)}", 500)



@yeast_bank_bp.get("/items/export/json")
@login_required
def export_items_json():
    YeastBankItem = get_yeast_bank_item()
    items = YeastBankItem.query.order_by(YeastBankItem.id.asc()).all()

    payload = {
        "ok": True,
        "items": [i.to_dict() for i in items]
    }
    return jsonify(payload)


@yeast_bank_bp.get("/items/export/csv")
@login_required
def export_items_csv():
    YeastBankItem = get_yeast_bank_item()
    items = YeastBankItem.query.order_by(YeastBankItem.id.asc()).all()

    # gera CSV em memória
    output = io.StringIO()
    writer = csv.writer(output)

    # header
    writer.writerow([
        "id",
        "strain_id",
        "strain_code",
        "strain_name",
        "storage_type",
        "label",
        "location",
        "prepared_date",
        "expiry_date",
        "status",
        "last_checked",
        "viability_notes"
    ])

    for i in items:
        s = i.strain
        writer.writerow([
            i.id,
            i.strain_id,
            getattr(s, "code", "") if s else "",
            getattr(s, "name", "") if s else "",
            i.storage_type or "",
            i.label or "",
            i.location or "",
            i.prepared_date.isoformat() if i.prepared_date else "",
            i.expiry_date.isoformat() if i.expiry_date else "",
            i.status or "",
            i.last_checked.isoformat() if i.last_checked else "",
            (i.viability_notes or "").replace("\n", " ").replace("\r", " ")
        ])

    csv_text = output.getvalue()
    output.close()

    filename = "yeast_bank_items.csv"
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
    
    
    
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
    
    brew = _parse_date(data.get("brew_date"))
    start = _parse_date(data.get("start_date"))

    if data.get("brew_date") and brew is None:
        return _json_error("brew_date inválido (use YYYY-MM-DD)")
    if data.get("start_date") and start is None:
        return _json_error("start_date inválido (use YYYY-MM-DD)")

    starter = YeastStarterLog(
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


@yeast_bank_bp.delete("/starters/<int:starter_id>")
@login_required
def delete_starter(starter_id: int):
    YeastStarterLog = get_yeast_starter_log()
    starter = YeastStarterLog.query.get(starter_id)
    if not starter:
        return _json_error("Starter não encontrado", 404)

    db.session.delete(starter)
    db.session.commit()
    return jsonify({"ok": True})


@yeast_bank_bp.get("/starters/export/json")
def export_starters_json():
    YeastStarterLog = get_yeast_starter_log()
    items = YeastStarterLog.query.order_by(YeastStarterLog.id.asc()).all()
    return jsonify({"ok": True, "items": [s.to_dict() for s in items]})


@yeast_bank_bp.get("/starters/export/csv")
def export_starters_csv():
    YeastStarterLog = get_yeast_starter_log()
    items = YeastStarterLog.query.order_by(YeastStarterLog.id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id",
        "bank_item_id",
        "start_date",
        "brew_date",
        "target_volume_l",
        "status",
        "notes",
        "created_at"
    ])

    for s in items:
        writer.writerow([
            s.id,
            s.bank_item_id,
            s.start_date.isoformat() if s.start_date else "",
            s.brew_date.isoformat() if s.brew_date else "",
            s.target_volume_l if s.target_volume_l is not None else "",
            s.status or "",
            (s.notes or "").replace("\n", " ").replace("\r", " "),
            s.created_at.isoformat() if s.created_at else ""
        ])

    csv_text = output.getvalue()
    output.close()

    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="yeast_bank_starters.csv"'}
    )

@yeast_bank_bp.put("/starters/<int:starter_id>")
def update_starter(starter_id: int):
    YeastStarterLog = get_yeast_starter_log()
    starter = YeastStarterLog.query.get(starter_id)
    if not starter:
        return _json_error("Starter não encontrado", 404)

    data = request.get_json(force=True, silent=True) or {}

    if "bank_item_id" in data:
        YeastBankItem = get_yeast_bank_item()
        bid = data.get("bank_item_id")
        if not bid or not YeastBankItem.query.get(bid):
            return _json_error("bank_item_id inválido")
        starter.bank_item_id = bid

    if "brew_date" in data: starter.brew_date = _parse_date(data.get("brew_date"))
    if "start_date" in data: starter.start_date = _parse_date(data.get("start_date"))
    if "target_volume_l" in data: starter.target_volume_l = data.get("target_volume_l")
    if "notes" in data: starter.notes = data.get("notes")
    if "status" in data: starter.status = data.get("status")

    db.session.commit()
    return jsonify({"ok": True, "item": starter.to_dict()})

# -------------------------
# Dashboard
# -------------------------
from datetime import date, timedelta

@yeast_bank_bp.get("/dashboard")
def dashboard_summary():
    YeastStrain = get_yeast_strain()
    YeastBankItem = get_yeast_bank_item()
    YeastStarterLog = get_yeast_starter_log()

    today = date.today()
    soon = today + timedelta(days=30)

    strains_count = YeastStrain.query.count()
    items_total = YeastBankItem.query.count()

    items_expired = YeastBankItem.query.filter(
        YeastBankItem.expiry_date.isnot(None),
        YeastBankItem.expiry_date < today
    ).count()

    items_renew_soon = YeastBankItem.query.filter(
        YeastBankItem.expiry_date.isnot(None),
        YeastBankItem.expiry_date >= today,
        YeastBankItem.expiry_date <= soon
    ).count()

    masters_count = YeastBankItem.query.filter(
        YeastBankItem.storage_type.in_(["slant_master_a", "slant_master_b"])
    ).count()

    work_count = YeastBankItem.query.filter(
        YeastBankItem.storage_type == "slant_work"
    ).count()

    plate_count = YeastBankItem.query.filter(
        YeastBankItem.storage_type == "plate"
    ).count()

    saline_count = YeastBankItem.query.filter(
        YeastBankItem.storage_type == "saline"
    ).count()

    # listas (limites pequenos)
    expiring_list = YeastBankItem.query.filter(
        YeastBankItem.expiry_date.isnot(None),
        YeastBankItem.expiry_date <= soon
    ).order_by(YeastBankItem.expiry_date.asc()).limit(10).all()

    upcoming_starters = YeastStarterLog.query.filter(
        YeastStarterLog.status.in_(["planned", "running"]),
        YeastStarterLog.brew_date.isnot(None),
        YeastStarterLog.brew_date >= today
    ).order_by(YeastStarterLog.brew_date.asc()).limit(10).all()

    return jsonify({
        "ok": True,
        "kpis": {
            "strains_count": strains_count,
            "items_total": items_total,
            "items_expired": items_expired,
            "items_renew_soon": items_renew_soon,
            "masters_count": masters_count,
            "work_count": work_count,
            "plate_count": plate_count,
            "saline_count": saline_count
        },
        "expiring_items": [i.to_dict() for i in expiring_list],
        "upcoming_starters": [s.to_dict() for s in upcoming_starters],
        "meta": {
            "today": today.isoformat(),
            "renew_window_days": 30
        }
    })


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

# -------------------------
# Google Calendar (Eventos)
# -------------------------
from flask import redirect, session
from plugins.plugin_yeast_bank.utils.google_calendar import (
    read_config as gcal_read_config,
    write_config as gcal_write_config,
    list_templates as gcal_list_templates,
    load_template as gcal_load_template,
    save_template as gcal_save_template,
    render_html as gcal_render_html,
    get_credentials as gcal_get_credentials,
    build_service as gcal_build_service,
    start_oauth as gcal_start_oauth,
    finish_oauth as gcal_finish_oauth,
    google_supported as gcal_google_supported,
    DEFAULT_CONFIG as GCAL_DEFAULT_CONFIG,
)

def _fmt_date(d):
    if not d:
        return ""
    try:
        return d.isoformat()
    except Exception:
        return str(d)

def _add_days(d: date, days: int) -> date:
    return d + timedelta(days=int(days or 0))

def _build_context(strain=None, bank_item=None, starter_date: date | None = None, viability_days: int = 0, review_days: int = 0):
    ctx = {
        "strain_id": getattr(strain, "id", None),
        "strain_code": getattr(strain, "code", None),
        "strain_name": getattr(strain, "name", None),
        "bank_item_id": getattr(bank_item, "id", None),
        "bank_item_label": getattr(bank_item, "label", None) if bank_item else None,
        "bank_item_batch": getattr(bank_item, "batch", None) if bank_item else None,
        "starter_date": _fmt_date(starter_date),
        "viability_days": int(viability_days or 0),
        "review_days": int(review_days or 0),
        "viability_date": _fmt_date(_add_days(starter_date, viability_days) if starter_date else None),
        "review_date": _fmt_date(_add_days(starter_date, review_days) if starter_date else None),
        "now": datetime.utcnow().isoformat() + "Z",
    }
    return ctx

def _plan_events(ctx: dict, cfg: dict):
    tz = (cfg.get("timezone") or GCAL_DEFAULT_CONFIG["timezone"])
    s = ctx.get("starter_date") or ""
    v = ctx.get("viability_date") or ""
    r = ctx.get("review_date") or ""

    templates = cfg.get("event_summary_templates") or GCAL_DEFAULT_CONFIG["event_summary_templates"]
    strain_name = ctx.get("strain_name") or "Cepa"

    def fmt_sum(key, fallback):
        t = templates.get(key) or fallback
        try:
            return t.format(**ctx)
        except Exception:
            return fallback.format(strain_name=strain_name)

    events = []

    if s:
        events.append({
            "kind": "starter",
            "summary": fmt_sum("starter", "Starter — {strain_name}"),
            "start": s,
            "end": s,
            "timezone": tz,
        })
    if v:
        events.append({
            "kind": "viability",
            "summary": fmt_sum("viability", "Viabilidade estimada — {strain_name}"),
            "start": v,
            "end": v,
            "timezone": tz,
        })
    if r:
        events.append({
            "kind": "review",
            "summary": fmt_sum("review", "Revisão — {strain_name}"),
            "start": r,
            "end": r,
            "timezone": tz,
        })
    return events

def _event_body(ev: dict, description_html: str | None = None):
    # all-day event (date only)
    tz = ev.get("timezone") or "America/Sao_Paulo"
    start = ev.get("start")
    end = ev.get("end") or start
    body = {
        "summary": ev.get("summary") or "YeastBank",
        "description": (description_html or "").strip(),
        "start": {"date": start, "timeZone": tz},
        "end": {"date": end, "timeZone": tz},
    }
    return body

@yeast_bank_bp.get("/gcal/config")
@login_required
def gcal_get_config():
    cfg = gcal_read_config()
    return jsonify({"ok": True, "config": cfg})

@yeast_bank_bp.post("/gcal/config")
@login_required
def gcal_set_config():
    data = request.get_json(force=True, silent=True) or {}
    if not isinstance(data, dict):
        return _json_error("JSON inválido")
    cfg = gcal_write_config(data)
    return jsonify({"ok": True, "config": cfg})

@yeast_bank_bp.get("/gcal/templates")
@login_required
def gcal_templates():
    return jsonify({"ok": True, "items": gcal_list_templates()})

@yeast_bank_bp.get("/gcal/templates/<name>")
@login_required
def gcal_template_get(name: str):
    try:
        html = gcal_load_template(name)
        return jsonify({"ok": True, "name": name, "html": html})
    except FileNotFoundError:
        return _json_error("Template não encontrado", 404)
    except Exception as e:
        return _json_error(str(e), 400)

@yeast_bank_bp.post("/gcal/templates/save")
@login_required
def gcal_template_save():
    data = request.get_json(force=True, silent=True) or {}
    try:
        name = gcal_save_template(data.get("name"), data.get("html") or "")
        return jsonify({"ok": True, "name": name})
    except Exception as e:
        return _json_error(str(e), 400)

@yeast_bank_bp.post("/gcal/templates/preview")
@login_required
def gcal_template_preview():
    data = request.get_json(force=True, silent=True) or {}
    html = data.get("html") or ""
    # preview context sample
    ctx = _build_context(
        strain=type("S", (), {"id": 1, "code": "WLP001", "name": "American Ale"})(),
        bank_item=type("I", (), {"id": 10, "label": "Slant A", "batch": "Lote-01"})(),
        starter_date=date.today(),
        viability_days=2,
        review_days=7
    )
    preview = gcal_render_html(html, ctx)
    return jsonify({"ok": True, "preview_html": preview})

@yeast_bank_bp.post("/gcal/plan")
@login_required
def gcal_plan():
    data = request.get_json(force=True, silent=True) or {}

    strain_id = data.get("strain_id")
    if not strain_id:
        return _json_error("strain_id é obrigatório")

    starter_date = _parse_date(data.get("starter_date"))
    if not starter_date:
        return _json_error("starter_date inválida (use YYYY-MM-DD)")

    viability_days = int(data.get("viability_days") or 0)
    review_days = int(data.get("review_days") or 0)

    YeastStrain = get_yeast_strain()
    YeastBankItem = get_yeast_bank_item()

    strain = YeastStrain.query.get(int(strain_id))
    if not strain:
        return _json_error("Cepa não encontrada", 404)

    bank_item = None
    bank_item_id = data.get("bank_item_id")
    if bank_item_id:
        bank_item = YeastBankItem.query.get(int(bank_item_id))

    cfg = gcal_read_config()
    ctx = _build_context(strain=strain, bank_item=bank_item, starter_date=starter_date, viability_days=viability_days, review_days=review_days)

    # choose template
    tpl_name = cfg.get("default_template_name") or "starter_event.html"
    preview_html = ""
    try:
        tpl_html = gcal_load_template(tpl_name)
        preview_html = gcal_render_html(tpl_html, ctx)
    except Exception:
        # fallback safe preview
        preview_html = gcal_render_html("<div><strong>{{ strain_name }}</strong><br/>Starter: {{ starter_date }}</div>", ctx)

    events = _plan_events(ctx, cfg)

    auth_required = (gcal_get_credentials() is None)
    if not gcal_google_supported():
        auth_required = True

    return jsonify({"ok": True, "events": events, "preview_html": preview_html, "auth_required": auth_required})

@yeast_bank_bp.get("/gcal/auth")
@login_required
def gcal_auth():
    next_path = request.args.get("next") or "/yeast_bank/calendar"
    auth_url, err = gcal_start_oauth(next_path=next_path)
    if err:
        # show error in a simple redirect back (caller UI will show warning)
        return jsonify({"ok": False, "error": err, "auth_required": True}), 400
    return redirect(auth_url)

@yeast_bank_bp.get("/gcal/callback")
@login_required
def gcal_callback():
    ok, msg = gcal_finish_oauth()
    next_path = (session.get("gcal_next") or "/yeast_bank/calendar").strip()
    if not ok:
        # fallback: return a simple page with error (avoid JSON here because user lands in browser)
        return f"<h3>OAuth erro</h3><pre>{msg}</pre><p><a href='{next_path}'>Voltar</a></p>", 400
    return redirect(next_path)

@yeast_bank_bp.post("/gcal/create")
@login_required
def gcal_create():
    data = request.get_json(force=True, silent=True) or {}

    strain_id = data.get("strain_id")
    if not strain_id:
        return _json_error("strain_id é obrigatório")

    starter_date = _parse_date(data.get("starter_date"))
    if not starter_date:
        return _json_error("starter_date inválida (use YYYY-MM-DD)")

    calendar_id = (data.get("calendar_id") or "").strip()
    if not calendar_id:
        return _json_error("calendar_id é obrigatório")

    viability_days = int(data.get("viability_days") or 0)
    review_days = int(data.get("review_days") or 0)

    YeastStrain = get_yeast_strain()
    YeastBankItem = get_yeast_bank_item()

    strain = YeastStrain.query.get(int(strain_id))
    if not strain:
        return _json_error("Cepa não encontrada", 404)

    bank_item = None
    bank_item_id = data.get("bank_item_id")
    if bank_item_id:
        bank_item = YeastBankItem.query.get(int(bank_item_id))

    cfg = gcal_read_config()
    ctx = _build_context(strain=strain, bank_item=bank_item, starter_date=starter_date, viability_days=viability_days, review_days=review_days)

    tpl_name = cfg.get("default_template_name") or "starter_event.html"
    try:
        tpl_html = gcal_load_template(tpl_name)
        description_html = gcal_render_html(tpl_html, ctx)
    except Exception:
        description_html = gcal_render_html("<div><strong>{{ strain_name }}</strong><br/>Starter: {{ starter_date }}</div>", ctx)

    events = _plan_events(ctx, cfg)

    creds = gcal_get_credentials()
    if not creds:
        return jsonify({"ok": False, "error": "Google não autorizado", "auth_required": True, "events": events, "preview_html": description_html}), 401

    try:
        service = gcal_build_service(creds)
        created = []
        for ev in events:
            body = _event_body(ev, description_html=description_html)
            created_ev = service.events().insert(calendarId=calendar_id, body=body).execute()
            created.append({"id": created_ev.get("id"), "summary": ev.get("summary"), "start": ev.get("start"), "kind": ev.get("kind")})
        return jsonify({"ok": True, "events": created, "preview_html": description_html})
    except Exception as e:
        return _json_error(f"Falha ao criar eventos no Google Calendar: {e}", 500)
