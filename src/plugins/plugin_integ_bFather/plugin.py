"""
Plugin principal do BrewStation Core.
Contém todas as funcionalidades originais do sistema.
"""

from typing import List

from flask import Blueprint

from core.plugin_base import PluginBase
from db.database import db


class PluginBrewstationCore(PluginBase):
    """
    Plugin core do BrewStation.
    
    Contém todas as funcionalidades principais:
    - Ingredientes (maltes, lúpulos, leveduras)
    - Receitas
    - Estoque
    - Envase
    - Cálculos
    - BrewFather integration
    - Notificações
    - Dispositivos
    """
    
    def install(self) -> bool:
        """Instala o plugin."""
        try:
            # Registrar modelos no banco
            models = self.register_models()
            if models:
                db.create_all()
            
            # Salvar no banco de dados
            from model.plugin import Plugin as PluginModel
            
            plugin_db = PluginModel.query.filter_by(name=self.name).first()
            if not plugin_db:
                plugin_db = PluginModel(
                    name=self.name,
                    version=self.version,
                    description=self.description,
                    author=self.author,
                    is_installed=True,
                    is_active=False,
                    dependencies=self.dependencies,
                    config_json=self.config
                )
                db.session.add(plugin_db)
            else:
                plugin_db.is_installed = True
                plugin_db.version = self.version
            
            db.session.commit()
            return True
        except Exception as e:
            print(f"Erro ao instalar plugin {self.name}: {e}")
            db.session.rollback()
            return False
    
    def uninstall(self) -> bool:
        """Desinstala o plugin."""
        try:
            from model.plugin import Plugin as PluginModel
            
            plugin_db = PluginModel.query.filter_by(name=self.name).first()
            if plugin_db:
                plugin_db.is_installed = False
                plugin_db.is_active = False
                db.session.commit()
            
            return True
        except Exception as e:
            print(f"Erro ao desinstalar plugin {self.name}: {e}")
            db.session.rollback()
            return False
    
    def register_routes(self, app) -> List[Blueprint]:
        """Registra as rotas do plugin."""
        blueprints = []
        
        try:
            # Importar blueprints da API do plugin
            import sys
            from pathlib import Path

            # Adicionar src ao path se necessário
            src_path = Path(__file__).parent.parent.parent
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))
            
            # Importar das rotas do plugin (usando caminho relativo)
            plugin_routes_path = self.plugin_path / 'api' / 'routes'
            if str(plugin_routes_path.parent.parent.parent) not in sys.path:
                sys.path.insert(0, str(plugin_routes_path.parent.parent.parent))
            
            # Importar usando importlib para garantir que funciona
            import importlib.util
            routes_init = plugin_routes_path / '__init__.py'
            if routes_init.exists():
                spec = importlib.util.spec_from_file_location("plugin_api_routes", routes_init)
                routes_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(routes_module)
                
                # Usar all_blueprints se disponível, senão importar individualmente
                if hasattr(routes_module, 'all_blueprints'):
                    blueprints.extend(routes_module.all_blueprints)
                else:
                    # Importar apenas blueprints que existem no plugin
                    ingredientes_bp = routes_module.ingredientes_bp
                    receitas_bp = routes_module.receitas_bp
                    calculos_bp = routes_module.calculos_bp
                    dispositivos_bp = routes_module.dispositivos_bp
                    brewfather_bp = routes_module.brewfather_bp
                    dashboard_bp = routes_module.dashboard_bp
                    envase_bp = routes_module.envase_bp
                    estoque_bp = routes_module.estoque_bp
                    config_bp = routes_module.config_bp
                    
                    blueprints.extend([
                        ingredientes_bp,
                        receitas_bp,
                        calculos_bp,
                        dispositivos_bp,
                        brewfather_bp,
                        dashboard_bp,
                        envase_bp,
                        estoque_bp,
                        config_bp
                    ])
            else:
                # Fallback: importar do local antigo se não encontrar no plugin
                # Nota: upload_bp e notifications_bp são do core, não do plugin
                from api.routes import (brewfather_bp, calculos_bp, config_bp,
                                        dashboard_bp, dispositivos_bp,
                                        envase_bp, estoque_bp, ingredientes_bp,
                                        receitas_bp)
                
                blueprints.extend([
                    ingredientes_bp,
                    receitas_bp,
                    calculos_bp,
                    dispositivos_bp,
                    brewfather_bp,
                    dashboard_bp,
                    envase_bp,
                    estoque_bp,
                    config_bp
                ])
            
            # Importar e registrar rotas web do plugin
            # Importar usando caminho relativo do plugin
            import importlib.util
            routes_path = self.plugin_path / 'controller' / 'routes.py'
            if routes_path.exists():
                spec = importlib.util.spec_from_file_location("plugin_routes", routes_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                web_plugin_bp = module.web_plugin_bp
                blueprints.append(web_plugin_bp)
            
        except ImportError as e:
            # Se não encontrar controller.routes, criar blueprint básico
            from flask import Blueprint
            web_plugin_bp = Blueprint(f'plugin_{self.name}_web', __name__)
            blueprints.append(web_plugin_bp)
        except Exception as e:
            print(f"Erro ao registrar rotas do plugin {self.name}: {e}")
        
        return blueprints
    
    def register_models(self) -> List:
        """Registra os modelos SQLAlchemy do plugin."""
        models = []
        
        try:
            # Importar modelos do próprio plugin primeiro
            try:
                from plugins.plugin_integ_bFather.model.brewfather import (
                    BrewFatherBatch, BrewFatherInventory, BrewFatherRecipe,
                    BrewFatherSync)
                from plugins.plugin_integ_bFather.model.calculo_envase import \
                    CalculoEnvase
                from plugins.plugin_integ_bFather.model.config import \
                    Configuracao
                from plugins.plugin_integ_bFather.model.dispositivos import \
                    Dispositivo
                from plugins.plugin_integ_bFather.model.envase import (
                    Embalagem, Envase, ItemEnvase, TipoEmbalagem)
                from plugins.plugin_integ_bFather.model.estoque import (
                    CustoProducao, EstoqueIngrediente, MovimentacaoEstoque)
                from plugins.plugin_integ_bFather.model.ingredientes import (
                    CalculoPreco, IngredienteReceita, Levedura, Lupulo, Malte,
                    Receita)
                from plugins.plugin_integ_bFather.model.sessao_brasagem import \
                    SessaoBrasagem
            except ImportError:
                # Fallback para modelos em src/model se não existirem no plugin
                from model.brewfather import (BrewFatherBatch,
                                              BrewFatherInventory,
                                              BrewFatherRecipe, BrewFatherSync)
                from model.calculo_envase import CalculoEnvase
                from model.config import Configuracao
                from model.dispositivos import Dispositivo
                from model.envase import (Embalagem, Envase, ItemEnvase,
                                          TipoEmbalagem)
                from model.estoque import (CustoProducao, EstoqueIngrediente,
                                           MovimentacaoEstoque)
                from model.ingredientes import (CalculoPreco,
                                                IngredienteReceita, Levedura,
                                                Lupulo, Malte, Receita)
                from model.sessao_brasagem import SessaoBrasagem
            
            models.extend([
                Malte, Lupulo, Levedura, Receita, IngredienteReceita, CalculoPreco,
                MovimentacaoEstoque, EstoqueIngrediente, CustoProducao,
                BrewFatherRecipe, BrewFatherBatch, BrewFatherInventory, BrewFatherSync,
                Envase, TipoEmbalagem, Embalagem, ItemEnvase,
                CalculoEnvase,
                Configuracao,
                Dispositivo,
                SessaoBrasagem
            ])
            
        except ImportError as e:
            print(f"Erro ao importar modelos do plugin {self.name}: {e}")
        
        return models

