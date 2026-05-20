"""
Plugin loader for dynamic plugin discovery and loading.
"""

import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from .plugin_base import PluginBase

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Carregador de plugins dinâmico.
    
    Responsável por descobrir, carregar e instanciar plugins.
    """
    
    def __init__(self, plugins_dir: Path):
        """
        Inicializa o carregador.
        
        Args:
            plugins_dir: Diretório onde os plugins estão localizados
        """
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, PluginBase] = {}
        
    def discover_plugins(self) -> List[str]:
        """
        Descobre plugins disponíveis no diretório.
        
        Returns:
            Lista de nomes de plugins encontrados
        """
        plugins = []
        
        if not self.plugins_dir.exists():
            logger.warning(f"Diretório de plugins não existe: {self.plugins_dir}")
            return plugins
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                install_json = plugin_dir / 'install.json'
                plugin_py = plugin_dir / 'plugin.py'
                
                if install_json.exists() and plugin_py.exists():
                    plugins.append(plugin_dir.name)
                    logger.info(f"Plugin descoberto: {plugin_dir.name}")
        
        return plugins
    
    def load_plugin_config(self, plugin_name: str) -> Optional[Dict]:
        """
        Carrega a configuração de um plugin (install.json).
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            Dicionário com configuração ou None se não encontrado
        """
        plugin_dir = self.plugins_dir / plugin_name
        install_json = plugin_dir / 'install.json'
        
        if not install_json.exists():
            logger.error(f"install.json não encontrado para plugin: {plugin_name}")
            return None
        
        try:
            with open(install_json, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Erro ao carregar install.json do plugin {plugin_name}: {e}")
            return None
    
    def load_plugin_class(self, plugin_name: str) -> Optional[Type[PluginBase]]:
        """
        Carrega a classe do plugin dinamicamente.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            Classe do plugin ou None se não encontrado
        """
        self.plugins_dir / plugin_name
        plugin_module_path = f"plugins.{plugin_name}.plugin"
        
        try:
            # Adicionar o diretório src ao path se necessário
            if str(self.plugins_dir.parent) not in sys.path:
                sys.path.insert(0, str(self.plugins_dir.parent))
            
            # Importar o módulo do plugin
            module = importlib.import_module(plugin_module_path)
            
            # Procurar pela classe do plugin
            # Tenta diferentes padrões de nome de classe
            possible_names = [
                # Padrão: Plugin<nome> (ex: PluginBrewstationCore)
                f"Plugin{plugin_name.replace('_', '').title().replace('-', '')}",
                # Padrão: Plugin<nome_camelcase> (ex: PluginIntegBrewFather)
                f"Plugin{plugin_name.replace('plugin_', '').replace('_', ' ').title().replace(' ', '')}",
                # Padrão direto: brewstation_core -> PluginBrewstationCore
                f"Plugin{''.join(word.capitalize() for word in plugin_name.split('_'))}"
            ]
            
            plugin_class_name = None
            for name in possible_names:
                if hasattr(module, name):
                    plugin_class_name = name
                    break
            
            # Tentar encontrar a classe
            if plugin_class_name and hasattr(module, plugin_class_name):
                return getattr(module, plugin_class_name)
            
            # Se não encontrar, procurar por qualquer classe que herde de PluginBase
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginBase) and 
                    attr != PluginBase):
                    return attr
            
            logger.error(f"Classe do plugin não encontrada em {plugin_module_path}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao carregar classe do plugin {plugin_name}: {e}")
            return None
    
    def load_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """
        Carrega e instancia um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            Instância do plugin ou None se não foi possível carregar
        """
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name]
        
        # Carregar configuração
        config = self.load_plugin_config(plugin_name)
        if not config or not isinstance(config, dict):
            logger.error(f"Configuração inválida para plugin {plugin_name}")
            return None
        
        # Garantir que config tenha valores padrão
        config = config.copy() if config else {}
        if 'name' not in config or config.get('name') is None:
            config['name'] = plugin_name
        if 'version' not in config or config.get('version') is None:
            config['version'] = '1.0.0'
        if 'description' not in config:
            config['description'] = ''
        if 'author' not in config:
            config['author'] = ''
        if 'dependencies' not in config:
            config['dependencies'] = []
        if 'menu' not in config:
            config['menu'] = {}
        
        # Carregar classe
        plugin_class = self.load_plugin_class(plugin_name)
        if not plugin_class:
            return None
        
        # Instanciar plugin
        plugin_dir = self.plugins_dir / plugin_name
        try:
            plugin_instance = plugin_class(plugin_dir, config)
            self.loaded_plugins[plugin_name] = plugin_instance
            logger.info(f"Plugin carregado com sucesso: {plugin_name}")
            return plugin_instance
        except Exception as e:
            logger.error(f"Erro ao instanciar plugin {plugin_name}: {e}", exc_info=True)
            return None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Descarrega um plugin da memória.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se descarregado com sucesso
        """
        if plugin_name in self.loaded_plugins:
            del self.loaded_plugins[plugin_name]
            logger.info(f"Plugin descarregado: {plugin_name}")
            return True
        return False

