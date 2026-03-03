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
    location = db.Column(db.String(120), nullable=True)       # ex: Geladeira 1 / Caixa A / Linha 2
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
        
        
        
        

class YeastCountHistory(db.Model):
    """Histórico de contagens/viabilidade (ferramentas).
    Mantém chave por (data, lote, método) + vínculos com cepa/item.
    """
    __tablename__ = "yeast_count_history"

    id = db.Column(db.Integer, primary_key=True)

    # vínculos
    strain_id = db.Column(db.Integer, db.ForeignKey(YeastStrain.id), nullable=False, index=True)
    bank_item_id = db.Column(db.Integer, db.ForeignKey(YeastBankItem.id), nullable=True, index=True)

    lot_code = db.Column(db.String(120), nullable=True, index=True)

    # método de cálculo selecionado (id do JSON)
    calc_method_id = db.Column(db.String(120), nullable=False, index=True)

    # datas
    sample_date = db.Column(db.Date, nullable=False, index=True)

    # medidas principais
    cells_per_ml = db.Column(db.Float, nullable=True)
    viability_percent = db.Column(db.Float, nullable=True)
    viable_cells_per_ml = db.Column(db.Float, nullable=True)

    estimated_viability_percent = db.Column(db.Float, nullable=True)

    # auditoria
    raw_inputs_json = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    strain = db.relationship("YeastStrain", backref="count_history")
    bank_item = db.relationship("YeastBankItem")

    def to_dict(self):
        return {
            "id": self.id,
            "strain_id": self.strain_id,
            "bank_item_id": self.bank_item_id,
            "lot_code": self.lot_code,
            "calc_method_id": self.calc_method_id,
            "sample_date": self.sample_date.isoformat() if self.sample_date else None,
            "cells_per_ml": self.cells_per_ml,
            "viability_percent": self.viability_percent,
            "viable_cells_per_ml": self.viable_cells_per_ml,
            "estimated_viability_percent": self.estimated_viability_percent,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
