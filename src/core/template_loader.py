"""
Custom Jinja2 template loader for plugins.
"""

import logging
from pathlib import Path
from typing import List

from jinja2 import BaseLoader, TemplateNotFound

logger = logging.getLogger(__name__)


class PluginTemplateLoader(BaseLoader):
    """
    Jinja2 loader customizado para carregar templates de plugins.
    
    Escaneia os diretórios de templates de todos os plugins ativos.
    """
    
    def __init__(self, plugins_dir: Path, active_plugins: List[str]):
        """
        Inicializa o loader.
        
        Args:
            plugins_dir: Diretório onde os plugins estão localizados
            active_plugins: Lista de nomes de plugins ativos
        """
        self.plugins_dir = Path(plugins_dir)
        self.active_plugins = active_plugins
        self._template_paths = self._build_template_paths()
    
    def _build_template_paths(self) -> List[Path]:
        """
        Constrói lista de caminhos de templates dos plugins ativos.
        
        Returns:
            Lista de caminhos de templates
        """
        paths = []
        
        # Adicionar templates do core primeiro (fallback)
        # Tentar caminho relativo primeiro (quando executado de src/)
        core_templates = Path("templates")
        if not core_templates.exists():
            # Se não encontrar, tentar caminho absoluto (quando executado de raiz)
            core_templates = Path("src/templates")
        if core_templates.exists() and core_templates.is_dir():
            paths.append(core_templates)
            logger.debug(f"Template path do core adicionado: {core_templates}")
        
        # Adicionar templates dos plugins
        for plugin_name in self.active_plugins:
            plugin_templates = self.plugins_dir / plugin_name / 'templates'
            if plugin_templates.exists() and plugin_templates.is_dir():
                paths.append(plugin_templates)
                logger.debug(f"Template path do plugin adicionado: {plugin_templates}")
        
        return paths
    
    def get_source(self, environment, template):
        """
        Carrega o source de um template.
        
        Args:
            environment: Ambiente Jinja2
            template: Nome do template
            
        Returns:
            Tupla (source, filename, uptodate)
            
        Raises:
            TemplateNotFound: Se o template não for encontrado
        """
        for template_path in self._template_paths:
            template_file = template_path / template
            
            if template_file.exists() and template_file.is_file():
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        source = f.read()
                    
                    mtime = template_file.stat().st_mtime
                    
                    def uptodate():
                        try:
                            return template_file.stat().st_mtime == mtime
                        except OSError:
                            return False
                    
                    return source, str(template_file), uptodate
                except Exception as e:
                    logger.error(f"Erro ao ler template {template_file}: {e}")
                    raise TemplateNotFound(template)
        
        raise TemplateNotFound(template)
    
    def list_templates(self) -> List[str]:
        """
        Lista todos os templates disponíveis.
        
        Returns:
            Lista de nomes de templates
        """
        templates = []
        
        for template_path in self._template_paths:
            if template_path.exists():
                for template_file in template_path.rglob('*.html'):
                    # Relativizar o caminho
                    rel_path = template_file.relative_to(template_path)
                    templates.append(str(rel_path).replace('\\', '/'))
        
        return sorted(set(templates))

