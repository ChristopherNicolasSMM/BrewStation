"""Rotas API do Plugin Maker (MVP)."""

import json
import re
from pathlib import Path
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from db.database import db

from plugins.plugin_maker.utils.model_loader import (
    get_maker_project, get_maker_table, get_maker_column, get_maker_generation_run
)

maker_bp = Blueprint("maker", __name__)
PLUGINS_DIR = Path(__file__).resolve().parents[3]  # src/plugins


# -----------------------
# Validation helpers
# -----------------------
_RE_PLUGIN_DIR = re.compile(r"^plugin_[a-zA-Z][a-zA-Z0-9_]*$")
_RE_PLUGIN_NAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")

def _clean_str(v, max_len=None):
    if v is None:
        return ""
    v = str(v).strip()
    if max_len:
        v = v[:max_len]
    return v

def _validate_project_payload(data, for_update=False):
    """Valida e normaliza payload de MakerProject.
    - for_update=True: não exige plugin_dir/plugin_name e não permite alterá-los.
    Retorna (clean, error_msg).
    """
    if not isinstance(data, dict):
        return None, "JSON inválido"

    clean = {}

    if not for_update:
        plugin_dir = _clean_str(data.get("plugin_dir"), 128)
        plugin_name = _clean_str(data.get("plugin_name"), 128)
        label = _clean_str(data.get("label"), 128)

        if not plugin_dir or not plugin_name or not label:
            return None, "plugin_dir, plugin_name e label são obrigatórios"

        if not _RE_PLUGIN_DIR.match(plugin_dir):
            return None, "plugin_dir inválido. Use 'plugin_' + letras/números/underscore (ex: plugin_sales)"
        if not _RE_PLUGIN_NAME.match(plugin_name):
            return None, "plugin_name inválido. Use letras/números/underscore (ex: sales)"

        clean["plugin_dir"] = plugin_dir
        clean["plugin_name"] = plugin_name
        clean["label"] = label
    else:
        if "label" in data:
            label = _clean_str(data.get("label"), 128)
            if not label:
                return None, "label não pode ser vazio"
            clean["label"] = label

    # comuns
    if "version" in data or not for_update:
        version = _clean_str(data.get("version") or "0.1.0", 32) or "0.1.0"
        clean["version"] = version

    if "description" in data or not for_update:
        desc = data.get("description")
        clean["description"] = _clean_str(desc, 2000) if desc is not None else None

    if "author" in data or not for_update:
        author = data.get("author")
        clean["author"] = _clean_str(author, 128) if author is not None else None

    if "generation_mode" in data or not for_update:
        gm = _clean_str(data.get("generation_mode") or "guarded_blocks", 32) or "guarded_blocks"
        if gm not in ("guarded_blocks", "full_overwrite"):
            return None, "generation_mode inválido (guarded_blocks|full_overwrite)"
        clean["generation_mode"] = gm

    if "status" in data and for_update:
        st = _clean_str(data.get("status"), 32)
        if st and st not in ("draft", "generated", "synced", "error"):
            return None, "status inválido (draft|generated|synced|error)"
        clean["status"] = st

    if "table_prefix" in data or not for_update:
        tp = data.get("table_prefix")
        tp = _clean_str(tp, 64) if tp is not None else ""
        if tp == "":
            tp = None
        if not for_update and not tp:
            tp = f"{clean['plugin_name']}_"
        if tp:
            tp = tp.replace("-", "_")
            if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*_$", tp):
                return None, "table_prefix inválido. Ex: sales_ (termina com _)"
        clean["table_prefix"] = tp

    return clean, None


def _ok(payload=None):
    data = {"ok": True}
    if payload:
        data.update(payload)
    return jsonify(data)


def _err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


def _log_run(project_id: int, run_type: str, result: str, diff_summary=None, log=None):
    MakerGenerationRun = get_maker_generation_run()
    rec = MakerGenerationRun(
        project_id=project_id,
        run_type=run_type,
        result=result,
        diff_summary=json.dumps(diff_summary, ensure_ascii=False) if isinstance(diff_summary, (dict, list)) else diff_summary,
        log=log
    )
    db.session.add(rec)
    db.session.commit()
    return rec


@maker_bp.get("/info")
@login_required
def info():
    return _ok({"name": "maker", "message": "Plugin Maker ativo"})


@maker_bp.get("/plugins")
@login_required
def list_plugins_fs():
    """Lista plugins existentes via filesystem (src/plugins/*/install.json)."""
    plugins = []
    for p in PLUGINS_DIR.iterdir():
        if not p.is_dir():
            continue
        install = p / "install.json"
        if not install.exists():
            continue
        try:
            cfg = json.loads(install.read_text(encoding="utf-8"))
        except Exception:
            continue
        plugins.append({
            "dir": p.name,
            "name": cfg.get("name") or p.name,
            "label": cfg.get("label") or cfg.get("name") or p.name,
            "version": cfg.get("version"),
        })
    plugins.sort(key=lambda x: x["dir"])
    return _ok({"items": plugins})


# -----------------------
# Projects CRUD
# -----------------------
@maker_bp.get("/projects")
@login_required
def list_projects():
    MakerProject = get_maker_project()
    if not MakerProject:
        return _err("Modelo MakerProject não registrado", 500)
    items = MakerProject.query.order_by(MakerProject.id.desc()).all() or []
    return _ok({"items": [p.to_dict() for p in items], "total": len(items)})


@maker_bp.get("/projects/<int:project_id>")
@login_required
def get_project(project_id: int):
    MakerProject = get_maker_project()
    if not MakerProject:
        return _err("Modelo MakerProject não registrado", 500)
    p = MakerProject.query.get(project_id)
    if not p:
        return _err("Projeto não encontrado", 404)
    return _ok({"item": p.to_dict()})



@maker_bp.post("/projects")
@login_required
def create_project():
    MakerProject = get_maker_project()
    if not MakerProject:
        return _err("Modelo MakerProject não registrado", 500)

    data = request.get_json(force=True, silent=True) or {}
    clean, err = _validate_project_payload(data, for_update=False)
    if err:
        return _err(err)

    # unicidade
    if MakerProject.query.filter_by(plugin_dir=clean["plugin_dir"]).first():
        return _err("plugin_dir já existe", 409)
    if MakerProject.query.filter_by(plugin_name=clean["plugin_name"]).first():
        return _err("plugin_name já existe", 409)

    p = MakerProject(
        plugin_dir=clean["plugin_dir"],
        plugin_name=clean["plugin_name"],
        label=clean["label"],
        version=clean["version"],
        description=clean["description"],
        author=clean["author"],
        table_prefix=clean["table_prefix"],
        status="draft",
        generation_mode=clean["generation_mode"],
    )

    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # fallback para corrida
        return _err("Conflito de unicidade (plugin_dir/plugin_name)", 409)

    return _ok({"item": p.to_dict()})



@maker_bp.put("/projects/<int:project_id>")
@login_required
def update_project(project_id: int):
    MakerProject = get_maker_project()
    if not MakerProject:
        return _err("Modelo MakerProject não registrado", 500)

    p = MakerProject.query.get(project_id)
    if not p:
        return _err("Projeto não encontrado", 404)

    data = request.get_json(force=True, silent=True) or {}
    clean, err = _validate_project_payload(data, for_update=True)
    if err:
        return _err(err)

    # por padrão, não permitimos alterar plugin_dir/plugin_name aqui
    for key in ["label", "version", "description", "author", "table_prefix", "generation_mode", "status"]:
        if key in clean:
            setattr(p, key, clean.get(key))

    db.session.commit()
    return _ok({"item": p.to_dict()})


@maker_bp.delete("/projects/<int:project_id>")
@login_required
def delete_project(project_id: int):
    MakerProject = get_maker_project()
    p = MakerProject.query.get(project_id)
    if not p:
        return _err("Projeto não encontrado", 404)
    db.session.delete(p)
    db.session.commit()
    return _ok()


# -----------------------
# Tables & Columns (mínimo)
# -----------------------
@maker_bp.get("/projects/<int:project_id>/tables")
@login_required
def list_tables(project_id: int):
    MakerTable = get_maker_table()
    items = MakerTable.query.filter_by(project_id=project_id).order_by(MakerTable.id.asc()).all()
    return _ok({"items": [t.to_dict() for t in items]})


@maker_bp.post("/projects/<int:project_id>/tables")
@login_required
def create_table(project_id: int):
    MakerTable = get_maker_table()
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    label = (data.get("label") or "").strip()
    if not name or not label:
        return _err("name e label são obrigatórios")

    t = MakerTable(project_id=project_id, name=name, label=label, description=data.get("description"))
    db.session.add(t)
    db.session.commit()
    return _ok({"item": t.to_dict()})


@maker_bp.put("/tables/<int:table_id>")
@login_required
def update_table(table_id: int):
    MakerTable = get_maker_table()
    if not MakerTable:
        return _err("Modelo MakerTable não registrado", 500)

    t = MakerTable.query.get(table_id)
    if not t:
        return _err("Tabela não encontrada", 404)

    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    label = (data.get("label") or "").strip()
    if "name" in data:
        if not name:
            return _err("name não pode ser vazio")
        t.name = name
    if "label" in data:
        if not label:
            return _err("label não pode ser vazio")
        t.label = label
    if "description" in data:
        t.description = data.get("description")

    for key in ["pk_strategy", "timestamps", "soft_delete"]:
        if key in data:
            setattr(t, key, data.get(key))

    db.session.commit()
    return _ok({"item": t.to_dict()})


@maker_bp.delete("/tables/<int:table_id>")
@login_required
def delete_table(table_id: int):
    MakerTable = get_maker_table()
    MakerColumn = get_maker_column()
    if not MakerTable or not MakerColumn:
        return _err("Modelos MakerTable/MakerColumn não registrados", 500)

    t = MakerTable.query.get(table_id)
    if not t:
        return _err("Tabela não encontrada", 404)

    # cascade manual (MVP)
    MakerColumn.query.filter_by(table_id=table_id).delete()
    db.session.delete(t)
    db.session.commit()
    return _ok()


@maker_bp.get("/tables/<int:table_id>/columns")
@login_required
def list_columns(table_id: int):
    MakerColumn = get_maker_column()
    items = MakerColumn.query.filter_by(table_id=table_id).order_by(MakerColumn.id.asc()).all()
    return _ok({"items": [c.to_dict() for c in items]})


@maker_bp.post("/tables/<int:table_id>/columns")
@login_required
def create_column(table_id: int):
    MakerColumn = get_maker_column()
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    label = (data.get("label") or "").strip()
    data_type = (data.get("data_type") or "").strip()
    if not name or not label or not data_type:
        return _err("name, label e data_type são obrigatórios")

    c = MakerColumn(
        table_id=table_id,
        name=name,
        label=label,
        data_type=data_type,
        length=data.get("length"),
        required=bool(data.get("required", False)),
        unique=bool(data.get("unique", False)),
        indexed=bool(data.get("indexed", False))
    )
    db.session.add(c)
    db.session.commit()
    return _ok({"item": c.to_dict()})


@maker_bp.put("/columns/<int:column_id>")
@login_required
def update_column(column_id: int):
    MakerColumn = get_maker_column()
    if not MakerColumn:
        return _err("Modelo MakerColumn não registrado", 500)

    c = MakerColumn.query.get(column_id)
    if not c:
        return _err("Coluna não encontrada", 404)

    data = request.get_json(force=True, silent=True) or {}

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return _err("name não pode ser vazio")
        c.name = name

    if "label" in data:
        label = (data.get("label") or "").strip()
        if not label:
            return _err("label não pode ser vazio")
        c.label = label

    if "data_type" in data:
        dt = (data.get("data_type") or "").strip()
        if not dt:
            return _err("data_type não pode ser vazio")
        c.data_type = dt

    for key in ["length", "required", "unique", "indexed"]:
        if key in data:
            setattr(c, key, data.get(key))

    db.session.commit()
    return _ok({"item": c.to_dict()})


@maker_bp.delete("/columns/<int:column_id>")
@login_required
def delete_column(column_id: int):
    MakerColumn = get_maker_column()
    if not MakerColumn:
        return _err("Modelo MakerColumn não registrado", 500)

    c = MakerColumn.query.get(column_id)
    if not c:
        return _err("Coluna não encontrada", 404)

    db.session.delete(c)
    db.session.commit()
    return _ok()


# -----------------------
# Rebuild MVP: gera plugin skeleton + manifest
# -----------------------
def _sanitize(name: str) -> str:
    name = name.strip().replace(" ", "_")
    return "".join(ch for ch in name if ch.isalnum() or ch in "_-")


@maker_bp.post("/projects/<int:project_id>/rebuild/preview")
@login_required
def rebuild_preview(project_id: int):
    MakerProject = get_maker_project()
    p = MakerProject.query.get(project_id)
    if not p:
        return _err("Projeto não encontrado", 404)

    target_dir = PLUGINS_DIR / _sanitize(p.plugin_dir)
    diff = {"target_dir": str(target_dir), "exists": target_dir.exists()}
    _log_run(project_id, "preview", "success", diff_summary=diff, log="preview ok")
    return _ok({"diff": diff})


@maker_bp.post("/projects/<int:project_id>/rebuild/apply")
@login_required
def rebuild_apply(project_id: int):
    MakerProject = get_maker_project()
    p = MakerProject.query.get(project_id)
    if not p:
        return _err("Projeto não encontrado", 404)

    plugin_dir = _sanitize(p.plugin_dir)
    plugin_name = _sanitize(p.plugin_name)

    target_dir = PLUGINS_DIR / plugin_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    maker_dir = target_dir / ".maker"
    maker_dir.mkdir(exist_ok=True)

    manifest = {
        "project_id": p.id,
        "plugin_dir": plugin_dir,
        "plugin_name": plugin_name,
        "managed_by_maker": True,
        "generated_at": datetime.utcnow().isoformat(),
        "artifacts": [
            {"path": "install.json", "owner": "maker"},
            {"path": "menu_config.json", "owner": "maker"},
            {"path": "plugin.py", "owner": "maker"},
            {"path": "controller/routes.py", "owner": "maker"},
            {"path": "api/routes/generated_routes.py", "owner": "maker"},
            {"path": f"templates/{plugin_name}/index.html", "owner": "maker"},
            {"path": "static/js/index.js", "owner": "maker"}
        ]
    }

    install_json = {
        "name": plugin_name,
        "label": p.label,
        "version": p.version,
        "description": p.description or "",
        "author": p.author or "",
        "menu_config_path": "menu_config.json",
        "dependencies": [],
        "db_models": [],
        "table_prefix": p.table_prefix
    }
    (target_dir / "install.json").write_text(json.dumps(install_json, ensure_ascii=False, indent=2), encoding="utf-8")

    menu = [{"label": p.label, "url": f"plugin_{plugin_name}_web.index", "icon": "bi bi-grid"}]
    (target_dir / "menu_config.json").write_text(json.dumps(menu, ensure_ascii=False, indent=2), encoding="utf-8")

    (target_dir / "plugin.py").write_text(
        f'"""Plugin {plugin_name} gerado pelo Maker."""\n\n'
        'from typing import List\n'
        'from flask import Blueprint\n'
        'from core.plugin_base import PluginBase\n\n\n'
        'class GeneratedPlugin(PluginBase):\n'
        '    def register_routes(self, app) -> List[Blueprint]:\n'
        '        return []\n\n'
        '    def register_models(self) -> List:\n'
        '        return []\n',
        encoding="utf-8"
    )

    (target_dir / "controller").mkdir(exist_ok=True)
    #(target_dir / "controller" / "routes.py").write_text(
    #    f'"""Rotas web geradas pelo Maker."""\n\n'
    #    'from flask import Blueprint, render_template\n'
    #    'from flask_login import login_required\n'
    #      'from sqlalchemy.exc import IntegrityError\n\n'
    #    f'plugin_{plugin_name}_web = Blueprint("plugin_{plugin_name}_web", __name__)\n\n'
    #    f'@plugin_{plugin_name}_web.route("/{plugin_name}")\n'
    #    '@login_required\n'
    #    'def index():\n'
    #    f'    return render_template("{plugin_name}/index.html")\n',
    #    encoding="utf-8"
    #)
    
    routes_py = f'''"""Rotas web geradas pelo Maker."""

    from flask import Blueprint, render_template
    from flask_login import login_required
    plugin_{plugin_name}_web = Blueprint("plugin_{plugin_name}_web", __name__)
    @plugin_{plugin_name}_web.route("/{plugin_name}")
    @login_required
    def index():
        return render_template("{plugin_name}/index.html")
    '''

    (target_dir / "controller" / "routes.py").write_text(routes_py, encoding="utf-8")

    

    (target_dir / "api" / "routes").mkdir(parents=True, exist_ok=True)
    #(target_dir / "api" / "routes" / "__init__.py").write_text(
    #    "from .generated_routes import generated_api\nall_blueprints=[generated_api]\n",
    #    encoding="utf-8"
    #)
    #(target_dir / "api" / "routes" / "generated_routes.py").write_text(
    #    '"""Rotas API geradas pelo Maker."""\n\n'
    #    'from flask import Blueprint, jsonify\n'
    #    'from flask_login import login_required
    #from sqlalchemy.exc import IntegrityError\n\n'
    #    'generated_api = Blueprint("generated_api", __name__)\n\n'
    #    '@generated_api.get("/info")\n'
    #    '@login_required\n'
    #    'def info():\n'
    #    '    return jsonify({"ok": True, "message": "Plugin gerado ativo"})\n',
    #    encoding="utf-8"
    #)
    
    generated_routes_py = '''"""Rotas API geradas pelo Maker."""

    from flask import Blueprint, jsonify
    from flask_login import login_required

    generated_api = Blueprint("generated_api", __name__)

    @generated_api.get("/info")
    @login_required
    def info():
        return jsonify({"ok": True, "message": "Plugin gerado ativo"})
    '''

    (target_dir / "api" / "routes" / "generated_routes.py").write_text(
        generated_routes_py,
        encoding="utf-8"
    )    

    (target_dir / "templates" / plugin_name).mkdir(parents=True, exist_ok=True)
    
    #(target_dir / "templates" / plugin_name / "index.html").write_text(
    #    '{% extends "base.html" %}\n'
    #    '{% block content %}\n'
    #    f'<div class="pagetitle"><h1>{p.label}</h1></div>\n'
    #    '<section class="section">\n'
    #    '  <div class="card"><div class="card-body">\n'
    #    '    <h5 class="card-title">Gerado pelo Maker</h5>\n'
    #    '    <p class="text-muted">Próximo passo: gerar CRUDs para tabelas.</p>\n'
    #    '  </div></div>\n'
    #    '</section>\n'
    #    '{% endblock %}\n',
    #    encoding="utf-8"
    #)
    
    index_html = (
        '{% extends "base.html" %}\n'
        '{% block content %}\n'
        f'<div class="pagetitle"><h1>{p.label}</h1></div>\n'
        '<section class="section">\n'
        '  <div class="card"><div class="card-body">\n'
        '    <h5 class="card-title">Gerado pelo Maker</h5>\n'
        '    <p class="text-muted">Próximo passo: gerar CRUDs para tabelas.</p>\n'
        '  </div></div>\n'
        '</section>\n'
        '{% endblock %}\n'
    )
    
    (target_dir / "templates" / plugin_name / "index.html").write_text(
        index_html, encoding="utf-8"
    )    

    (target_dir / "static" / "js").mkdir(parents=True, exist_ok=True)
    (target_dir / "static" / "js" / "index.js").write_text(
        "console.log('generated plugin loaded');\n",
        encoding="utf-8"
    )

    (maker_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    p.status = "generated"
    db.session.commit()
    _log_run(project_id, "rebuild", "success", diff_summary={"generated": True, "plugin_dir": plugin_dir}, log="apply ok")

    return _ok({"generated": True, "plugin_dir": plugin_dir})