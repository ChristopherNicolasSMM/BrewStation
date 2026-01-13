"""
Exceção e classe para gerenciamento de erros de dependências de plugins.
"""

from typing import List, Dict, Optional


class DependencyStatus:
    """Status de uma dependência."""
    
    def __init__(self, name: str, required_version: Optional[str] = None):
        self.name = name
        self.required_version = required_version
        self.found = False
        self.installed = False
        self.active = False
        self.installed_version: Optional[str] = None
        self.installed_plugin_name: Optional[str] = None  # Nome do diretório do plugin
        self.version_compatible = True
        
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'name': self.name,
            'required_version': self.required_version,
            'found': self.found,
            'installed': self.installed,
            'active': self.active,
            'installed_version': self.installed_version,
            'installed_plugin_name': self.installed_plugin_name,
            'version_compatible': self.version_compatible,
            'status': self.get_status_string()
        }
    
    def get_status_string(self) -> str:
        """Retorna string descritiva do status."""
        if not self.found:
            return "NÃO ENCONTRADO"
        if not self.installed:
            return "NÃO INSTALADO"
        if not self.active:
            return "INSTALADO MAS INATIVO"
        if not self.version_compatible:
            return f"VERSÃO INCOMPATÍVEL (requer {self.required_version}, encontrado {self.installed_version})"
        return "OK"
    
    def is_ok(self) -> bool:
        """Verifica se a dependência está OK (encontrada, instalada e ativa)."""
        return self.found and self.installed and self.active and self.version_compatible


class PluginDependencyError(Exception):
    """
    Exceção lançada quando há problemas com dependências de plugins.
    
    Contém informações detalhadas sobre o status de cada dependência.
    """
    
    def __init__(self, plugin_name: str, dependency_statuses: List[DependencyStatus], message: str = None):
        self.plugin_name = plugin_name
        self.dependency_statuses = dependency_statuses
        self.message = message or self._generate_message()
        super().__init__(self.message)
    
    def _generate_message(self) -> str:
        """Gera mensagem detalhada sobre as dependências."""
        lines = [
            f"Não foi possível instalar o plugin '{self.plugin_name}' devido a problemas com dependências:",
            ""
        ]
        
        for dep_status in self.dependency_statuses:
            status_icon = "✅" if dep_status.is_ok() else "❌"
            version_info = f" (versão {dep_status.required_version} requerida)" if dep_status.required_version else ""
            lines.append(f"{status_icon} {dep_status.name}{version_info}: {dep_status.get_status_string()}")
            
            if dep_status.found and dep_status.installed_plugin_name:
                lines.append(f"   Plugin encontrado: {dep_status.installed_plugin_name}")
                if dep_status.installed_version:
                    lines.append(f"   Versão instalada: {dep_status.installed_version}")
        
        lines.append("")
        lines.append("Todas as dependências devem estar INSTALADAS e ATIVAS para continuar a instalação.")
        
        return "\n".join(lines)
    
    def get_status_dict(self) -> Dict:
        """Retorna dicionário com status das dependências."""
        return {
            'plugin_name': self.plugin_name,
            'dependencies': [dep.to_dict() for dep in self.dependency_statuses],
            'all_ok': all(dep.is_ok() for dep in self.dependency_statuses)
        }
