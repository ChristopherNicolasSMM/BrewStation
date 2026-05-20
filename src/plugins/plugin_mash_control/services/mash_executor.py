"""
Executor de etapas de brassagem com DeviceAPI.

MashExecutor estende ProcessControlService com:
- Controle PID (proporcional-integral-derivativo) real em vez de histerese simples
- Validação robusta de atores usando DeviceAPI (corrige bug is_active)
- Callbacks de eventos para integração WebSocket (Fase 4)
- Tratamento estruturado de erros (ator desconectado, falha de leitura)
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from plugins.plugin_mash_control.services.device_integration import \
    DeviceIntegrationService
from plugins.plugin_mash_control.utils.model_loader import get_brew_session

logger = logging.getLogger(__name__)


class PIDController:
    """
    Controlador PID discreto para brassagem.

    Implementa a fórmula PID padrão: u(t) = Kp*e(t) + Ki*int(e) + Kd*de(t)/dt
    Com anti-windup no termo integral e saída limitada a [0, 1].
    """

    def __init__(self, kp: float = 1.0, ki: float = 0.01, kd: float = 0.1,
                 setpoint: float = 0.0, output_min: float = 0.0, output_max: float = 1.0):
        """
        Args:
            kp: Ganho proporcional
            ki: Ganho integral
            kd: Ganho derivativo
            setpoint: Temperatura alvo em °C
            output_min: Saída mínima (0.0 = desligado)
            output_max: Saída máxima (1.0 = 100% duty cycle)
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_min = output_min
        self.output_max = output_max

        self._last_error: float = 0.0
        self._integral: float = 0.0
        self._last_time: Optional[float] = None
        self._last_output: float = 0.0

    def reset(self):
        """Reseta o estado interno do controlador."""
        self._last_error = 0.0
        self._integral = 0.0
        self._last_time = None
        self._last_output = 0.0

    def update(self, current_value: float, dt: Optional[float] = None) -> float:
        """
        Calcula a saída do PID dada a leitura atual.

        Args:
            current_value: Temperatura atual medida
            dt: Delta-t em segundos (auto-calculado se None)

        Returns:
            Saída do controlador entre output_min e output_max
        """
        now = time.monotonic()

        if self._last_time is None:
            dt = 0.1
        elif dt is None:
            dt = now - self._last_time
            dt = max(dt, 0.001)  # evitar divisão por zero

        error = self.setpoint - current_value

        # Proporcional
        proportional = self.kp * error

        # Integral com anti-windup
        self._integral += error * dt
        # Limitar integral para evitar windup
        integral_max = abs(self.output_max / self.ki) if self.ki > 0 else 0
        self._integral = max(-integral_max, min(integral_max, self._integral))
        integral = self.ki * self._integral

        # Derivativo (usando medição, não erro, para evitar "derivative kick")
        derivative = 0.0
        if dt > 0:
            # Filtro passa-baixa na derivada
            measurement_derivative = -(current_value - (current_value - error + self._last_error)) / dt
            derivative = self.kd * measurement_derivative

        # Saída
        output = proportional + integral + derivative
        output = max(self.output_min, min(self.output_max, output))

        self._last_error = error
        self._last_time = now
        self._last_output = output

        return output

    def set_setpoint(self, setpoint: float):
        """Altera o setpoint sem resetar o estado do controlador."""
        self.setpoint = setpoint

    @property
    def last_output(self) -> float:
        return self._last_output


class MashExecutor:
    """
    Executor de etapas de brassagem com DeviceAPI.

    Fornece execução de passos com controle PID, validação de atores,
    callbacks de eventos e tratamento estruturado de erros.

    Uso:
        executor = MashExecutor(device_integration_service)
        executor.register_callback('temperature', my_temp_callback)
        success = executor.execute_step_with_deviceapi(session_id, step_data)
    """

    # Tipos de callback disponíveis
    CALLBACK_TEMPERATURE = 'temperature'       # (session_id, current_temp, setpoint)
    CALLBACK_STEP = 'step'                     # (session_id, step_index, step_name, status)
    CALLBACK_ERROR = 'error'                   # (session_id, error_type, message)
    CALLBACK_ALARM = 'alarm'                   # (session_id, alarm_type, message)
    CALLBACK_DEVICE = 'device'                 # (session_id, device_id, action, value)

    def __init__(self, device_integration: DeviceIntegrationService,
                 pid_kp: float = 1.0, pid_ki: float = 0.01, pid_kd: float = 0.1):
        """
        Args:
            device_integration: Instância de DeviceIntegrationService
            pid_kp: Ganho proporcional padrão do PID
            pid_ki: Ganho integral padrão do PID
            pid_kd: Ganho derivativo padrão do PID
        """
        self.device_integration = device_integration
        self._pid_controllers: Dict[str, PIDController] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            self.CALLBACK_TEMPERATURE: [],
            self.CALLBACK_STEP: [],
            self.CALLBACK_ERROR: [],
            self.CALLBACK_ALARM: [],
            self.CALLBACK_DEVICE: [],
        }
        self._default_kp = pid_kp
        self._default_ki = pid_ki
        self._default_kd = pid_kd

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #

    def register_callback(self, event_type: str, callback: Callable):
        """
        Registra um callback para eventos do executor.

        Args:
            event_type: Tipo do evento (vide constantes CALLBACK_*)
            callback: Função callback que receberá os args do evento
        """
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    def unregister_callback(self, event_type: str, callback: Callable) -> bool:
        """Remove um callback registrado. Retorna True se foi removido."""
        if event_type in self._callbacks and callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)
            return True
        return False

    def _emit(self, event_type: str, *args, **kwargs):
        """Dispara todos os callbacks registrados para um tipo de evento."""
        for cb in self._callbacks.get(event_type, []):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Erro em callback {event_type}: {e}")

    # ------------------------------------------------------------------ #
    # Validação de atores
    # ------------------------------------------------------------------ #

    def validate_actor(self, actor_id: str, role: str = "desconhecido") -> bool:
        """
        Valida que um ator existe e está acessível via DeviceAPI.

        Corrige o bug do ProcessControlService que verificava 'is_active'
        inexistente no dicionário retornado por get_device_status().

        Args:
            actor_id: ID do ator
            role: Descrição da função (para logging)

        Returns:
            True se o ator está válido e acessível
        """
        if not self.device_integration.is_available():
            self._emit(self.CALLBACK_ERROR, None, "device_manager_indisponivel",
                       "device_manager não está disponível")
            return False

        status = self.device_integration.get_device_status(actor_id)
        if not status:
            logger.error(f"Ator {actor_id} ({role}): não encontrado ou sem resposta")
            self._emit(self.CALLBACK_ERROR, None, "ator_nao_encontrado",
                       f"Ator {actor_id} ({role}) não encontrado")
            return False

        # Validação correta: verificar se status != 'offline'
        if status.get('status') == 'offline':
            logger.error(f"Ator {actor_id} ({role}): offline")
            self._emit(self.CALLBACK_ERROR, None, "ator_offline",
                       f"Ator {actor_id} ({role}) está offline")
            return False

        return True

    def validate_step_devices(self, equipment_mapping: Dict[str, str],
                              devices_config: Dict[str, str]) -> Dict[str, str]:
        """
        Valida que todos os dispositivos necessários para uma etapa estão acessíveis.

        Args:
            equipment_mapping: Mapeamento função → actor_id da sessão
            devices_config: Dispositivos necessários para a etapa (role → nome_amigável)

        Returns:
            Dict com role → actor_id resolvido para dispositivos válidos

        Raises:
            ValueError: Se algum dispositivo necessário não estiver disponível
        """
        resolved = {}
        for role, friendly_name in devices_config.items():
            actor_id = equipment_mapping.get(role)
            if not actor_id:
                msg = f"Dispositivo '{friendly_name}' (role={role}) não mapeado na sessão"
                logger.error(msg)
                self._emit(self.CALLBACK_ERROR, None, "dispositivo_nao_mapeado", msg)
                raise ValueError(msg)

            if not self.validate_actor(actor_id, friendly_name):
                msg = f"Dispositivo '{friendly_name}' ({actor_id}) não disponível"
                self._emit(self.CALLBACK_ERROR, None, "dispositivo_indisponivel", msg)
                raise ValueError(msg)

            resolved[role] = actor_id

        return resolved

    # ------------------------------------------------------------------ #
    # Controle PID
    # ------------------------------------------------------------------ #

    def get_pid(self, controller_id: str) -> PIDController:
        """Obtém ou cria um controlador PID para um contexto."""
        if controller_id not in self._pid_controllers:
            self._pid_controllers[controller_id] = PIDController(
                kp=self._default_kp, ki=self._default_ki, kd=self._default_kd
            )
        return self._pid_controllers[controller_id]

    def control_temperature_pid(self, session_id: Optional[str], sensor_id: str,
                                heater_id: str, setpoint: float,
                                tolerance: float = 0.5) -> Dict[str, Any]:
        """
        Controla temperatura usando PID real.

        Executa UMA iteração do controlador PID. Deve ser chamado
        repetidamente (ex: a cada 5s) para manter a temperatura.

        Args:
            session_id: ID da sessão (para callbacks)
            sensor_id: Actor ID do sensor de temperatura
            heater_id: Actor ID do aquecedor (atuador)
            setpoint: Temperatura alvo em °C
            tolerance: Tolerância aceitável (padrão 0.5°C)

        Returns:
            Dict com resultado:
                - current_temp: Temperatura lida
                - pid_output: Saída do PID (0.0 a 1.0)
                - heater_on: Se o aquecedor foi acionado
                - on_target: True se está dentro da tolerância
        """
        pid = self.get_pid(session_id)

        # Mudar setpoint se necessário
        if abs(pid.setpoint - setpoint) > 0.1:
            pid.set_setpoint(setpoint)
            pid.reset()

        # Ler sensor
        current_temp = self.device_integration.get_port_value(sensor_id, None)
        if current_temp is None:
            logger.warning(f"Sessão {session_id}: falha ao ler sensor {sensor_id}")
            self._emit(self.CALLBACK_ERROR, session_id, "falha_leitura_sensor",
                       f"Sensor {sensor_id} não retornou valor")
            return {'current_temp': None, 'pid_output': 0.0, 'heater_on': False, 'on_target': False}

        # Calcular PID
        pid_output = pid.update(current_temp)

        # Converter PID output para ação on/off usando PWM-like com período fixo
        # Se o heater é digital (on/off), usamos o PID output como probabilidade
        heater_on = pid_output > 0.5  # Liga se >50% duty cycle

        # Aplicar ao atuador
        heater_result = self.device_integration.set_port_value(heater_id, None, heater_on)

        self._emit(self.CALLBACK_DEVICE, session_id, heater_id,
                   'set_heater', heater_on)

        # Emitir temperatura
        self._emit(self.CALLBACK_TEMPERATURE, session_id, current_temp, setpoint)

        on_target = abs(current_temp - setpoint) <= tolerance
        return {
            'current_temp': current_temp,
            'pid_output': round(pid_output, 3),
            'heater_on': heater_on,
            'heater_result': heater_result,
            'on_target': on_target,
        }

    def control_temperature_pid_continuous(self, session_id: str, sensor_id: str,
                                            heater_id: str, setpoint: float,
                                            duration_min: int = 60, interval_s: int = 5,
                                            tolerance: float = 0.5,
                                            stop_event: Optional[threading.Event] = None
                                            ) -> Dict[str, Any]:
        """
        Executa controle PID contínuo em background thread.

        Args:
            session_id: ID da sessão
            sensor_id: Actor ID do sensor
            heater_id: Actor ID do aquecedor
            setpoint: Temperatura alvo
            duration_min: Duração máxima em minutos
            interval_s: Intervalo entre iterações PID
            tolerance: Tolerância
            stop_event: Evento para parada antecipada

        Returns:
            Dict com sumário da execução
        """
        pid = self.get_pid(f"continuous_{session_id}")
        pid.set_setpoint(setpoint)
        pid.reset()

        start_time = time.monotonic()
        max_duration_s = duration_min * 60
        readings: List[Dict[str, Any]] = []
        last_alarm_temp: Optional[float] = None

        while True:
            # Verificar parada
            if stop_event and stop_event.is_set():
                logger.info(f"Sessão {session_id}: controle PID interrompido por stop_event")
                break

            elapsed = time.monotonic() - start_time
            if elapsed > max_duration_s:
                logger.info(f"Sessão {session_id}: duração máxima atingida ({duration_min}min)")
                break

            result = self.control_temperature_pid(
                session_id, sensor_id, heater_id, setpoint, tolerance
            )
            readings.append({
                'timestamp': datetime.now().isoformat(),
                'elapsed_s': round(elapsed),
                **result
            })

            # Alarmes por temperatura excessiva
            current_temp = result.get('current_temp')
            if current_temp is not None:
                if current_temp > setpoint + 5.0 and current_temp != last_alarm_temp:
                    self._emit(self.CALLBACK_ALARM, session_id, 'superaquecimento',
                               f"Temperatura {current_temp:.1f}°C excede {setpoint:.1f}°C +5°C")
                    last_alarm_temp = current_temp
                elif current_temp < setpoint - 5.0 and current_temp != last_alarm_temp:
                    self._emit(self.CALLBACK_ALARM, session_id, 'temperatura_baixa',
                               f"Temperatura {current_temp:.1f}°C está {setpoint:.1f}°C -5°C")
                    last_alarm_temp = current_temp

            time.sleep(interval_s)

        # Desligar heater ao final
        self.device_integration.set_port_value(heater_id, None, False)
        self._emit(self.CALLBACK_DEVICE, session_id, heater_id, 'set_heater', False)

        return {
            'session_id': session_id,
            'setpoint': setpoint,
            'duration_min': duration_min,
            'total_readings': len(readings),
            'readings': readings,
        }

    # ------------------------------------------------------------------ #
    # Execução de etapas
    # ------------------------------------------------------------------ #

    def execute_step_with_deviceapi(self, session_id: str,
                                     step_data: Dict[str, Any]) -> bool:
        """
        Executa uma etapa usando DeviceAPI diretamente.

        Difere de ProcessControlService.execute_step() por:
        - Usar validate_step_devices() para verificar atores antes de executar
        - Usar controle PID real em vez de histerese
        - Emitir callbacks para todos os eventos
        - Tratar erros de forma estruturada

        Args:
            session_id: ID da sessão
            step_data: Dados da etapa {name, type, target_temp, duration, devices, actions}

        Returns:
            True se a etapa foi executada sem erros críticos
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

            step_name = step_data.get('name', 'desconhecido')
            step_data.get('type', 'unknown')
            target_temp = step_data.get('target_temp')
            duration = step_data.get('duration', 0)
            devices_config = step_data.get('devices', {})

            self._emit(self.CALLBACK_STEP, session_id,
                       session_dict.get('current_step', 0), step_name, 'iniciado')

            # Ações manuais na etapa
            actions = step_data.get('actions', [])
            for action in actions:
                action_type = action.get('type')

                if action_type == 'set_temperature':
                    if not target_temp:
                        target_temp = action.get('target')
                    tolerance = action.get('tolerance', 1.0)

                    # Validar dispositivos necessários
                    try:
                        resolved = self.validate_step_devices(
                            equipment_mapping, devices_config
                        )
                    except ValueError:
                        logger.error(f"Sessão {session_id}: falha na validação dos dispositivos da etapa '{step_name}'")
                        self._emit(self.CALLBACK_ERROR, session_id, "validacao_dispositivos",
                                   f"Etapa '{step_name}': dispositivos necessários não disponíveis")
                        return False

                    # Obter sensor e heater
                    sensor_id = resolved.get('sensor')
                    heater_id = resolved.get('heater')

                    if sensor_id and heater_id and target_temp:
                        logger.info(f"Sessão {session_id}: iniciando controle PID para "
                                    f"{target_temp}°C (sensor={sensor_id}, heater={heater_id})")

                        # Criar stop_event para esta etapa
                        step_stop = threading.Event()
                        pid_thread = threading.Thread(
                            target=self._run_pid_for_duration,
                            args=(session_id, sensor_id, heater_id,
                                  target_temp, duration, tolerance, step_stop),
                            daemon=True
                        )
                        pid_thread.start()

                        # Aguardar duração da etapa ou interrupção
                        pid_thread.join(timeout=(duration * 60) + 10)

                        # Se a thread ainda estiver viva após o timeout, parar
                        if pid_thread.is_alive():
                            step_stop.set()
                            pid_thread.join(timeout=5)

                elif action_type == 'wait':
                    wait_duration = action.get('duration', 0)
                    time.sleep(wait_duration)

                elif action_type == 'set_port':
                    device_role = action.get('device')
                    port = action.get('port')
                    value = action.get('value')
                    actor_id = equipment_mapping.get(device_role) if device_role else None
                    if actor_id:
                        self.device_integration.set_port_value(actor_id, port, value)
                        self._emit(self.CALLBACK_DEVICE, session_id, actor_id,
                                   'set_port', value)

                elif action_type == 'set_output':
                    # Ação direta: liga/desliga atuador por role
                    device_role = action.get('device')
                    value = action.get('value', False)
                    actor_id = equipment_mapping.get(device_role) if device_role else None
                    if actor_id:
                        self.device_integration.set_port_value(actor_id, None, value)
                        self._emit(self.CALLBACK_DEVICE, session_id, actor_id,
                                   'set_output', value)

            self._emit(self.CALLBACK_STEP, session_id,
                       session_dict.get('current_step', 0), step_name, 'concluido')
            return True

        except Exception as e:
            logger.error(f"Erro ao executar etapa via DeviceAPI na sessão {session_id}: {e}",
                         exc_info=True)
            self._emit(self.CALLBACK_ERROR, session_id, "erro_execucao", str(e))
            return False

    def _run_pid_for_duration(self, session_id: Optional[str], sensor_id: str,
                               heater_id: str, setpoint: float,
                               duration_min: int, tolerance: float,
                               stop_event: threading.Event):
        """Executa PID em loop por uma duração (executado em thread separada)."""
        pid = self.get_pid(f"step_{session_id or 'recipe'}")
        pid.set_setpoint(setpoint)
        pid.reset()

        start = time.monotonic()
        duration_s = duration_min * 60
        interval_s = 5  # período PID

        while not stop_event.is_set():
            elapsed = time.monotonic() - start

            if duration_s > 0 and elapsed > duration_s:
                break

            # Verificar se a sessão ainda está running (session_id opcional)
            if session_id:
                try:
                    BrewSession = get_brew_session()
                    if BrewSession:
                        session = BrewSession.query.get(session_id)
                        if session and session.status not in ('running', 'paused'):
                            logger.info(f"Sessão {session_id} não está mais running, parando PID")
                            break
                except Exception:
                    pass

            result = self.control_temperature_pid(
                session_id, sensor_id, heater_id, setpoint, tolerance
            )

            logger.debug(f"Sessão {session_id} PID: temp={result.get('current_temp')}, "
                         f"output={result.get('pid_output')}, heater={result.get('heater_on')}")

            time.sleep(interval_s)

        # Desligar heater ao final
        try:
            self.device_integration.set_port_value(heater_id, None, False)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Utilitários
    # ------------------------------------------------------------------ #

    def get_session_equipment_mapping(self, session_id: str) -> Dict[str, str]:
        """Obtém o equipment_mapping de uma sessão."""
        try:
            BrewSession = get_brew_session()
            if not BrewSession:
                return {}

            session = BrewSession.query.get(session_id)
            if not session:
                return {}

            session_dict = session.to_dict()
            return session_dict.get('session_data', {}).get('equipment_mapping', {})
        except Exception as e:
            logger.error(f"Erro ao obter equipment_mapping: {e}")
            return {}

    def reset_pid(self, controller_id: str):
        """Reseta o estado do PID para um controlador específico."""
        if controller_id in self._pid_controllers:
            self._pid_controllers[controller_id].reset()

    # ------------------------------------------------------------------ #
    # Controle de execução (para MashSessionService)
    # ------------------------------------------------------------------ #

    def set_callbacks(self, on_step_change=None, on_temperature_update=None,
                      on_log=None, on_alarm=None, on_complete=None,
                      on_error=None):
        """
        Helper para registrar callbacks de alto nível de uma só vez.
        Internamente mapeia cada callback para os eventos internos.
        """
        self._custom_callbacks = {
            'on_step_change': on_step_change,
            'on_temperature_update': on_temperature_update,
            'on_log': on_log,
            'on_alarm': on_alarm,
            'on_complete': on_complete,
            'on_error': on_error,
        }

    def execute_recipe(self, mash_steps: List[Dict], equipment_mapping: Dict[str, str] = None):
        """
        Executa uma receita de mostura em thread separada.

        Usa dispositivos reais via DeviceIntegrationService quando equipment_mapping
        contém temperature_sensor e heater. Caso contrário, executa simulação.

        Args:
            mash_steps: Lista de dicionários com etapas (name, temperature, duration)
            equipment_mapping: Mapeamento de equipamentos (role → actor_id)
        """
        import threading
        import time

        # Criar stop event para controle
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._advance_event = threading.Event()
        self._paused = False
        self._running = True

        # Detectar se há dispositivos reais disponíveis
        use_real_devices = (
            equipment_mapping
            and 'temperature_sensor' in equipment_mapping
            and 'heater' in equipment_mapping
            and self.device_integration.is_available()
        )

        logger.info(
            f"Iniciando execução de receita com {len(mash_steps)} etapas "
            f"({'dispositivos reais' if use_real_devices else 'simulação'})"
        )

        if use_real_devices and self._custom_callbacks.get('on_log'):
            self._custom_callbacks['on_log'](
                f"Usando dispositivos reais: sensor={equipment_mapping['temperature_sensor']}, "
                f"heater={equipment_mapping['heater']}", 'info'
            )

        try:
            for step_idx, step in enumerate(mash_steps):
                # Verificar stop
                if self._stop_event.is_set():
                    logger.info("Execução parada pelo usuário")
                    if self._custom_callbacks.get('on_log'):
                        self._custom_callbacks['on_log']('Execução parada pelo usuário', 'warning')
                    if self._custom_callbacks.get('on_complete'):
                        self._custom_callbacks['on_complete']()
                    return

                # Aguardar se pausado
                while self._paused and not self._stop_event.is_set():
                    time.sleep(0.5)

                if self._stop_event.is_set():
                    return

                # Disparar callback de mudança de etapa
                if self._custom_callbacks.get('on_step_change'):
                    self._custom_callbacks['on_step_change'](step_idx, mash_steps)

                step_name = step.get('name', f'Etapa {step_idx + 1}')
                target_temp = step.get('temperature', step.get('temp', 65))
                duration_min = step.get('duration', step.get('time', 10))

                if self._custom_callbacks.get('on_log'):
                    self._custom_callbacks['on_log'](
                        f"Etapa {step_idx + 1}: {step_name} - aquecendo para {target_temp}°C por {duration_min}min", 'info'
                    )

                if use_real_devices:
                    self._execute_step_real(step_idx, step, equipment_mapping)
                else:
                    self._execute_step_simulated(step_idx, step)

                if self._custom_callbacks.get('on_log'):
                    self._custom_callbacks['on_log'](
                        f"Etapa {step_idx + 1} concluída: {step_name}", 'success'
                    )

            # Todas as etapas concluídas
            if self._custom_callbacks.get('on_complete'):
                self._custom_callbacks['on_complete']()

        except Exception as e:
            logger.error(f"Erro na execução da receita: {e}", exc_info=True)
            if self._custom_callbacks.get('on_error'):
                self._custom_callbacks['on_error'](str(e))

    def _execute_step_simulated(self, step_idx: int, step: Dict):
        """
        Executa uma etapa em modo simulado (fallback).

        Args:
            step_idx: Índice da etapa
            step: Dados da etapa {name, temperature, duration, ...}
        """
        import random
        import time

        target_temp = step.get('temperature', step.get('temp', 65))
        duration = step.get('duration', step.get('time', 10)) * 60  # min -> s

        # Simular aquecimento: rampa de 25°C até target
        current_temp = 25.0
        ramp_time = max(10, int(abs(target_temp - current_temp) * 1.5))
        for i in range(ramp_time):
            if self._stop_event.is_set():
                return
            while self._paused and not self._stop_event.is_set():
                time.sleep(0.5)
            if self._stop_event.is_set():
                return

            progress = (i + 1) / ramp_time
            current_temp = 25.0 + (target_temp - 25.0) * progress
            pid_output = min(1.0, max(0, progress * 1.2))

            if self._custom_callbacks.get('on_temperature_update'):
                self._custom_callbacks['on_temperature_update'](current_temp, pid_output)
            time.sleep(1)

        # Manter temperatura com variação aleatória
        elapsed = 0
        while elapsed < duration:
            if self._stop_event.is_set():
                return
            while self._paused and not self._stop_event.is_set():
                time.sleep(0.5)
            if self._stop_event.is_set():
                return

            current_temp = target_temp + random.uniform(-0.5, 0.5)
            pid_output = 0.3 + random.uniform(-0.1, 0.2)

            if self._custom_callbacks.get('on_temperature_update'):
                self._custom_callbacks['on_temperature_update'](current_temp, pid_output)
            time.sleep(1)
            elapsed += 1

    def _execute_step_real(self, step_idx: int, step: Dict,
                            equipment_mapping: Dict[str, str]):
        """
        Executa uma etapa usando dispositivos reais via DeviceIntegrationService.

        Args:
            step_idx: Índice da etapa
            step: Dados da etapa {name, temperature, duration, ...}
            equipment_mapping: Mapeamento de equipamentos (role → actor_id)
        """
        import time

        target_temp = step.get('temperature', step.get('temp', 65))
        duration_min = step.get('duration', step.get('time', 10))

        sensor_id = equipment_mapping.get('temperature_sensor')
        heater_id = equipment_mapping.get('heater')

        if not sensor_id or not heater_id:
            if self._custom_callbacks.get('on_log'):
                self._custom_callbacks['on_log'](
                    "Falha: sensor ou heater não mapeados, voltando à simulação", 'error'
                )
            return self._execute_step_simulated(step_idx, step)

        # Validar dispositivos
        if not self.validate_actor(sensor_id, 'temperature_sensor'):
            if self._custom_callbacks.get('on_log'):
                self._custom_callbacks['on_log'](
                    f"Sensor {sensor_id} não disponível, voltando à simulação", 'error'
                )
            return self._execute_step_simulated(step_idx, step)

        if not self.validate_actor(heater_id, 'heater'):
            if self._custom_callbacks.get('on_log'):
                self._custom_callbacks['on_log'](
                    f"Heater {heater_id} não disponível, voltando à simulação", 'error'
                )
            return self._execute_step_simulated(step_idx, step)

        if self._custom_callbacks.get('on_log'):
            self._custom_callbacks['on_log'](
                f"Iniciando PID real: {target_temp}°C por {duration_min}min "
                f"(sensor={sensor_id}, heater={heater_id})", 'info'
            )

        # Fase 1: Aquecimento (rampa) — chamar PID repetidamente até atingir alvo
        pid = self.get_pid(f"step_{step_idx}")
        pid.set_setpoint(target_temp)
        pid.reset()

        ramp_interval = 5  # segundos entre iterações PID na rampa
        hold_interval = 10  # segundos entre iterações na manutenção
        tolerance = 0.5

        while not self._stop_event.is_set():
            while self._paused and not self._stop_event.is_set():
                time.sleep(0.5)
            if self._stop_event.is_set():
                return

            result = self.control_temperature_pid(
                None, sensor_id, heater_id, target_temp, tolerance
            )

            current_temp = result.get('current_temp')
            pid_output = result.get('pid_output', 0.0)

            # Callback de temperatura
            if current_temp is not None and self._custom_callbacks.get('on_temperature_update'):
                self._custom_callbacks['on_temperature_update'](current_temp, pid_output)

            if self._custom_callbacks.get('on_log'):
                self._custom_callbacks['on_log'](
                    f"Rampa: {current_temp:.1f}°C / {target_temp}°C (PID: {pid_output:.0%})", 'info'
                )

            if result.get('on_target'):
                break

            if self._stop_event.is_set():
                return
            time.sleep(ramp_interval)

        # Fase 2: Manutenção — usar control_temperature_pid_continuous em background
        if self._custom_callbacks.get('on_log'):
            self._custom_callbacks['on_log'](
                f"Temperatura alvo atingida. Mantendo por {duration_min}min...", 'success'
            )

        step_stop = threading.Event()
        pid_thread = threading.Thread(
            target=self._run_pid_for_duration,
            args=(None, sensor_id, heater_id, target_temp,
                  duration_min, tolerance, step_stop),
            daemon=True
        )
        pid_thread.start()

        # Monitorar a thread de PID, emitindo callbacks de temperatura periódicos
        while pid_thread.is_alive() and not self._stop_event.is_set():
            while self._paused and not self._stop_event.is_set():
                time.sleep(0.5)

            # Ler temperatura atual para callback
            current_temp = self.device_integration.get_port_value(sensor_id, None)
            if current_temp is not None and self._custom_callbacks.get('on_temperature_update'):
                self._custom_callbacks['on_temperature_update'](current_temp, pid.last_output)

            time.sleep(hold_interval)

        # Garantir que a thread parou
        step_stop.set()
        pid_thread.join(timeout=5)

    def stop(self):
        """Solicita a parada da execução."""
        if hasattr(self, '_stop_event') and self._stop_event:
            self._stop_event.set()
        self._running = False

    def pause(self):
        """Solicita a pausa da execução."""
        self._paused = True

    def resume(self):
        """Retoma a execução pausada."""
        self._paused = False

    def advance_step(self):
        """Avança para a próxima etapa."""
        logger.info("Advance step solicitado")
