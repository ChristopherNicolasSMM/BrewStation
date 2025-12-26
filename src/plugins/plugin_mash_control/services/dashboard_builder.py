"""
Serviço de construção de dashboards.

Gerencia layouts SVG, posicionamento de elementos e vinculação com dispositivos.
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path

from flask import current_app
from db.database import db

from plugins.plugin_mash_control.utils.model_loader import get_dashboard_layout

logger = logging.getLogger(__name__)


class DashboardBuilderService:
    """
    Serviço para gerenciamento de layouts de dashboard.
    
    Gerencia criação, carregamento e salvamento de layouts SVG,
    posicionamento de elementos e vinculação com dispositivos reais.
    """
    
    def __init__(self, plugin_path: Path):
        """
        Inicializa o serviço de construção de dashboards.
        
        Args:
            plugin_path: Caminho do diretório do plugin
        """
        self.plugin_path = plugin_path
        self.dashboards_path = plugin_path / "data" / "dashboards"
        self.dashboards_path.mkdir(parents=True, exist_ok=True)
    
    def load_layout(self, layout_id: str) -> Optional[Dict[str, Any]]:
        """
        Carrega um layout salvo.
        
        Args:
            layout_id: ID do layout
            
        Returns:
            Dados do layout ou None se não encontrado
        """
        try:
            DashboardLayout = get_dashboard_layout()
            if not DashboardLayout:
                return None
            
            layout = DashboardLayout.query.get(layout_id)
            if not layout:
                return None
            
            return layout.to_dict()
        except Exception as e:
            logger.error(f"Erro ao carregar layout {layout_id}: {e}", exc_info=True)
            return None
    
    def save_layout(self, layout_data: Dict[str, Any], user_id: Optional[int] = None, is_default: bool = False) -> Optional[str]:
        """
        Salva um layout.
        
        Args:
            layout_data: Dados do layout (elementos SVG, posicionamento, etc.)
            user_id: ID do usuário (opcional)
            is_default: Se True, marca como layout padrão do usuário
            
        Returns:
            ID do layout salvo ou None em caso de erro
        """
        try:
            DashboardLayout = get_dashboard_layout()
            if not DashboardLayout:
                return None
            
            # Se for padrão, remover outros layouts padrão do usuário
            if is_default and user_id:
                existing_defaults = DashboardLayout.query.filter_by(
                    user_id=user_id,
                    is_default=True
                ).all()
                for layout in existing_defaults:
                    layout.is_default = False
                db.session.commit()
            
            layout_id = layout_data.get('id') or str(uuid.uuid4())
            
            layout = DashboardLayout.query.get(layout_id)
            if layout:
                # Atualizar layout existente
                layout.name = layout_data.get('name', layout.name)
                layout.layout_data = json.dumps(layout_data.get('elements', []))
                layout.is_default = is_default
                layout.user_id = user_id or layout.user_id
            else:
                # Criar novo layout
                layout = DashboardLayout(
                    id=layout_id,
                    name=layout_data.get('name', 'Novo Layout'),
                    user_id=user_id,
                    layout_data=json.dumps(layout_data.get('elements', [])),
                    is_default=is_default
                )
                db.session.add(layout)
            
            db.session.commit()
            logger.info(f"Layout {layout_id} salvo")
            return layout_id
        except Exception as e:
            logger.error(f"Erro ao salvar layout: {e}", exc_info=True)
            db.session.rollback()
            return None
    
    def get_default_layout(self, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Obtém layout padrão do usuário.
        
        Args:
            user_id: ID do usuário (opcional)
            
        Returns:
            Dados do layout padrão ou None se não encontrado
        """
        try:
            DashboardLayout = get_dashboard_layout()
            if not DashboardLayout:
                return None
            
            query = DashboardLayout.query.filter_by(is_default=True)
            if user_id:
                query = query.filter_by(user_id=user_id)
            else:
                query = query.filter_by(user_id=None)
            
            layout = query.first()
            if layout:
                return layout.to_dict()
            
            return None
        except Exception as e:
            logger.error(f"Erro ao obter layout padrão: {e}", exc_info=True)
            return None
    
    def create_element(self, element_type: str, position: Dict[str, float], device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Cria um novo elemento SVG.
        
        Args:
            element_type: Tipo do elemento (kettle, pump, valve, sensor, etc.)
            position: Posição {x, y}
            device_id: ID do dispositivo vinculado (opcional)
            
        Returns:
            Dados do elemento criado
        """
        element = {
            'id': str(uuid.uuid4()),
            'type': element_type,
            'x': position.get('x', 0),
            'y': position.get('y', 0),
            'device_id': device_id,
            'properties': self._get_default_properties(element_type)
        }
        
        return element
    
    def update_element_position(self, element_id: str, layout_id: str, x: float, y: float) -> bool:
        """
        Atualiza posição de um elemento.
        
        Args:
            element_id: ID do elemento
            layout_id: ID do layout
            x: Nova coordenada X
            y: Nova coordenada Y
            
        Returns:
            True se posição foi atualizada
        """
        try:
            DashboardLayout = get_dashboard_layout()
            if not DashboardLayout:
                return False
            
            layout = DashboardLayout.query.get(layout_id)
            if not layout:
                return False
            
            layout_dict = layout.to_dict()
            elements = layout_dict.get('layout_data', [])
            
            for element in elements:
                if element.get('id') == element_id:
                    element['x'] = x
                    element['y'] = y
                    break
            
            layout.layout_data = json.dumps(elements)
            db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar posição do elemento: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def link_element_to_device(self, element_id: str, layout_id: str, device_id: str) -> bool:
        """
        Vincula um elemento SVG a um dispositivo real.
        
        Args:
            element_id: ID do elemento
            layout_id: ID do layout
            device_id: ID do dispositivo
            
        Returns:
            True se vinculação foi bem-sucedida
        """
        try:
            DashboardLayout = get_dashboard_layout()
            if not DashboardLayout:
                return False
            
            layout = DashboardLayout.query.get(layout_id)
            if not layout:
                return False
            
            layout_dict = layout.to_dict()
            elements = layout_dict.get('layout_data', [])
            
            for element in elements:
                if element.get('id') == element_id:
                    element['device_id'] = device_id
                    break
            
            layout.layout_data = json.dumps(elements)
            db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao vincular elemento a dispositivo: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def get_svg_components(self) -> List[Dict[str, Any]]:
        """
        Retorna biblioteca de componentes SVG disponíveis.
        
        Returns:
            Lista de componentes disponíveis
        """
        return [
            {
                'type': 'kettle',
                'name': 'Panela',
                'icon': 'bi bi-circle',
                'default_size': {'width': 100, 'height': 120}
            },
            {
                'type': 'mash_tun',
                'name': 'Tunel de Mostura',
                'icon': 'bi bi-square',
                'default_size': {'width': 120, 'height': 150}
            },
            {
                'type': 'pump',
                'name': 'Bomba',
                'icon': 'bi bi-arrow-repeat',
                'default_size': {'width': 60, 'height': 60}
            },
            {
                'type': 'valve',
                'name': 'Válvula',
                'icon': 'bi bi-circle-half',
                'default_size': {'width': 40, 'height': 40}
            },
            {
                'type': 'sensor',
                'name': 'Sensor',
                'icon': 'bi bi-thermometer',
                'default_size': {'width': 30, 'height': 30}
            },
            {
                'type': 'heater',
                'name': 'Aquecedor',
                'icon': 'bi bi-fire',
                'default_size': {'width': 50, 'height': 50}
            },
            {
                'type': 'chiller',
                'name': 'Resfriador',
                'icon': 'bi bi-snow',
                'default_size': {'width': 50, 'height': 50}
            }
        ]
    
    def _get_default_properties(self, element_type: str) -> Dict[str, Any]:
        """Retorna propriedades padrão para um tipo de elemento."""
        defaults = {
            'kettle': {
                'fill_color': '#4CAF50',
                'show_temp': True,
                'show_level': True
            },
            'mash_tun': {
                'fill_color': '#2196F3',
                'show_temp': True,
                'show_level': True
            },
            'pump': {
                'fill_color': '#FF9800',
                'show_status': True
            },
            'valve': {
                'fill_color': '#9E9E9E',
                'show_status': True
            },
            'sensor': {
                'fill_color': '#F44336',
                'show_value': True
            },
            'heater': {
                'fill_color': '#FF5722',
                'show_status': True
            },
            'chiller': {
                'fill_color': '#00BCD4',
                'show_status': True
            }
        }
        
        return defaults.get(element_type, {})

