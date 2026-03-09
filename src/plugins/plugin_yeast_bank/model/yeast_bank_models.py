from datetime import datetime, date
from db.database import db

class YeastStrain(db.Model):
    """
    Cepa base (ex: W-34/70, US-05, Belgian Ardennes, Kveik Voss etc).
    """
    __tablename__ = "yeast_strain"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(64), nullable=True)          # ex: W34/70, US-05, WY1056...
    name = db.Column(db.String(200), nullable=False)        # nome “humano”
    family = db.Column(db.String(50), nullable=True)        # ale/lager/belgian/kveik/wild
    supplier = db.Column(db.String(120), nullable=True)     # Fermentis, Lallemand, White Labs...
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "family": self.family,
            "supplier": self.supplier,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class YeastBankItem(db.Model):
    """
    Item físico do banco (um tubo slant, uma placa, um frasco salina, etc).
    """
    __tablename__ = "yeast_bank_item"

    id = db.Column(db.Integer, primary_key=True)

    strain_id = db.Column(db.Integer, db.ForeignKey("yeast_strain.id"), nullable=False)
    strain = db.relationship("YeastStrain", backref=db.backref("bank_items", lazy=True))

    storage_type = db.Column(db.String(40), nullable=False)   # slant_master_a / slant_master_b / slant_work / plate / saline
    location = db.Column(db.String(120), nullable=True)       # legado / observação complementar
    storage_device_id = db.Column(db.Integer, db.ForeignKey("yeast_storage_device.id"), nullable=True)
    storage_device = db.relationship("YeastStorageDevice", backref=db.backref("bank_items", lazy=True))
    storage_slot = db.Column(db.String(120), nullable=True)
    label = db.Column(db.String(120), nullable=True)          # etiqueta interna (ex: YB-001-A)

    prepared_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)

    status = db.Column(db.String(30), default="ok", nullable=False)  # ok / renew_soon / expired / contaminated / retired
    last_checked = db.Column(db.Date, nullable=True)
    viability_notes = db.Column(db.Text, nullable=True)

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class YeastStarterLog(db.Model):
    """
    Log / planejamento de starter (você disse: 1 semana antes).
    """
    __tablename__ = "yeast_starter_log"

    id = db.Column(db.Integer, primary_key=True)

    bank_item_id = db.Column(db.Integer, db.ForeignKey("yeast_bank_item.id"), nullable=False)
    bank_item = db.relationship("YeastBankItem", backref=db.backref("starters", lazy=True))

    brew_date = db.Column(db.Date, nullable=True)            # dia da brassagem
    start_date = db.Column(db.Date, nullable=True)           # dia que começou starter
    target_volume_l = db.Column(db.Float, nullable=True)     # volume alvo
    notes = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(30), default="planned", nullable=False)  # planned / running / done / canceled

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "bank_item_id": self.bank_item_id,
            "brew_date": self.brew_date.isoformat() if self.brew_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "target_volume_l": self.target_volume_l,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        
class YeastStorageDevice(db.Model):
    __tablename__ = "yeast_storage_device"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
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

    # prazos (dias)
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
        
        
        
        