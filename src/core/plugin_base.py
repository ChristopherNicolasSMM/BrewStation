"""
Base class for BrewStation plugins.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


class PluginBase(ABC):
    """
    Classe base abstrata para todos os plugins do BrewStation.
    
    Cada plugin deve herdar desta classe e implementar os métodos necessários.
    """
    
    def __init__(self, plugin_path: Path, config: Dict[str, Any]):
        """
        Inicializa o plugin.
        
        Args:
            plugin_path: Caminho do diretório do plugin
            config: Configuração do plugin (do install.json)
        """
        self.plugin_path = Path(plugin_path) if not isinstance(plugin_path, Path) else plugin_path
        self.config = config or {}
        
        # Garantir que todos os valores sejam strings válidas (não None)
        name_val = config.get('name', '') if config else ''
        self.name = str(name_val) if name_val is not None else ''
        
        # Label para exibição no menu (prioridade sobre name)
        label_val = config.get('label', '') if config else ''
        self.label = str(label_val) if label_val is not None else ''
        
        version_val = config.get('version', '1.0.0') if config else '1.0.0'
        self.version = str(version_val) if version_val is not None else '1.0.0'
        
        desc_val = config.get('description', '') if config else ''
        self.description = str(desc_val) if desc_val is not None else ''
        
        author_val = config.get('author', '') if config else ''
        self.author = str(author_val) if author_val is not None else ''
        
        self.dependencies = config.get('dependencies', []) if config else []
        self.menu_config = config.get('menu', {}) if config else {}
        self.is_active = False
        self.is_installed = False
        
    @abstractmethod
    def install(self) -> bool:
        """
        Instala o plugin.
        
        Returns:
            True se a instalação foi bem-sucedida, False caso contrário.
        """
        pass
    
    @abstractmethod
    def uninstall(self) -> bool:
        """
        Desinstala o plugin.
        
        Returns:
            True se a desinstalação foi bem-sucedida, False caso contrário.
        """
        pass
    
    def activate(self) -> bool:
        """
        Ativa o plugin.
        
        Returns:
            True se a ativação foi bem-sucedida, False caso contrário.
        """
        self.is_active = True
        return True
    
    def deactivate(self) -> bool:
        """
        Desativa o plugin.
        
        Returns:
            True se a desativação foi bem-sucedida, False caso contrário.
        """
        self.is_active = False
        return True
    
    @abstractmethod
    def register_routes(self, app) -> List:
        """
        Registra as rotas do plugin na aplicação Flask.
        
        Args:
            app: Instância da aplicação Flask
            
        Returns:
            Lista de blueprints registrados
        """
        pass
    
    @abstractmethod
    def register_models(self) -> List:
        """
        Registra os modelos SQLAlchemy do plugin.
        
        Returns:
            Lista de modelos registrados
        """
        pass
    
    def get_menu_config(self) -> Dict[str, Any]:
        """
        Retorna a configuração de menu do plugin.
        
        Carrega do arquivo menu_config.json se especificado no install.json,
        caso contrário usa a configuração inline do install.json.
        
        Returns:
            Dicionário com configuração de menu
        """
        # Verificar se há caminho para arquivo de menu separado
        menu_config_path = self.config.get('menu_config_path')
        if menu_config_path:
            menu_file = self.plugin_path / menu_config_path
            if menu_file.exists():
                try:
                    import json
                    with open(menu_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erro ao carregar menu_config.json do plugin {self.name}: {e}")
        
        # Fallback para menu inline no install.json
        return self.menu_config
    
    def get_static_folder(self) -> Optional[Path]:
        """
        Retorna o caminho da pasta static do plugin, se existir.
        
        Returns:
            Path da pasta static ou None
        """
        static_path = self.plugin_path / 'static'
        if static_path.exists():
            return static_path
        return None
    
    def get_templates_folder(self) -> Optional[Path]:
        """
        Retorna o caminho da pasta templates do plugin.
        
        Returns:
            Path da pasta templates
        """
        templates_path = self.plugin_path / 'templates'
        if templates_path.exists():
            return templates_path
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o plugin para dicionário.
        
        Returns:
            Dicionário com informações do plugin
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'dependencies': self.dependencies,
            'is_active': self.is_active,
            'is_installed': self.is_installed,
            'menu_config': self.menu_config
        }

