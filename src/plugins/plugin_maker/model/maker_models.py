"""Modelos do Plugin Maker (MVP).

IMPORTANTE:
- As tabelas serão prefixadas pelo core com base no install.json (table_prefix).
"""

from datetime import datetime
from db.database import db


class MakerProject(db.Model):
    __tablename__ = "maker_project"
    id = db.Column(db.Integer, primary_key=True)

    plugin_dir = db.Column(db.String(128), nullable=False, unique=True)
    plugin_name = db.Column(db.String(128), nullable=False, unique=True)
    label = db.Column(db.String(128), nullable=False)

    version = db.Column(db.String(32), default="0.1.0")
    description = db.Column(db.Text, nullable=True)
    author = db.Column(db.String(128), nullable=True)

    table_prefix = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(32), default="draft")            # draft|generated|synced|error
    generation_mode = db.Column(db.String(32), default="guarded_blocks")  # guarded_blocks|full_overwrite

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "plugin_dir": self.plugin_dir,
            "plugin_name": self.plugin_name,
            "label": self.label,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "table_prefix": self.table_prefix,
            "status": self.status,
            "generation_mode": self.generation_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MakerTable(db.Model):
    __tablename__ = "maker_table"
    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(db.Integer, db.ForeignKey("maker_project.id"), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    label = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)

    pk_strategy = db.Column(db.String(16), default="int")
    timestamps = db.Column(db.Boolean, default=True)
    soft_delete = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "pk_strategy": self.pk_strategy,
            "timestamps": self.timestamps,
            "soft_delete": self.soft_delete,
        }


class MakerColumn(db.Model):
    __tablename__ = "maker_column"
    id = db.Column(db.Integer, primary_key=True)

    table_id = db.Column(db.Integer, db.ForeignKey("maker_table.id"), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    label = db.Column(db.String(128), nullable=False)

    data_type = db.Column(db.String(32), nullable=False)
    length = db.Column(db.Integer, nullable=True)

    required = db.Column(db.Boolean, default=False)
    unique = db.Column(db.Boolean, default=False)
    indexed = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "table_id": self.table_id,
            "name": self.name,
            "label": self.label,
            "data_type": self.data_type,
            "length": self.length,
            "required": self.required,
            "unique": self.unique,
            "indexed": self.indexed,
        }


class MakerGenerationRun(db.Model):
    __tablename__ = "maker_generation_run"
    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(db.Integer, db.ForeignKey("maker_project.id"), nullable=False)
    run_type = db.Column(db.String(32), nullable=False)     # preview|rebuild|sync|scan
    result = db.Column(db.String(16), nullable=False)       # success|warning|error
    diff_summary = db.Column(db.Text, nullable=True)
    log = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "run_type": self.run_type,
            "result": self.result,
            "diff_summary": self.diff_summary,
            "log": self.log,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Stubs (para não quebrar install.json/db_models no MVP)
# Na próxima iteração, preenchemos essas classes com os campos completos.
class MakerRelation(db.Model): __tablename__ = "maker_relation"; id = db.Column(db.Integer, primary_key=True)
class MakerScreen(db.Model): __tablename__ = "maker_screen"; id = db.Column(db.Integer, primary_key=True)
class MakerTabGroup(db.Model): __tablename__ = "maker_tab_group"; id = db.Column(db.Integer, primary_key=True)
class MakerTab(db.Model): __tablename__ = "maker_tab"; id = db.Column(db.Integer, primary_key=True)
class MakerSection(db.Model): __tablename__ = "maker_section"; id = db.Column(db.Integer, primary_key=True)
class MakerFieldPlacement(db.Model): __tablename__ = "maker_field_placement"; id = db.Column(db.Integer, primary_key=True)
class MakerComputedField(db.Model): __tablename__ = "maker_computed_field"; id = db.Column(db.Integer, primary_key=True)
class MakerGridView(db.Model): __tablename__ = "maker_grid_view"; id = db.Column(db.Integer, primary_key=True)
class MakerGridColumn(db.Model): __tablename__ = "maker_grid_column"; id = db.Column(db.Integer, primary_key=True)
class MakerGridAggregation(db.Model): __tablename__ = "maker_grid_agg"; id = db.Column(db.Integer, primary_key=True)
class MakerGridVariant(db.Model): __tablename__ = "maker_grid_variant"; id = db.Column(db.Integer, primary_key=True)