"""Plugin Maker (Plugin Forge) for BrewStation."""

from typing import List
from flask import Blueprint
from core.plugin_base import PluginBase
from db.database import db


class MakerPlugin(PluginBase):
    def install(self) -> bool:
        # Em dev ajuda, mas o PluginManager já cria todas tabelas depois de registrar plugins
        try:
            models = self.register_models()
            if models:
                with db.engine.begin():
                    db.create_all()
            return True
        except Exception as e:
            print(f"Erro ao instalar plugin {self.name}: {e}")
            db.session.rollback()
            return False

    def uninstall(self) -> bool:
        return True

    def register_routes(self, app) -> List[Blueprint]:
        return []

    def register_models(self) -> List:
        from plugins.plugin_maker.model.maker_models import (
            MakerProject, MakerTable, MakerColumn, MakerRelation,
            MakerScreen, MakerTabGroup, MakerTab, MakerSection, MakerFieldPlacement,
            MakerComputedField,
            MakerGridView, MakerGridColumn, MakerGridAggregation, MakerGridVariant,
            MakerGenerationRun
        )
        return [
            MakerProject, MakerTable, MakerColumn, MakerRelation,
            MakerScreen, MakerTabGroup, MakerTab, MakerSection, MakerFieldPlacement,
            MakerComputedField,
            MakerGridView, MakerGridColumn, MakerGridAggregation, MakerGridVariant,
            MakerGenerationRun
        ]