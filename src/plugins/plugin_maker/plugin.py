"""Plugin Maker (Plugin Forge) for BrewStation."""

from typing import List

from flask import Blueprint

from core.plugin_base import PluginBase
from db.database import db


class MakerPlugin(PluginBase):
    def install(self) -> bool:
        """O core (PluginManager) cria as tabelas depois de registrar/prefixar models.
        Aqui apenas garantimos que os models importam corretamente.
        """
        try:
            _ = self.register_models()
            return True
        except Exception as e:
            print(f"[plugin_maker] Erro ao instalar plugin {self.name}: {e}")
            db.session.rollback()
            return False

    def uninstall(self) -> bool:
        return True

    def register_routes(self, app) -> List[Blueprint]:
        try:
            # WEB
            # API
            from plugins.plugin_maker.api.routes import all_blueprints
            from plugins.plugin_maker.controller.routes import plugin_maker_web
            return [plugin_maker_web, *all_blueprints]
        except Exception as e:
            print(f"[plugin_maker] Erro ao registrar rotas: {e}")
            return []

    def register_models(self) -> List:
        from plugins.plugin_maker.model.maker_models import (
            MakerColumn, MakerComputedField, MakerFieldPlacement,
            MakerGenerationRun, MakerGridAggregation, MakerGridColumn,
            MakerGridVariant, MakerGridView, MakerProject, MakerRelation,
            MakerScreen, MakerSection, MakerTab, MakerTabGroup, MakerTable)
        return [
            MakerProject, MakerTable, MakerColumn, MakerRelation,
            MakerScreen, MakerTabGroup, MakerTab, MakerSection, MakerFieldPlacement,
            MakerComputedField,
            MakerGridView, MakerGridColumn, MakerGridAggregation, MakerGridVariant,
            MakerGenerationRun
        ]
