"""
CLI commands para gerenciamento de plugins.
"""

from pathlib import Path

import click
from flask.cli import AppGroup, with_appcontext

from core.plugin_dependency_error import PluginDependencyError
from core.plugin_manager import PluginManager


def register_plugin_commands(app):
    """Registra comandos CLI para plugins."""
    
    plugin_group = AppGroup('plugin', help='Comandos para gerenciar plugins')
    
    @plugin_group.command("list")
    @with_appcontext
    def list_plugins():
        """Lista todos os plugins disponíveis."""
        # Detectar se estamos em src/ ou na raiz
        current_dir = Path.cwd()
        if current_dir.name == 'src':
            plugins_dir = Path("plugins")
            config_file = Path("plugins/plugins.json")
        else:
            plugins_dir = Path("src/plugins")
            config_file = Path("src/plugins/plugins.json")
        
        manager = PluginManager(app, plugins_dir, config_file)
        plugins = manager.get_all_plugins()
        
        click.echo("\nPlugins disponíveis:")
        click.echo("-" * 80)
        
        for name, plugin in plugins.items():
            status = []
            if plugin.is_installed:
                status.append("INSTALADO")
            if plugin.is_active:
                status.append("ATIVO")
            
            status_str = ", ".join(status) if status else "NÃO INSTALADO"
            
            click.echo(f"\n{name} v{plugin.version}")
            click.echo(f"  Descrição: {plugin.description}")
            click.echo(f"  Autor: {plugin.author}")
            click.echo(f"  Status: {status_str}")
            if plugin.dependencies:
                click.echo(f"  Dependências: {', '.join(plugin.dependencies)}")
        
        click.echo("\n" + "-" * 80)
    
    @plugin_group.command("discover")
    @with_appcontext
    def discover_plugins():
        """Descobre novos plugins no diretório."""
        # Detectar se estamos em src/ ou na raiz
        current_dir = Path.cwd()
        if current_dir.name == 'src':
            plugins_dir = Path("plugins")
            config_file = Path("plugins/plugins.json")
        else:
            plugins_dir = Path("src/plugins")
            config_file = Path("src/plugins/plugins.json")
        
        manager = PluginManager(app, plugins_dir, config_file)
        discovered = manager.loader.discover_plugins()
        
        click.echo(f"\nPlugins descobertos: {len(discovered)}")
        for name in discovered:
            click.echo(f"  - {name}")
    
    @plugin_group.command("install")
    @click.argument("plugin_name")
    @with_appcontext
    def install_plugin(plugin_name):
        """Instala um plugin."""
        # Detectar se estamos em src/ ou na raiz
        current_dir = Path.cwd()
        if current_dir.name == 'src':
            plugins_dir = Path("plugins")
            config_file = Path("plugins/plugins.json")
        else:
            plugins_dir = Path("src/plugins")
            config_file = Path("src/plugins/plugins.json")
        
        manager = PluginManager(app, plugins_dir, config_file)
        
        try:
            if manager.install_plugin(plugin_name, raise_on_error=True):
                click.echo(f"✅ Plugin '{plugin_name}' instalado com sucesso!")
            else:
                click.echo(f"❌ Erro ao instalar plugin '{plugin_name}'", err=True)
        except PluginDependencyError as e:
            click.echo(e.message, err=True)
            click.echo("", err=True)
            click.echo("Ação sugerida:", err=True)
            click.echo("1. Instale todas as dependências faltantes", err=True)
            click.echo("2. Ative todas as dependências instaladas mas inativas", err=True)
            click.echo("3. Tente instalar o plugin novamente", err=True)
    
    @plugin_group.command("uninstall")
    @click.argument("plugin_name")
    @with_appcontext
    def uninstall_plugin(plugin_name):
        """Desinstala um plugin."""
        # Detectar se estamos em src/ ou na raiz
        current_dir = Path.cwd()
        if current_dir.name == 'src':
            plugins_dir = Path("plugins")
            config_file = Path("plugins/plugins.json")
        else:
            plugins_dir = Path("src/plugins")
            config_file = Path("src/plugins/plugins.json")
        
        manager = PluginManager(app, plugins_dir, config_file)
        
        if manager.uninstall_plugin(plugin_name):
            click.echo(f"✅ Plugin '{plugin_name}' desinstalado com sucesso!")
        else:
            click.echo(f"❌ Erro ao desinstalar plugin '{plugin_name}'", err=True)
    
    @plugin_group.command("activate")
    @click.argument("plugin_name")
    @with_appcontext
    def activate_plugin(plugin_name):
        """Ativa um plugin."""
        # Detectar se estamos em src/ ou na raiz
        current_dir = Path.cwd()
        if current_dir.name == 'src':
            plugins_dir = Path("plugins")
            config_file = Path("plugins/plugins.json")
        else:
            plugins_dir = Path("src/plugins")
            config_file = Path("src/plugins/plugins.json")
        
        manager = PluginManager(app, plugins_dir, config_file)
        
        if manager.activate_plugin(plugin_name):
            click.echo(f"✅ Plugin '{plugin_name}' ativado com sucesso!")
        else:
            click.echo(f"❌ Erro ao ativar plugin '{plugin_name}'", err=True)
    
    @plugin_group.command("deactivate")
    @click.argument("plugin_name")
    @with_appcontext
    def deactivate_plugin(plugin_name):
        """Desativa um plugin."""
        # Detectar se estamos em src/ ou na raiz
        current_dir = Path.cwd()
        if current_dir.name == 'src':
            plugins_dir = Path("plugins")
            config_file = Path("plugins/plugins.json")
        else:
            plugins_dir = Path("src/plugins")
            config_file = Path("src/plugins/plugins.json")
        
        manager = PluginManager(app, plugins_dir, config_file)
        
        if manager.deactivate_plugin(plugin_name):
            click.echo(f"✅ Plugin '{plugin_name}' desativado com sucesso!")
        else:
            click.echo(f"❌ Erro ao desativar plugin '{plugin_name}'", err=True)
    
    @plugin_group.command("info")
    @click.argument("plugin_name")
    @with_appcontext
    def plugin_info(plugin_name):
        """Mostra informações detalhadas de um plugin."""
        # Detectar se estamos em src/ ou na raiz
        current_dir = Path.cwd()
        if current_dir.name == 'src':
            plugins_dir = Path("plugins")
            config_file = Path("plugins/plugins.json")
        else:
            plugins_dir = Path("src/plugins")
            config_file = Path("src/plugins/plugins.json")
        
        manager = PluginManager(app, plugins_dir, config_file)
        plugin = manager.get_plugin(plugin_name)
        
        if not plugin:
            click.echo(f"❌ Plugin '{plugin_name}' não encontrado", err=True)
            return
        
        click.echo(f"\nInformações do plugin: {plugin_name}")
        click.echo("-" * 80)
        click.echo(f"Versão: {plugin.version}")
        click.echo(f"Descrição: {plugin.description}")
        click.echo(f"Autor: {plugin.author}")
        click.echo(f"Instalado: {'Sim' if plugin.is_installed else 'Não'}")
        click.echo(f"Ativo: {'Sim' if plugin.is_active else 'Não'}")
        
        if plugin.dependencies:
            click.echo(f"Dependências: {', '.join(plugin.dependencies)}")
        
        click.echo(f"\nCaminho: {plugin.plugin_path}")
        click.echo("-" * 80)
    
    app.cli.add_command(plugin_group)
