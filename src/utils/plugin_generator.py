"""
Gerador de templates de plugins para o BrewStation.
"""

import json
from pathlib import Path
from typing import Optional


class PluginGenerator:
    """Gera estrutura de plugin template."""
    
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
    
    def create_plugin_template(
        self,
        plugin_name: str,
        menu_label: str,
        description: Optional[str] = None,
        author: Optional[str] = None,
        version: str = "1.0.0"
    ) -> bool:
        """
        Cria um plugin template completo.
        
        Args:
            plugin_name: Nome do plugin (diretório)
            menu_label: Nome exibido no menu
            description: Descrição do plugin
            author: Autor do plugin
            version: Versão do plugin
            
        Returns:
            True se criado com sucesso, False caso contrário
        """
        try:
            prefix = "plugin_"
            plugin_path = self.plugins_dir / f"{prefix}{plugin_name}"
            
            # Verificar se já existe
            if plugin_path.exists():
                print(f"❌ Erro: Plugin '{plugin_name}' já existe em {plugin_path}")
                return False
            
            # Criar estrutura de diretórios
            plugin_path.mkdir(parents=True, exist_ok=True)
            (plugin_path / "api" / "routes").mkdir(parents=True, exist_ok=True)
            (plugin_path / "controller").mkdir(parents=True, exist_ok=True)
            (plugin_path / "templates").mkdir(parents=True, exist_ok=True)
            (plugin_path / "model").mkdir(parents=True, exist_ok=True)
            (plugin_path / "utils").mkdir(parents=True, exist_ok=True)
            (plugin_path / "logs").mkdir(parents=True, exist_ok=True)
            
            # Criar install.json
            self._create_install_json(
                plugin_path,
                plugin_name,
                menu_label,
                description or f"Plugin {menu_label}",
                author or "BrewStation User",
                version
            )
            
            # Criar menu_config.json
            self._create_menu_config(plugin_path, plugin_name, menu_label)
            
            # Criar plugin.py
            self._create_plugin_py(plugin_path, plugin_name, menu_label)
            
            # Criar __init__.py do plugin
            self._create_plugin_init(plugin_path, plugin_name)
            
            # Criar rotas API
            self._create_api_routes(plugin_path, plugin_name)
            
            # Criar rotas web
            self._create_web_routes(plugin_path, plugin_name, menu_label)
            
            # Criar template HTML
            self._create_template_html(plugin_path, plugin_name, menu_label)
            
            print(f"✅ Plugin '{plugin_name}' criado com sucesso!")
            print(f"📁 Localização: {plugin_path}")
            print(f"\n📝 Próximos passos:")
            print(f"   1. Instalar: python run.py plugin -i {plugin_name}")
            print(f"   2. Ativar: python run.py plugin -a {plugin_name}")
            print(f"   3. Acessar: http://localhost:5000/{plugin_name.lower()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar plugin: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_install_json(
        self,
        plugin_path: Path,
        plugin_name: str,
        menu_label: str,
        description: str,
        author: str,
        version: str
    ):
        """Cria o arquivo install.json."""
        install_data = {
            "name": plugin_name,
            "label": menu_label,
            "version": version,
            "description": description,
            "author": author,
            "menu_config_path": "menu_config.json",
            "dependencies": [],
            "db_models": []
        }
        
        install_file = plugin_path / "install.json"
        with open(install_file, 'w', encoding='utf-8') as f:
            json.dump(install_data, f, indent=2, ensure_ascii=False)
    
    def _create_menu_config(self, plugin_path: Path, plugin_name: str, menu_label: str):
        """Cria o arquivo menu_config.json."""
        # Criar nome de blueprint baseado no nome do plugin
        blueprint_name = f"plugin_{plugin_name.lower().replace('-', '_')}_web"
        
        menu_data = {
            "main_items": [
                {
                    "id": plugin_name.lower().replace('-', '_'),
                    "label": menu_label,
                    "icon": "bi bi-puzzle",
                    "url": f"{blueprint_name}.index"
                }
            ]
        }
        
        menu_file = plugin_path / "menu_config.json"
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(menu_data, f, indent=2, ensure_ascii=False)
    
    def _create_plugin_py(self, plugin_path: Path, plugin_name: str, menu_label: str):
        """Cria o arquivo plugin.py."""
        class_name = self._to_class_name(plugin_name)
        
        plugin_code = f'''"""
Plugin {menu_label}.
Plugin gerado automaticamente pelo PluginGenerator.
"""

from pathlib import Path
from typing import List
from flask import Blueprint

from core.plugin_base import PluginBase
from db.database import db


class {class_name}(PluginBase):
    """
    Plugin {menu_label}.
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
                plugin_db.description = self.description
                plugin_db.author = self.author
            
            db.session.commit()
            return True
        except Exception as e:
            print(f"Erro ao instalar plugin {{self.name}}: {{e}}")
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
            print(f"Erro ao desinstalar plugin {{self.name}}: {{e}}")
            db.session.rollback()
            return False
    
    def register_routes(self, app) -> List[Blueprint]:
        """Registra as rotas do plugin."""
        # O sistema descobre automaticamente rotas em api/routes/ e controller/routes.py
        return []
    
    def register_models(self) -> List:
        """Registra os modelos SQLAlchemy do plugin."""
        # Adicionar modelos aqui quando necessário
        return []
'''
        
        plugin_file = plugin_path / "plugin.py"
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(plugin_code)
    
    def _create_plugin_init(self, plugin_path: Path, plugin_name: str):
        """Cria o __init__.py do plugin."""
        class_name = self._to_class_name(plugin_name)
        
        init_code = f'''"""
Plugin {plugin_name}.
"""

from .plugin import {class_name}

__all__ = ['{class_name}']
'''
        
        init_file = plugin_path / "__init__.py"
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_code)
    
    def _create_api_routes(self, plugin_path: Path, plugin_name: str):
        """Cria rotas API de exemplo."""
        route_name = plugin_name.lower().replace('-', '_')
        blueprint_name = f"plugin_{route_name}_api"
        
        # Criar rota API de exemplo
        api_route_code = f'''"""
Rotas API do plugin {plugin_name}.
"""

from flask import Blueprint, jsonify
from flask_login import login_required

{blueprint_name} = Blueprint('{blueprint_name}', __name__)


@{blueprint_name}.route('/{route_name}/info', methods=['GET'])
@login_required
def get_info():
    """Retorna informações do plugin."""
    return jsonify({{
        'name': '{plugin_name}',
        'status': 'active',
        'message': 'Plugin funcionando corretamente!'
    }}), 200
'''
        
        api_file = plugin_path / "api" / "routes" / f"{route_name}_routes.py"
        with open(api_file, 'w', encoding='utf-8') as f:
            f.write(api_route_code)
        
        # Criar __init__.py das rotas API
        api_init_code = f'''"""
Rotas API do plugin {plugin_name}.
"""

from .{route_name}_routes import {blueprint_name}

all_blueprints = [{blueprint_name}]
'''
        
        api_init_file = plugin_path / "api" / "routes" / "__init__.py"
        with open(api_init_file, 'w', encoding='utf-8') as f:
            f.write(api_init_code)
        
        # Criar __init__.py do api
        api_dir_init = plugin_path / "api" / "__init__.py"
        api_dir_init.touch()
    
    def _create_web_routes(self, plugin_path: Path, plugin_name: str, menu_label: str):
        """Cria rotas web de exemplo."""
        route_name = plugin_name.lower().replace('-', '_')
        blueprint_name = f"plugin_{route_name}_web"
        
        routes_code = f'''"""
Rotas web do plugin {plugin_name}.
"""

from flask import Blueprint, render_template
from flask_login import login_required
from pathlib import Path

{blueprint_name} = Blueprint('{blueprint_name}', __name__)


def render_plugin_template(template_name: str, **context):
    """Renderiza template do plugin."""
    return render_template(template_name, **context)


@{blueprint_name}.route("/{route_name}")
@login_required
def index():
    """Página principal do plugin."""
    return render_plugin_template("{plugin_name.lower()}.html")
'''
        
        routes_file = plugin_path / "controller" / "routes.py"
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(routes_code)
    
    def _create_template_html(self, plugin_path: Path, plugin_name: str, menu_label: str):
        """Cria template HTML de exemplo."""
        # Escapar chaves para Jinja2: {{ para escapar { em f-strings
        template_code = f'''{{% extends "base.html" %}}

{{% block title %}}{menu_label}{{% endblock %}}

{{% block content %}}
<div class="pagetitle">
    <h1>{menu_label}</h1>
    <nav>
        <ol class="breadcrumb">
            <li class="breadcrumb-item"><a href="{{{{ url_for('web.index') }}}}">Home</a></li>
            <li class="breadcrumb-item active">{menu_label}</li>
        </ol>
    </nav>
</div>

<section class="section">
    <div class="row">
        <div class="col-lg-12">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{menu_label}</h5>
                    <p class="card-text">
                        Este é um plugin template gerado automaticamente.
                        Edite este arquivo para personalizar a página do plugin.
                    </p>
                    <button class="btn btn-primary" onclick="testApi()">Testar API</button>
                    <div id="api-result" class="mt-3"></div>
                </div>
            </div>
        </div>
    </div>
</section>

<script>
function testApi() {{
    fetch('/api/{plugin_name.lower().replace('-', '_')}/info')
        .then(response => response.json())
        .then(data => {{
            document.getElementById('api-result').innerHTML = 
                '<div class="alert alert-success"><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
        }})
        .catch(error => {{
            document.getElementById('api-result').innerHTML = 
                '<div class="alert alert-danger">Erro: ' + error + '</div>';
        }});
}}
</script>
{{% endblock %}}
'''
        
        template_file = plugin_path / "templates" / f"{plugin_name.lower()}.html"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_code)
    
    def _to_class_name(self, name: str) -> str:
        """Converte nome do plugin para nome de classe Python."""
        # Remove caracteres especiais e converte para PascalCase
        parts = name.replace('-', '_').replace(' ', '_').split('_')
        return ''.join(word.capitalize() for word in parts if word) + 'Plugin'

