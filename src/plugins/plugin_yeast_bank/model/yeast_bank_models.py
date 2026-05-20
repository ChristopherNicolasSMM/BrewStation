from __future__ import annotations

"""Modelos principais do plugin YeastBank.

IMPORTANTE PARA FUTUROS DESENVOLVEDORES
--------------------------------------
1. Este arquivo concentra a estrutura de dados "canônica" do plugin.
2. Sempre que adicionar um novo campo aqui, atualize também:
   - utils/schema.py (migração incremental / bootstrap de schema)
   - utils/model_loader.py (se adicionar novos modelos)
   - plugin.py (registro de modelos)
   - api/routes/yeast_bank_routes.py (serialização/validação/uso dos campos)
3. Evite remover colunas antigas sem estratégia de migração. O plugin já pode
   estar instalado em bases em produção.
"""

from datetime import datetime

from db.database import db


class YeastStrain(db.Model):
    """Cepa base (identidade da levedura).

    A cepa representa a "família/raça" da levedura. Ela não é a amostra física;
    as amostras físicas ficam em YeastBankItem.

    Os campos de viabilidade abaixo são parâmetros do MODELO da cepa, usados
    para estimar a viabilidade dos itens do banco ao longo do tempo.
    """

    __tablename__ = "yeast_strain"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(64), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    family = db.Column(db.String(50), nullable=True)
    supplier = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Estado estratégico da cepa. Não confundir com o status do item físico.
    status = db.Column(db.String(30), nullable=False, default="active")

    # Parâmetros de viabilidade por cepa.
    viability_model = db.Column(db.String(50), nullable=False, default="linear_decay_default")
    daily_viability_loss_pct = db.Column(db.Float, nullable=True, default=0.35)
    viability_correction_factor = db.Column(db.Float, nullable=True, default=1.0)
    initial_reference_viability_pct = db.Column(db.Float, nullable=True, default=95.0)
    viability_floor_pct = db.Column(db.Float, nullable=True, default=0.0)
    viability_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "family": self.family,
            "supplier": self.supplier,
            "notes": self.notes,
            "status": self.status,
            "viability_model": self.viability_model,
            "daily_viability_loss_pct": self.daily_viability_loss_pct,
            "viability_correction_factor": self.viability_correction_factor,
            "initial_reference_viability_pct": self.initial_reference_viability_pct,
            "viability_floor_pct": self.viability_floor_pct,
            "viability_notes": self.viability_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class YeastBankItem(db.Model):
    """Item físico do banco (slant, placa, salina, etc.).

    A viabilidade estimada pertence ao ITEM, não à cepa. A cepa apenas fornece
    os parâmetros do modelo.
    """

    __tablename__ = "yeast_bank_item"

    id = db.Column(db.Integer, primary_key=True)

    strain_id = db.Column(db.Integer, db.ForeignKey("yeast_strain.id"), nullable=False)
    strain = db.relationship("YeastStrain", backref=db.backref("bank_items", lazy=True))

    storage_type = db.Column(db.String(40), nullable=False)
    location = db.Column(db.String(120), nullable=True)
    storage_device_id = db.Column(db.Integer, db.ForeignKey("yeast_storage_device.id"), nullable=True)
    storage_device = db.relationship("YeastStorageDevice", backref=db.backref("bank_items", lazy=True))
    storage_slot = db.Column(db.String(120), nullable=True)
    label = db.Column(db.String(120), nullable=True)

    prepared_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)

    # Status operacional do ITEM físico.
    status = db.Column(db.String(30), default="ok", nullable=False)
    last_checked = db.Column(db.Date, nullable=True)
    viability_notes = db.Column(db.Text, nullable=True)

    # Campos derivados/estimados. Atualizados por histórico, starters e endpoint
    # de recálculo.
    estimated_viability_pct = db.Column(db.Float, nullable=True)
    estimated_viability_updated_at = db.Column(db.DateTime, nullable=True)
    last_viability_reference_type = db.Column(db.String(30), nullable=True)
    last_viability_reference_date = db.Column(db.Date, nullable=True)
    last_viability_reference_value = db.Column(db.Float, nullable=True)

    # Auditoria simples para descarte.
    discarded_at = db.Column(db.DateTime, nullable=True)
    discard_reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "strain_id": self.strain_id,
            "strain": self.strain.to_dict() if self.strain else None,
            "storage_type": self.storage_type,
            "location": self.location,
            "storage_device_id": self.storage_device_id,
            "storage_device": self.storage_device.to_dict() if self.storage_device else None,
            "storage_slot": self.storage_slot,
            "label": self.label,
            "prepared_date": self.prepared_date.isoformat() if self.prepared_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "status": self.status,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "viability_notes": self.viability_notes,
            "estimated_viability_pct": self.estimated_viability_pct,
            "estimated_viability_updated_at": self.estimated_viability_updated_at.isoformat() if self.estimated_viability_updated_at else None,
            "last_viability_reference_type": self.last_viability_reference_type,
            "last_viability_reference_date": self.last_viability_reference_date.isoformat() if self.last_viability_reference_date else None,
            "last_viability_reference_value": self.last_viability_reference_value,
            "discarded_at": self.discarded_at.isoformat() if self.discarded_at else None,
            "discard_reason": self.discard_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class YeastStarterLog(db.Model):
    """Starter / propagação.

    O starter nasce de um item do banco e pode refletir resultados operacionais,
    inclusive contaminação e ações sugeridas/confirmadas sobre a amostra.
    """

    __tablename__ = "yeast_starter_log"

    id = db.Column(db.Integer, primary_key=True)

    bank_item_id = db.Column(db.Integer, db.ForeignKey("yeast_bank_item.id"), nullable=False)
    bank_item = db.relationship("YeastBankItem", backref=db.backref("starters", lazy=True))

    brew_date = db.Column(db.Date, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    target_volume_l = db.Column(db.Float, nullable=True)
    objective = db.Column(db.String(30), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(30), default="planned", nullable=False)
    result_viability_percent = db.Column(db.Float, nullable=True)
    contamination_detected = db.Column(db.Boolean, nullable=False, default=False)
    action_on_bank_item = db.Column(db.String(30), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "bank_item_id": self.bank_item_id,
            "brew_date": self.brew_date.isoformat() if self.brew_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "target_volume_l": self.target_volume_l,
            "objective": self.objective,
            "notes": self.notes,
            "status": self.status,
            "result_viability_percent": self.result_viability_percent,
            "contamination_detected": bool(self.contamination_detected),
            "action_on_bank_item": self.action_on_bank_item,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class YeastStorageDevice(db.Model):
    __tablename__ = "yeast_storage_device"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    machcode = db.Column(db.String(40), nullable=True)
    device_type = db.Column(db.String(40), nullable=False, default="freezer")
    status = db.Column(db.String(30), nullable=False, default="active")
    description = db.Column(db.Text, nullable=True)
    brand = db.Column(db.String(120), nullable=True)
    model = db.Column(db.String(120), nullable=True)
    serial_number = db.Column(db.String(120), nullable=True)
    physical_location = db.Column(db.String(180), nullable=True)
    virtual_address = db.Column(db.String(180), nullable=True)
    target_temperature_c = db.Column(db.Float, nullable=True)
    temperature_min_c = db.Column(db.Float, nullable=True)
    temperature_max_c = db.Column(db.Float, nullable=True)
    current_temperature_c = db.Column(db.Float, nullable=True)
    last_temperature_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def status_badge(self):
        if not self.is_active or self.status == "inactive":
            return "inactive"
        if self.current_temperature_c is None:
            return "no_data"
        if self.temperature_min_c is not None and self.current_temperature_c < self.temperature_min_c:
            return "alert_low"
        if self.temperature_max_c is not None and self.current_temperature_c > self.temperature_max_c:
            return "alert_high"
        return "ok"

    def to_dict(self, include_recent_readings=False):
        data = {
            "id": self.id,
            "name": self.name,
            "machcode": self.machcode,
            "device_type": self.device_type,
            "status": self.status,
            "description": self.description,
            "brand": self.brand,
            "model": self.model,
            "serial_number": self.serial_number,
            "physical_location": self.physical_location,
            "virtual_address": self.virtual_address,
            "target_temperature_c": self.target_temperature_c,
            "temperature_min_c": self.temperature_min_c,
            "temperature_max_c": self.temperature_max_c,
            "current_temperature_c": self.current_temperature_c,
            "last_temperature_at": self.last_temperature_at.isoformat() if self.last_temperature_at else None,
            "is_active": self.is_active,
            "health_status": self.status_badge(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_recent_readings:
            data["recent_readings"] = [r.to_dict() for r in sorted(self.readings, key=lambda x: x.recorded_at or datetime.min)[-20:]] if hasattr(self, "readings") else []
        return data


class YeastStorageReading(db.Model):
    __tablename__ = "yeast_storage_reading"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("yeast_storage_device.id"), nullable=False)
    device = db.relationship("YeastStorageDevice", backref=db.backref("readings", lazy=True, cascade="all, delete-orphan"))
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    temperature_c = db.Column(db.Float, nullable=False)
    humidity_percent = db.Column(db.Float, nullable=True)
    source_type = db.Column(db.String(30), nullable=False, default="manual")
    source_ref = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class YeastBankConfig(db.Model):
    __tablename__ = "yeast_bank_config"

    id = db.Column(db.Integer, primary_key=True)

    expiry_master_days = db.Column(db.Integer, nullable=True)
    expiry_work_days = db.Column(db.Integer, nullable=True)
    expiry_plate_days = db.Column(db.Integer, nullable=True)
    expiry_saline_days = db.Column(db.Integer, nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "expiry_master_days": self.expiry_master_days,
            "expiry_work_days": self.expiry_work_days,
            "expiry_plate_days": self.expiry_plate_days,
            "expiry_saline_days": self.expiry_saline_days,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class YeastCellCountHistory(db.Model):
    """Histórico de contagem / viabilidade.

    Pode ser vinculado a uma cepa, item do banco e/ou starter.
    O objetivo é registrar tanto o cálculo livre quanto o cálculo vinculado.
    """

    __tablename__ = "yeast_cell_count_history"

    id = db.Column(db.Integer, primary_key=True)
    strain_id = db.Column(db.Integer, db.ForeignKey("yeast_strain.id"), nullable=True)
    strain = db.relationship("YeastStrain", backref=db.backref("count_history", lazy=True))

    bank_item_id = db.Column(db.Integer, db.ForeignKey("yeast_bank_item.id"), nullable=True)
    bank_item = db.relationship("YeastBankItem", backref=db.backref("count_history", lazy=True))

    starter_id = db.Column(db.Integer, db.ForeignKey("yeast_starter_log.id"), nullable=True)
    starter = db.relationship("YeastStarterLog", backref=db.backref("count_history", lazy=True))

    sample_date = db.Column(db.Date, nullable=True)
    lot_code = db.Column(db.String(120), nullable=True)
    calc_method_id = db.Column(db.String(80), nullable=True)

    cells_per_ml = db.Column(db.Float, nullable=True)
    viability_percent = db.Column(db.Float, nullable=True)
    viable_cells_per_ml = db.Column(db.Float, nullable=True)
    estimated_viability_percent = db.Column(db.Float, nullable=True)

    contamination_detected = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text, nullable=True)
    raw_inputs = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "strain_id": self.strain_id,
            "bank_item_id": self.bank_item_id,
            "starter_id": self.starter_id,
            "sample_date": self.sample_date.isoformat() if self.sample_date else None,
            "lot_code": self.lot_code,
            "calc_method_id": self.calc_method_id,
            "cells_per_ml": self.cells_per_ml,
            "viability_percent": self.viability_percent,
            "viable_cells_per_ml": self.viable_cells_per_ml,
            "estimated_viability_percent": self.estimated_viability_percent,
            "contamination_detected": bool(self.contamination_detected),
            "notes": self.notes,
            "raw_inputs": self.raw_inputs,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class YeastBankEvent(db.Model):
    """Histórico operacional simples para rastreabilidade de decisões."""

    __tablename__ = "yeast_bank_event"

    id = db.Column(db.Integer, primary_key=True)
    bank_item_id = db.Column(db.Integer, db.ForeignKey("yeast_bank_item.id"), nullable=True)
    bank_item = db.relationship("YeastBankItem", backref=db.backref("events", lazy=True))

    strain_id = db.Column(db.Integer, db.ForeignKey("yeast_strain.id"), nullable=True)
    strain = db.relationship("YeastStrain", backref=db.backref("events", lazy=True))

    starter_id = db.Column(db.Integer, db.ForeignKey("yeast_starter_log.id"), nullable=True)
    starter = db.relationship("YeastStarterLog", backref=db.backref("events", lazy=True))

    event_type = db.Column(db.String(50), nullable=False)
    status_before = db.Column(db.String(30), nullable=True)
    status_after = db.Column(db.String(30), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "bank_item_id": self.bank_item_id,
            "strain_id": self.strain_id,
            "starter_id": self.starter_id,
            "event_type": self.event_type,
            "status_before": self.status_before,
            "status_after": self.status_after,
            "notes": self.notes,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
