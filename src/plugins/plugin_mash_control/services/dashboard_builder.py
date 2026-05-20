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

MAX_LAYOUTS_PER_USER = 10


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

            layout = db.session.query(DashboardLayout).filter_by(id=layout_id).first()
            if not layout:
                return None

            layout_dict = layout.to_dict()
            # Garantir que layout_data seja uma lista de elementos
            layout_data = layout_dict.get('layout_data')
            if isinstance(layout_data, str):
                try:
                    layout_data = json.loads(layout_data)
                except (json.JSONDecodeError, TypeError):
                    layout_data = []
            elif layout_data is None:
                layout_data = []
            elif not isinstance(layout_data, list):
                layout_data = []
            
            # Garantir que temos elements no formato correto
            layout_dict['elements'] = layout_data
            
            # Remover layout_data se existir para evitar confusão
            if 'layout_data' in layout_dict:
                del layout_dict['layout_data']
            
            return layout_dict
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
            
            # Verificar limite de dashboards por usuário
            if not layout_data.get('id'):
                user_layouts_count = DashboardLayout.query.filter_by(user_id=user_id).count()
                if user_layouts_count >= MAX_LAYOUTS_PER_USER:
                    logger.warning(f"Usuário {user_id} já tem 10 dashboards, não é possível criar mais")
                    return None
            
            # Se não houver ID e não for especificado como padrão, verificar se deve ser padrão
            layout_id = layout_data.get('id')
            if not layout_id:
                # Se não há layout padrão para o usuário, tornar este padrão
                if not is_default:
                    query = DashboardLayout.query.filter_by(is_default=True)
                    if user_id:
                        query = query.filter_by(user_id=user_id)
                    else:
                        query = query.filter_by(user_id=None)
                    if not query.first():
                        is_default = True
                layout_id = str(uuid.uuid4())
            
            # Se for padrão, remover outros layouts padrão do usuário
            if is_default:
                query = DashboardLayout.query.filter_by(is_default=True)
                if user_id:
                    query = query.filter_by(user_id=user_id)
                else:
                    query = query.filter_by(user_id=None)
                existing_defaults = query.all()
                for layout in existing_defaults:
                    if layout.id != layout_id:  # Não remover o próprio layout
                        layout.is_default = False
                db.session.commit()
            
            layout = DashboardLayout.query.get(layout_id) if layout_id else None
            
            if layout:
                # Atualizar layout existente
                layout.name = layout_data.get('name', layout.name)
                layout.layout_data = json.dumps(layout_data.get('elements', []))
                layout.is_default = is_default
                layout.user_id = user_id or layout.user_id
                logger.info(f"Atualizando layout existente: {layout_id}")
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
                logger.info(f"Criando novo layout: {layout_id}")
            
            try:
                db.session.commit()
                logger.info(f"Layout {layout_id} salvo com sucesso")
                return layout_id
            except Exception as e:
                logger.error(f"Erro ao commitar layout: {e}", exc_info=True)
                db.session.rollback()
                raise
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
                layout_dict = layout.to_dict()
                # Garantir que layout_data seja uma lista de elementos
                layout_data = layout_dict.get('layout_data')
                if isinstance(layout_data, str):
                    try:
                        layout_data = json.loads(layout_data)
                    except (json.JSONDecodeError, TypeError):
                        layout_data = []
                elif layout_data is None:
                    layout_data = []
                elif not isinstance(layout_data, list):
                    layout_data = []
                
                # Garantir que temos elements no formato correto
                layout_dict['elements'] = layout_data
                
                # Remover layout_data se existir para evitar confusão
                if 'layout_data' in layout_dict:
                    del layout_dict['layout_data']
                
                return layout_dict
            
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
    
    def list_user_layouts(self, user_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Lista todos os layouts do usuário.
        
        Args:
            user_id: ID do usuário (opcional)
            limit: Número máximo de layouts a retornar
            
        Returns:
            Lista de layouts do usuário
        """
        try:
            DashboardLayout = get_dashboard_layout()
            if not DashboardLayout:
                return []
            
            query = DashboardLayout.query
            if user_id:
                query = query.filter_by(user_id=user_id)
            else:
                query = query.filter_by(user_id=None)
            
            layouts = query.order_by(DashboardLayout.created_at.desc()).limit(limit).all()
            
            result = []
            for layout in layouts:
                layout_dict = layout.to_dict()
                # Normalizar layout_data para elements
                layout_data = layout_dict.get('layout_data')
                if isinstance(layout_data, str):
                    try:
                        layout_data = json.loads(layout_data)
                    except (json.JSONDecodeError, TypeError):
                        layout_data = []
                elif layout_data is None:
                    layout_data = []
                elif not isinstance(layout_data, list):
                    layout_data = []
                
                layout_dict['elements'] = layout_data
                if 'layout_data' in layout_dict:
                    del layout_dict['layout_data']
                
                # Adicionar informações resumidas
                layout_dict['element_count'] = len(layout_data)
                result.append(layout_dict)
            
            return result
        except Exception as e:
            logger.error(f"Erro ao listar layouts do usuário: {e}", exc_info=True)
            return []
    
    def set_default_layout(self, layout_id: str, user_id: Optional[int] = None) -> bool:
        """
        Define um layout como padrão do usuário.
        
        Args:
            layout_id: ID do layout
            user_id: ID do usuário
            
        Returns:
            True se bem-sucedido
        """
        try:
            DashboardLayout = get_dashboard_layout()
            if not DashboardLayout:
                return False
            
            layout = DashboardLayout.query.get(layout_id)
            if not layout:
                return False
            
            # Verificar se o layout pertence ao usuário
            if user_id and layout.user_id != user_id:
                return False
            
            # Remover outros layouts padrão do usuário
            query = DashboardLayout.query.filter_by(is_default=True)
            if user_id:
                query = query.filter_by(user_id=user_id)
            else:
                query = query.filter_by(user_id=None)
            
            existing_defaults = query.all()
            for l in existing_defaults:
                if l.id != layout_id:
                    l.is_default = False
            
            # Definir este como padrão
            layout.is_default = True
            db.session.commit()
            
            logger.info(f"Layout {layout_id} definido como padrão para usuário {user_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao definir layout padrão: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def delete_layout(self, layout_id: str, user_id: Optional[int] = None) -> bool:
        """
        Deleta um layout.
        
        Args:
            layout_id: ID do layout
            user_id: ID do usuário (para verificação de permissão)
            
        Returns:
            True se bem-sucedido
        """
        try:
            DashboardLayout = get_dashboard_layout()
            if not DashboardLayout:
                return False
            
            layout = DashboardLayout.query.get(layout_id)
            if not layout:
                return False
            
            # Verificar se o layout pertence ao usuário
            if user_id and layout.user_id != user_id:
                return False
            
            db.session.delete(layout)
            db.session.commit()
            
            logger.info(f"Layout {layout_id} deletado")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar layout: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def get_svg_components(self) -> List[Dict[str, Any]]:
        """
        Retorna biblioteca de componentes SVG disponíveis.
        Descobre automaticamente os SVGs na pasta static/mash_control/svg/
        e carrega suas configurações JSON.
        
        Returns:
            Lista de componentes disponíveis
        """
        svg_path = self.plugin_path / "static" / "mash_control" / "svg"
        components = []
        
        if not svg_path.exists():
            logger.warning(f"Pasta de SVGs não encontrada: {svg_path}")
            return components
        
        # Buscar todos os arquivos SVG
        for svg_file in svg_path.glob("*.svg"):
            component_name = svg_file.stem  # Nome sem extensão
            
            # Tentar carregar configuração JSON correspondente
            json_file = svg_path / f"{component_name}.json"
            config = {}
            
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except Exception as e:
                    logger.warning(f"Erro ao carregar configuração para {component_name}: {e}")
            
            # Criar entrada do componente
            component = {
                'type': component_name,
                'name': config.get('name', component_name),
                'label': config.get('label', component_name.title()),
                'description': config.get('description', ''),
                'category': config.get('category', 'general'),
                'default_size': {
                    'width': config.get('default_width', 50),
                    'height': config.get('default_height', 50)
                },
                'properties': config.get('properties', {}),
                'icon': config.get('icon', 'bi bi-square')
            }
            
            components.append(component)
        
        return components
    
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

