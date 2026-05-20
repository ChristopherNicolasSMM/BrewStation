"""
Testes unitários para PlantService (Fase 1.4).

Cobre CRUD de plantas, validação de atores, fallback quando
device_manager não está disponível, e resolução de papéis.

Para executar:
    cd src && pytest tests/test_plants.py -v
"""

from unittest.mock import patch

import pytest

# =============================================================================
# Helpers
# =============================================================================

def _criar_plant_no_banco(app, plant_service, nome="Test Plant"):
    """Cria uma plant válida e retorna o dicionário."""
    with app.app_context():
        return plant_service.create_plant(
            name=nome,
            description="Descrição de teste",
            device_roles={},
            user_id=1
        )


# =============================================================================
# Testes de Criação
# =============================================================================

class TestCreatePlant:
    """Testes para criação de plantas."""

    def test_create_plant_success(self, app, db, plant_service):
        """Cria uma plant com sucesso."""
        plant = _criar_plant_no_banco(app, plant_service)
        assert plant is not None
        assert plant['name'] == 'Test Plant'
        assert plant['description'] == 'Descrição de teste'
        assert plant['device_roles'] == {}
        assert plant['is_active'] is True
        assert 'id' in plant
        assert 'created_at' in plant

    def test_create_plant_with_roles(self, app, db, plant_service):
        """Cria plant com mapeamento de dispositivos válido."""
        with app.app_context():
            with patch(
                'plugins.plugin_device_manager.utils.device_api.DeviceAPI.get_actor'
            ) as mock_get_actor:
                mock_get_actor.return_value = {
                    'id': 'actor-001', 'name': 'Sensor Temp'
                }

                device_roles = {
                    'temperature_sensor': 'actor-001',
                    'heater': 'actor-002'
                }
                plant = plant_service.create_plant(
                    name='Plant com Ator',
                    description='Com dispositivos',
                    device_roles=device_roles,
                    user_id=1
                )

        assert plant is not None
        assert plant['device_roles'] == device_roles

    def test_create_plant_invalid_actor_raises_error(self, app, db, plant_service):
        """Criação rejeita actor_id que não existe."""
        with app.app_context():
            with patch(
                'plugins.plugin_device_manager.utils.device_api.DeviceAPI.get_actor'
            ) as mock_get_actor:
                mock_get_actor.return_value = None

                with pytest.raises(ValueError) as exc:
                    plant_service.create_plant(
                        name='Plant Inválida',
                        description='',
                        device_roles={'temperature_sensor': 'actor-inexistente'},
                        user_id=1
                    )
                assert 'não encontrado' in str(exc.value)

    def test_create_plant_empty_roles_valid(self, app, db, plant_service):
        """Cria plant sem device_roles (válido)."""
        with app.app_context():
            plant = plant_service.create_plant(
                name='Plant sem roles',
                description='',
                device_roles={},
                user_id=1
            )
        assert plant is not None

    def test_create_plant_none_roles_valid(self, app, db, plant_service):
        """Cria plant com device_roles=None (tratado como {})."""
        with app.app_context():
            plant = plant_service.create_plant(
                name='Plant None roles',
                description='',
                device_roles=None,
                user_id=1
            )
        assert plant is not None
        assert plant['device_roles'] == {}  # None é convertido para {} pelo serviço

    def test_create_plant_without_user_id(self, app, db, plant_service):
        """Cria plant sem user_id."""
        with app.app_context():
            plant = plant_service.create_plant(
                name='Plant sem dono',
                description='Anônima'
            )
        assert plant is not None
        assert plant['user_id'] is None


# =============================================================================
# Testes de Leitura/Listagem
# =============================================================================

class TestGetPlant:
    """Testes para leitura de plantas."""

    def test_get_plant_by_id(self, app, db, plant_service):
        """Obtém plant pelo ID."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            retrieved = plant_service.get_plant(created['id'])
        assert retrieved is not None
        assert retrieved['id'] == created['id']
        assert retrieved['name'] == created['name']

    def test_get_plant_not_found(self, app, db, plant_service):
        """Retorna None para ID inexistente."""
        with app.app_context():
            result = plant_service.get_plant('id-inexistente')
        assert result is None


class TestListPlants:
    """Testes para listagem de plantas."""

    def test_list_all_plants(self, app, db, plant_service):
        """Lista todas as plantas."""
        _criar_plant_no_banco(app, plant_service, "Plant A")
        _criar_plant_no_banco(app, plant_service, "Plant B")
        with app.app_context():
            plants = plant_service.list_plants()
        assert len(plants) == 2

    def test_list_plants_filter_by_user(self, app, db, plant_service):
        """Filtra plantas por user_id."""
        with app.app_context():
            plant_service.create_plant(name="User1 Plant", user_id=10)
            plant_service.create_plant(name="User2 Plant", user_id=20)

            user1_plants = plant_service.list_plants(user_id=10)
            assert len(user1_plants) == 1
            assert user1_plants[0]['user_id'] == 10

    def test_list_plants_inactive_excluded(self, app, db, plant_service):
        """Lista apenas plantas ativas (padrão)."""
        with app.app_context():
            plant_service.create_plant(name="Ativa", user_id=1)
            p2 = plant_service.create_plant(name="Desativada", user_id=1)
            plant_service.update_plant(p2['id'], is_active=False)

            plants = plant_service.list_plants()
            names = [p['name'] for p in plants]
        assert 'Ativa' in names
        assert 'Desativada' not in names

    def test_list_plants_empty(self, app, db, plant_service):
        """Retorna lista vazia quando não há plantas."""
        with app.app_context():
            plants = plant_service.list_plants()
        assert plants == []


# =============================================================================
# Testes de Atualização
# =============================================================================

class TestUpdatePlant:
    """Testes para atualização de plantas."""

    def test_update_plant_name(self, app, db, plant_service):
        """Atualiza nome da plant."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            updated = plant_service.update_plant(created['id'], name='Novo Nome')
        assert updated is not None
        assert updated['name'] == 'Novo Nome'

    def test_update_plant_description(self, app, db, plant_service):
        """Atualiza descrição da plant."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            updated = plant_service.update_plant(
                created['id'], description='Nova descrição'
            )
        assert updated['description'] == 'Nova descrição'

    def test_update_plant_deactivate(self, app, db, plant_service):
        """Desativa uma plant."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            updated = plant_service.update_plant(created['id'], is_active=False)
        assert updated['is_active'] is False

    def test_update_plant_roles(self, app, db, plant_service):
        """Atualiza device_roles com atores válidos."""
        created = _criar_plant_no_banco(app, plant_service)
        new_roles = {'temperature_sensor': 'actor-003'}
        with app.app_context():
            with patch(
                'plugins.plugin_device_manager.utils.device_api.DeviceAPI.get_actor'
            ) as mock_get_actor:
                mock_get_actor.return_value = {
                    'id': 'actor-003', 'name': 'Sensor'
                }
                updated = plant_service.update_plant(
                    created['id'], device_roles=new_roles
                )
        assert updated['device_roles'] == new_roles

    def test_update_plant_invalid_roles(self, app, db, plant_service):
        """Rejeita device_roles com ator inexistente."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            with patch(
                'plugins.plugin_device_manager.utils.device_api.DeviceAPI.get_actor'
            ) as mock_get_actor:
                mock_get_actor.return_value = None

                with pytest.raises(ValueError):
                    plant_service.update_plant(
                        created['id'],
                        device_roles={'temperature_sensor': 'bad-actor'}
                    )

    def test_update_plant_not_found(self, app, db, plant_service):
        """Retorna None para plant inexistente."""
        with app.app_context():
            result = plant_service.update_plant('id-invalido', name='X')
        assert result is None


# =============================================================================
# Testes de Deleção
# =============================================================================

class TestDeletePlant:
    """Testes para remoção de plantas."""

    def test_delete_plant(self, app, db, plant_service):
        """Deleta plant existente."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            result = plant_service.delete_plant(created['id'])
        assert result is True
        with app.app_context():
            assert plant_service.get_plant(created['id']) is None

    def test_delete_plant_not_found(self, app, db, plant_service):
        """Retorna False para plant inexistente."""
        with app.app_context():
            result = plant_service.delete_plant('id-inexistente')
        assert result is False

    def test_delete_plant_twice(self, app, db, plant_service):
        """Deletar plant já deletada retorna False."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            plant_service.delete_plant(created['id'])
            result = plant_service.delete_plant(created['id'])
        assert result is False


# =============================================================================
# Testes de Atribuição e Resolução de Papéis
# =============================================================================

class TestAssignRole:
    """Testes para assign_role."""

    def test_assign_role_success(self, app, db, plant_service):
        """Atribui papel a dispositivo."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            with patch(
                'plugins.plugin_device_manager.utils.device_api.DeviceAPI.get_actor'
            ) as mock_get_actor:
                mock_get_actor.return_value = {
                    'id': 'actor-pump', 'name': 'Bomba'
                }
                result = plant_service.assign_role(
                    created['id'], 'pump', 'actor-pump'
                )
        assert result is not None
        assert result['device_roles'].get('pump') == 'actor-pump'

    def test_assign_role_not_found(self, app, db, plant_service):
        """Retorna None para plant inexistente."""
        result = plant_service.assign_role('id-invalido', 'pump', 'actor-1')
        assert result is None

    def test_assign_role_twice(self, app, db, plant_service):
        """Substitui papel já atribuído."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            with patch(
                'plugins.plugin_device_manager.utils.device_api.DeviceAPI.get_actor'
            ) as mock_get_actor:
                mock_get_actor.return_value = {'id': 'actor-x'}
                plant_service.assign_role(created['id'], 'heater', 'actor-old')
                plant_service.assign_role(created['id'], 'heater', 'actor-new')

                plant = plant_service.get_plant(created['id'])
        assert plant['device_roles']['heater'] == 'actor-new'


class TestResolveDevice:
    """Testes para resolve_device."""

    def test_resolve_device_found(self, app, db, plant_service):
        """Resolve device_id para um papel."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            with patch(
                'plugins.plugin_device_manager.utils.device_api.DeviceAPI.get_actor'
            ) as mock_get_actor:
                mock_get_actor.return_value = {'id': 'dev-sensor'}
                plant_service.assign_role(
                    created['id'], 'temperature_sensor', 'dev-sensor'
                )
                device_id = plant_service.resolve_device(
                    created['id'], 'temperature_sensor'
                )
        assert device_id == 'dev-sensor'

    def test_resolve_device_not_found(self, app, db, plant_service):
        """Retorna None para papel não atribuído."""
        created = _criar_plant_no_banco(app, plant_service)
        with app.app_context():
            device_id = plant_service.resolve_device(created['id'], 'pump')
        assert device_id is None

    def test_resolve_device_plant_not_found(self, app, db, plant_service):
        """Retorna None para plant inexistente."""
        result = plant_service.resolve_device('bad-id', 'heater')
        assert result is None


# =============================================================================
# Testes de Fallback (DeviceAPI indisponível)
# =============================================================================

class TestDeviceAPIFallback:
    """Testa comportamento quando device_manager não está instalado."""

    def test_create_plant_when_device_api_unavailable(self, app, db, plant_service):
        """
        Cria plant mesmo com device_manager ausente.
        Simula ImportError no DeviceAPI (import dentro de _validar_atores).
        """
        with app.app_context():
            with patch(
                'plugins.plugin_device_manager.utils.device_api.DeviceAPI.get_actor',
                side_effect=ImportError("plugin not installed")
            ):
                # Deve criar sem validar atores
                plant = plant_service.create_plant(
                    name='Plant s/ DeviceAPI',
                    device_roles={'temperature_sensor': 'actor-001'},
                    user_id=1
                )
        assert plant is not None
        # A validação foi ignorada, então roles foram salvos mesmo sem DeviceAPI
        assert plant['device_roles']['temperature_sensor'] == 'actor-001'

    def test_import_error_handling(self, app, db, plant_service):
        """_validar_atores não quebra quando DeviceAPI não pode ser importado."""
        # O serviço lida com ImportError internamente e loga warning
        # Verificar que a criação funciona mesmo quando plugin não está disponível
        with app.app_context():
            with patch(
                'plugins.plugin_device_manager.utils.device_api.DeviceAPI.get_actor',
                side_effect=ImportError("plugin not installed")
            ):
                plant = plant_service.create_plant(
                    name='Fallback OK',
                    device_roles={'heater': 'actor-999'},
                    user_id=1
                )
        assert plant is not None
