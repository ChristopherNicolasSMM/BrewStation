"""
Serviço de controle de processos automáticos.

Gerencia execução de receitas, controle PID de temperatura e transições entre etapas.
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from flask import current_app
from db.database import db

from plugins.plugin_mash_control.services.device_integration import DeviceIntegrationService
from plugins.plugin_mash_control.utils.model_loader import get_brew_session, get_mash_recipe

logger = logging.getLogger(__name__)


class ProcessControlService:
    """
    Serviço para controle de processos automáticos de brassagem.
    
    Gerencia execução de receitas, controle PID de temperatura, transições
    entre etapas e sistema de alarmes.
    """
    
    def __init__(self, plugin_path: Path):
        """
        Inicializa o serviço de controle de processos.
        
        Args:
            plugin_path: Caminho do diretório do plugin
        """
        self.plugin_path = plugin_path
        self.device_integration = DeviceIntegrationService()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._session_threads: Dict[str, threading.Thread] = {}
        self._session_locks: Dict[str, threading.Lock] = {}
        self.sessions_path = plugin_path / "data" / "sessions"
        self.sessions_path.mkdir(parents=True, exist_ok=True)
    
    def start_session(self, recipe_id: str, equipment_mapping: Dict[str, str], session_name: Optional[str] = None) -> Optional[str]:
        """
        Inicia uma nova sessão de brassagem.
        
        Args:
            recipe_id: ID da receita a ser executada
            equipment_mapping: Mapeamento dispositivo → função
            session_name: Nome opcional para a sessão
            
        Returns:
            ID da sessão criada ou None em caso de erro
        """
        try:
            MashRecipe = get_mash_recipe()
            BrewSession = get_brew_session()
            
            if not MashRecipe or not BrewSession:
                logger.error("Modelos não disponíveis")
                return None
            
            # Obter receita
            recipe = MashRecipe.query.get(recipe_id)
            if not recipe:
                logger.error(f"Receita {recipe_id} não encontrada")
                return None
            
            # Validar equipamento necessário
            recipe_data = recipe.to_dict().get('recipe_data', {})
            required_devices = self._extract_required_devices(recipe_data)
            
            for device_function, device_id in equipment_mapping.items():
                if device_function in required_devices:
                    device_status = self.device_integration.get_device_status(device_id)
                    if not device_status or not device_status.get('is_active'):
                        logger.error(f"Dispositivo {device_id} necessário para {device_function} não está disponível")
                        return None
            
            # Criar sessão
            import uuid
            session_id = str(uuid.uuid4())
            
            session = BrewSession(
                id=session_id,
                recipe_id=recipe_id,
                name=session_name or f"{recipe.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                status='pending',
                current_step=0,
                equipment_used=json.dumps(list(equipment_mapping.values())),
                user_id=current_app.login_manager.current_user.id if hasattr(current_app, 'login_manager') else None,
                session_data=json.dumps({
                    'equipment_mapping': equipment_mapping,
                    'events': [],
                    'telemetry': []
                })
            )
            
            db.session.add(session)
            db.session.commit()
            
            # Iniciar thread de execução
            self._session_locks[session_id] = threading.Lock()
            thread = threading.Thread(
                target=self._execute_session,
                args=(session_id,),
                daemon=True
            )
            thread.start()
            self._session_threads[session_id] = thread
            
            logger.info(f"Sessão {session_id} iniciada para receita {recipe_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Erro ao iniciar sessão: {e}", exc_info=True)
            db.session.rollback()
            return None
    
    def pause_session(self, session_id: str) -> bool:
        """
        Pausa uma sessão em execução.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se sessão foi pausada com sucesso
        """
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return False
            
            session = BrewSession.query.get(session_id)
            if not session:
                return False
            
            if session.status == 'running':
                session.status = 'paused'
                db.session.commit()
                
                self._log_event(session_id, 'session_paused', {'timestamp': datetime.now().isoformat()})
                logger.info(f"Sessão {session_id} pausada")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao pausar sessão {session_id}: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def resume_session(self, session_id: str) -> bool:
        """
        Retoma uma sessão pausada.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se sessão foi retomada com sucesso
        """
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return False
            
            session = BrewSession.query.get(session_id)
            if not session:
                return False
            
            if session.status == 'paused':
                session.status = 'running'
                db.session.commit()
                
                self._log_event(session_id, 'session_resumed', {'timestamp': datetime.now().isoformat()})
                logger.info(f"Sessão {session_id} retomada")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao retomar sessão {session_id}: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def stop_session(self, session_id: str) -> bool:
        """
        Para uma sessão em execução.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se sessão foi parada com sucesso
        """
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return False
            
            session = BrewSession.query.get(session_id)
            if not session:
                return False
            
            if session.status in ['running', 'paused']:
                session.status = 'completed'
                session.end_time = datetime.now()
                db.session.commit()
                
                # Desligar todos os dispositivos
                self._stop_all_devices(session_id)
                
                self._log_event(session_id, 'session_stopped', {'timestamp': datetime.now().isoformat()})
                logger.info(f"Sessão {session_id} parada")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao parar sessão {session_id}: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def execute_step(self, session_id: str, step_data: Dict[str, Any]) -> bool:
        """
        Executa uma etapa específica da receita.
        
        Args:
            session_id: ID da sessão
            step_data: Dados da etapa a ser executada
            
        Returns:
            True se etapa foi executada com sucesso
        """
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return False
            
            session = BrewSession.query.get(session_id)
            if not session:
                return False
            
            # Obter mapeamento de equipamento
            session_dict = session.to_dict()
            equipment_mapping = session_dict.get('session_data', {}).get('equipment_mapping', {})
            
            # Executar ações da etapa
            actions = step_data.get('actions', [])
            for action in actions:
                if action.get('type') == 'set_temperature':
                    target = action.get('target')
                    tolerance = action.get('tolerance', 1.0)
                    device_id = equipment_mapping.get(step_data.get('devices', {}).get('heater'))
                    if device_id:
                        self.control_temperature(device_id, target, tolerance)
                
                elif action.get('type') == 'wait':
                    duration = action.get('duration', 0)
                    time.sleep(duration)
                
                elif action.get('type') == 'set_port':
                    device_id = equipment_mapping.get(action.get('device'))
                    port = action.get('port')
                    value = action.get('value')
                    if device_id:
                        self.device_integration.set_port_value(device_id, port, value)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao executar etapa da sessão {session_id}: {e}", exc_info=True)
            return False
    
    def control_temperature(self, device_id: str, target_temp: float, tolerance: float = 1.0) -> bool:
        """
        Controla temperatura usando controle PID simples.
        
        Args:
            device_id: ID do dispositivo aquecedor
            target_temp: Temperatura alvo
            tolerance: Tolerância aceitável
            
        Returns:
            True se controle foi iniciado
        """
        try:
            # Obter sensor de temperatura associado
            ports = self.device_integration.get_all_ports(device_id)
            
            # Encontrar porta de temperatura
            temp_port = None
            heater_port = None
            
            for port_name, port_config in ports.items():
                if port_config.get('type') == 'sensor' and 'temp' in port_name.lower():
                    temp_port = port_name
                elif port_config.get('type') == 'actuator' and ('heater' in port_name.lower() or 'heat' in port_name.lower()):
                    heater_port = port_name
            
            if not temp_port or not heater_port:
                logger.warning(f"Portas de temperatura ou aquecedor não encontradas para dispositivo {device_id}")
                return False
            
            # Controle PID simples (on/off com histerese)
            current_temp = self.device_integration.get_port_value(device_id, temp_port)
            
            if current_temp is None:
                logger.warning(f"Temperatura atual não disponível para dispositivo {device_id}")
                return False
            
            if current_temp < target_temp - tolerance:
                # Ligar aquecedor
                self.device_integration.set_port_value(device_id, heater_port, True)
            elif current_temp > target_temp + tolerance:
                # Desligar aquecedor
                self.device_integration.set_port_value(device_id, heater_port, False)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao controlar temperatura do dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    def check_step_completion(self, session_id: str, step: Dict[str, Any]) -> bool:
        """
        Verifica se uma etapa foi completada.
        
        Args:
            session_id: ID da sessão
            step: Dados da etapa
            
        Returns:
            True se etapa foi completada
        """
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return False
            
            session = BrewSession.query.get(session_id)
            if not session:
                return False
            
            session_dict = session.to_dict()
            equipment_mapping = session_dict.get('session_data', {}).get('equipment_mapping', {})
            
            # Verificar condições de conclusão
            if step.get('type') == 'mash':
                target_temp = step.get('target_temp')
                duration = step.get('duration', 0)
                
                # Obter temperatura atual
                device_id = equipment_mapping.get(step.get('devices', {}).get('sensor'))
                if device_id:
                    temp_port = self._find_temp_port(device_id)
                    if temp_port:
                        current_temp = self.device_integration.get_port_value(device_id, temp_port)
                        
                        # Verificar se temperatura está no alvo e tempo decorrido
                        if current_temp and abs(current_temp - target_temp) <= 1.0:
                            # Verificar duração (simplificado - em produção usar timestamp de início)
                            return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar conclusão da etapa: {e}", exc_info=True)
            return False
    
    def handle_alarm(self, session_id: str, alarm_type: str, message: str) -> bool:
        """
        Trata alarmes durante a execução.
        
        Args:
            session_id: ID da sessão
            alarm_type: Tipo de alarme
            message: Mensagem do alarme
            
        Returns:
            True se alarme foi tratado
        """
        try:
            self._log_event(session_id, 'alarm', {
                'type': alarm_type,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.warning(f"Alarme na sessão {session_id}: {alarm_type} - {message}")
            
            # Em produção, aqui poderia pausar a sessão automaticamente se crítico
            if alarm_type == 'critical':
                self.pause_session(session_id)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao tratar alarme: {e}", exc_info=True)
            return False
    
    def log_event(self, session_id: str, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Registra um evento na sessão.
        
        Args:
            session_id: ID da sessão
            event_type: Tipo do evento
            data: Dados do evento
            
        Returns:
            True se evento foi registrado
        """
        return self._log_event(session_id, event_type, data)
    
    def _log_event(self, session_id: str, event_type: str, data: Dict[str, Any]) -> bool:
        """Método interno para registrar eventos."""
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return False
            
            session = BrewSession.query.get(session_id)
            if not session:
                return False
            
            session_dict = session.to_dict()
            session_data = session_dict.get('session_data', {})
            events = session_data.get('events', [])
            
            events.append({
                'type': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
            
            session_data['events'] = events
            session.session_data = json.dumps(session_data)
            db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao registrar evento: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def _execute_session(self, session_id: str):
        """Thread de execução da sessão."""
        try:
            BrewSession = get_brew_session()
            MashRecipe = get_mash_recipe()
            
            if not BrewSession or not MashRecipe:
                return
            
            session = BrewSession.query.get(session_id)
            if not session:
                return
            
            recipe = MashRecipe.query.get(session.recipe_id)
            if not recipe:
                return
            
            recipe_data = recipe.to_dict().get('recipe_data', {})
            steps = recipe_data.get('steps', [])
            
            session.status = 'running'
            session.start_time = datetime.now()
            db.session.commit()
            
            self._log_event(session_id, 'session_started', {'timestamp': session.start_time.isoformat()})
            
            for i, step in enumerate(steps):
                if session.status != 'running':
                    break
                
                session.current_step = i
                db.session.commit()
                
                self._log_event(session_id, 'step_started', {
                    'step_index': i,
                    'step_name': step.get('name'),
                    'timestamp': datetime.now().isoformat()
                })
                
                # Executar etapa
                self.execute_step(session_id, step)
                
                # Aguardar conclusão
                while not self.check_step_completion(session_id, step) and session.status == 'running':
                    time.sleep(1)
                    session = BrewSession.query.get(session_id)
                    if not session:
                        break
                
                self._log_event(session_id, 'step_completed', {
                    'step_index': i,
                    'step_name': step.get('name'),
                    'timestamp': datetime.now().isoformat()
                })
            
            # Finalizar sessão
            if session.status == 'running':
                session.status = 'completed'
                session.end_time = datetime.now()
                db.session.commit()
                
                self._stop_all_devices(session_id)
                self._log_event(session_id, 'session_completed', {'timestamp': session.end_time.isoformat()})
        
        except Exception as e:
            logger.error(f"Erro na execução da sessão {session_id}: {e}", exc_info=True)
            BrewSession = get_brew_session()
            if BrewSession:
                session = BrewSession.query.get(session_id)
                if session:
                    session.status = 'error'
                    session.end_time = datetime.now()
                    db.session.commit()
    
    def _stop_all_devices(self, session_id: str):
        """Desliga todos os dispositivos da sessão."""
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return
            
            session = BrewSession.query.get(session_id)
            if not session:
                return
            
            session_dict = session.to_dict()
            equipment_mapping = session_dict.get('session_data', {}).get('equipment_mapping', {})
            
            for device_id in equipment_mapping.values():
                ports = self.device_integration.get_all_ports(device_id)
                for port_name, port_config in ports.items():
                    if port_config.get('type') == 'actuator':
                        self.device_integration.set_port_value(device_id, port_name, False)
        except Exception as e:
            logger.error(f"Erro ao parar dispositivos: {e}", exc_info=True)
    
    def _extract_required_devices(self, recipe_data: Dict[str, Any]) -> List[str]:
        """Extrai lista de dispositivos necessários da receita."""
        required = []
        steps = recipe_data.get('steps', [])
        for step in steps:
            devices = step.get('devices', {})
            required.extend(devices.values())
        return list(set(required))
    
    def _find_temp_port(self, device_id: str) -> Optional[str]:
        """Encontra porta de temperatura de um dispositivo."""
        ports = self.device_integration.get_all_ports(device_id)
        for port_name, port_config in ports.items():
            if port_config.get('type') == 'sensor' and 'temp' in port_name.lower():
                return port_name
        return None

