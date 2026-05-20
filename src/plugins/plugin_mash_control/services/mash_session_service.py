"""
Serviço de gerenciamento de sessão de mostura para o dashboard.

Orquestra o MashExecutor, expondo estado de sessão, timeline de etapas,
logs e controle PID para o frontend do dashboard de mostura.
"""

import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from db.database import db

from plugins.plugin_mash_control.services.mash_executor import MashExecutor, PIDController
from plugins.plugin_mash_control.services.device_integration import DeviceIntegrationService
from plugins.plugin_mash_control.utils.model_loader import get_brew_session

logger = logging.getLogger(__name__)


class MashSessionService:
    """
    Serviço de sessão de mostura para o dashboard.

    Mantém o estado ativo da sessão, gerencia callbacks do MashExecutor
    e expõe dados estruturados para consumo do frontend.
    """

    # Cache de sessão ativa em memória
    _active_sessions: Dict[str, Dict[str, Any]] = {}
    _lock = threading.Lock()

    def __init__(self):
        self.device_integration = DeviceIntegrationService()

    # ─── Gerenciamento de sessão ───────────────────────────────────────

    def start_session(self, recipe_id: str, plant_id: str,
                      session_name: Optional[str] = None,
                      equipment_mapping: Optional[Dict[str, str]] = None,
                      user_id: Optional[int] = None) -> Optional[str]:
        """
        Inicia uma nova sessão de mostura.

        Cria o registro no banco, configura o MashExecutor e dispara
        a thread de execução.

        Returns:
            session_id ou None em caso de erro
        """
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                logger.error("Modelo BrewSession não disponível")
                return None

            import uuid
            session_id = str(uuid.uuid4())

            # Buscar receita para obter as etapas
            from plugins.plugin_mash_control.utils.model_loader import get_mash_recipe, get_recipe
            RecipeModel = get_recipe()
            MashRecipeModel = get_mash_recipe()

            recipe = None
            mash_steps = []

            # Tentar Recipe primeiro (novo modelo)
            if RecipeModel:
                recipe = db.session.query(RecipeModel).filter_by(id=recipe_id).first()
                if recipe and recipe.mash_steps:
                    try:
                        mash_steps = json.loads(recipe.mash_steps) if isinstance(recipe.mash_steps, str) else recipe.mash_steps
                    except (json.JSONDecodeError, TypeError):
                        mash_steps = []

            # Fallback para MashRecipe
            if not recipe and MashRecipeModel:
                recipe = db.session.query(MashRecipeModel).filter_by(id=recipe_id).first()
                if recipe and recipe.recipe_data:
                    try:
                        recipe_data = json.loads(recipe.recipe_data) if isinstance(recipe.recipe_data, str) else recipe.recipe_data
                        mash_steps = recipe_data.get('mash_steps', [])
                    except (json.JSONDecodeError, TypeError):
                        mash_steps = []

            if not recipe:
                logger.error(f"Receita {recipe_id} não encontrada")
                return None

            if not mash_steps:
                logger.warning(f"Receita {recipe_id} não possui etapas de mostura")
                return None

            # Criar registro no banco
            recipe_name = recipe.name if hasattr(recipe, 'name') else getattr(recipe, 'name', 'Receita')
            recipe_type = 'Recipe' if RecipeModel and isinstance(recipe, RecipeModel) else 'MashRecipe'

            session_record = BrewSession(
                id=session_id,
                recipe_id=recipe_id,
                plant_id=plant_id,
                name=session_name or recipe_name,
                status='running',
                current_step=0,
                start_time=datetime.utcnow(),
                user_id=user_id,
                session_data=json.dumps({
                    'recipe_type': recipe_type,
                    'mash_steps': mash_steps,
                    'current_step_index': 0,
                    'total_steps': len(mash_steps),
                    'step_start_time': datetime.utcnow().isoformat(),
                    'temperatures': {},
                    'pid_output': 0.0,
                    'actuator_states': {},
                    'logs': [],
                    'alarms': []
                })
            )
            db.session.add(session_record)
            try:
                db.session.commit()
            except Exception as db_err:
                db.session.rollback()
                logger.warning(f"Erro ao salvar sessão no banco (FK?): {db_err}")
                logger.info("Continuando sessão em modo somente memória")

            # Configurar executor
            executor = MashExecutor(self.device_integration)
            executor.set_callbacks(
                on_step_change=lambda step_idx, steps: self._on_step_change(session_id, step_idx, mash_steps),
                on_temperature_update=lambda temp, pid: self._on_temperature_update(session_id, temp, pid),
                on_log=lambda msg, level: self._on_log(session_id, msg, level),
                on_alarm=lambda alarm: self._on_alarm(session_id, alarm),
                on_complete=lambda: self._on_complete(session_id),
                on_error=lambda err: self._on_error(session_id, err)
            )

            # Estado em memória
            session_state = {
                'session_id': session_id,
                'recipe_name': recipe.name,
                'status': 'running',
                'current_step_index': 0,
                'total_steps': len(mash_steps),
                'mash_steps': mash_steps,
                'step_start_time': datetime.utcnow().isoformat(),
                'temperatures': {},
                'pid_output': 0.0,
                'actuator_states': {},
                'logs': [{
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': f'Sessão iniciada: {recipe.name}',
                    'level': 'info'
                }],
                'alarms': [],
                'executor': executor,
                'equipment_mapping': equipment_mapping or {}
            }

            with self._lock:
                self._active_sessions[session_id] = session_state

            # Iniciar executor em thread separada
            import threading
            thread = threading.Thread(
                target=executor.execute_recipe,
                args=(mash_steps, equipment_mapping or {}),
                daemon=True,
                name=f'mash-session-{session_id[:8]}'
            )
            thread.start()

            logger.info(f"Sessão de mostura {session_id} iniciada para receita {recipe.name}")
            return session_id

        except Exception as e:
            logger.error(f"Erro ao iniciar sessão de mostura: {e}", exc_info=True)
            return None

    def stop_session(self, session_id: str) -> bool:
        """Para uma sessão de mostura ativa."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return False
            executor = state.get('executor')
            if executor:
                executor.stop()
            state['status'] = 'stopped'
            self._update_db_status(session_id, 'stopped')

        self._on_log(session_id, 'Sessão parada pelo usuário', 'warning')
        return True

    def pause_session(self, session_id: str) -> bool:
        """Pausa uma sessão ativa."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return False
            executor = state.get('executor')
            if executor:
                executor.pause()
            state['status'] = 'paused'

        self._on_log(session_id, 'Sessão pausada', 'warning')
        return True

    def resume_session(self, session_id: str) -> bool:
        """Retoma uma sessão pausada."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return False
            executor = state.get('executor')
            if executor:
                executor.resume()
            state['status'] = 'running'

        self._on_log(session_id, 'Sessão retomada', 'info')
        return True

    def advance_step(self, session_id: str) -> bool:
        """Avança manualmente para a próxima etapa."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return False
            executor = state.get('executor')
            if executor:
                executor.advance_step()
            return True

    # ─── Consulta de estado ────────────────────────────────────────────

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retorna o estado atual da sessão para o frontend."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return self._load_session_from_db(session_id)
            return self._build_status_response(state)

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Lista todas as sessões ativas em memória."""
        with self._lock:
            return [
                self._build_status_response(s)
                for s in self._active_sessions.values()
            ]

    def list_recent_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Lista sessões recentes do banco de dados."""
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return []
            sessions = db.session.query(BrewSession).order_by(
                BrewSession.created_at.desc()
            ).limit(limit).all()
            return [s.to_dict() for s in sessions]
        except Exception as e:
            logger.error(f"Erro ao listar sessões recentes: {e}")
            return []

    # ─── Callbacks do MashExecutor ─────────────────────────────────────

    def _on_step_change(self, session_id: str, step_index: int, mash_steps: List[Dict]):
        """Callback quando a etapa muda."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return
            state['current_step_index'] = step_index
            state['step_start_time'] = datetime.utcnow().isoformat()
            # Se acabaram as etapas, marcar como completed
            if step_index >= len(mash_steps):
                state['status'] = 'completed'
                self._update_db_status(session_id, 'completed')

        step_name = mash_steps[step_index].get('name', f'Etapa {step_index + 1}') if step_index < len(mash_steps) else 'Finalizada'
        self._on_log(session_id, f'Etapa {step_index + 1}/{len(mash_steps)}: {step_name}', 'success')

    def _on_temperature_update(self, session_id: str, temperature: float, pid_output: float):
        """Callback de atualização de temperatura."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return
            state['temperatures']['current'] = temperature
            state['pid_output'] = pid_output
            # Atualizar timestamp
            state['last_update'] = datetime.utcnow().isoformat()

    def _on_log(self, session_id: str, message: str, level: str = 'info'):
        """Callback de log."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return
            state['logs'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'message': message,
                'level': level
            })
            # Manter apenas últimos 200 logs
            if len(state['logs']) > 200:
                state['logs'] = state['logs'][-200:]

    def _on_alarm(self, session_id: str, alarm: Dict[str, Any]):
        """Callback de alarme."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return
            alarm['timestamp'] = datetime.utcnow().isoformat()
            state['alarms'].append(alarm)

    def _on_complete(self, session_id: str):
        """Callback de conclusão da mostura."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return
            state['status'] = 'completed'
            self._update_db_status(session_id, 'completed')
            state['step_start_time'] = None

        self._on_log(session_id, 'Mostura concluída com sucesso!', 'success')

    def _on_error(self, session_id: str, error: str):
        """Callback de erro."""
        with self._lock:
            state = self._active_sessions.get(session_id)
            if not state:
                return
            state['status'] = 'error'
            self._update_db_status(session_id, 'error')

        self._on_log(session_id, f'Erro: {error}', 'error')

    # ─── Helpers ───────────────────────────────────────────────────────

    def _update_db_status(self, session_id: str, status: str):
        """Atualiza o status no banco de dados."""
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return
            record = db.session.query(BrewSession).filter_by(id=session_id).first()
            if record:
                record.status = status
                if status in ('completed', 'stopped', 'error'):
                    record.end_time = datetime.utcnow()
                db.session.commit()
        except Exception as e:
            logger.error(f"Erro ao atualizar status da sessão {session_id}: {e}")

    def _build_status_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Constrói a resposta de status para o frontend (sem o executor)."""
        # Enriquecer com dados de status dos dispositivos mapeados
        device_statuses = {}
        equipment_mapping = state.get('equipment_mapping', {})
        if equipment_mapping:
            for role, actor_id in equipment_mapping.items():
                try:
                    dev_status = self.device_integration.get_device_status(actor_id)
                    if dev_status:
                        device_statuses[role] = dev_status
                except Exception:
                    pass

        return {
            'session_id': state['session_id'],
            'recipe_name': state['recipe_name'],
            'status': state['status'],
            'current_step_index': state['current_step_index'],
            'total_steps': state['total_steps'],
            'mash_steps': state['mash_steps'],
            'step_start_time': state.get('step_start_time'),
            'temperatures': state.get('temperatures', {}),
            'pid_output': state.get('pid_output', 0.0),
            'actuator_states': state.get('actuator_states', {}),
            'logs': state.get('logs', []),
            'alarms': state.get('alarms', []),
            'last_update': state.get('last_update'),
            'equipment_mapping': equipment_mapping,
            'device_statuses': device_statuses
        }

    def _load_session_from_db(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Carrega dados de sessão do banco (sessões finalizadas)."""
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return None
            record = db.session.query(BrewSession).filter_by(id=session_id).first()
            if not record:
                return None
            return record.to_dict()
        except Exception as e:
            logger.error(f"Erro ao carregar sessão {session_id} do banco: {e}")
            return None


# Singleton para acesso global
_session_service_instance = None
_session_service_lock = threading.Lock()


def get_mash_session_service() -> MashSessionService:
    """Obtém ou cria a instância singleton do MashSessionService."""
    global _session_service_instance
    if _session_service_instance is None:
        with _session_service_lock:
            if _session_service_instance is None:
                _session_service_instance = MashSessionService()
    return _session_service_instance
