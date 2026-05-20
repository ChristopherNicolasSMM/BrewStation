"""
Testes para as rotas de Dashboard CRUD.

Cobre operações básicas de layout (criar, carregar, listar, definir padrão,
excluir) e verifica respostas da API.

NOTA: Os testes utilizam DashboardLayout e Plant diretamente dos modelos
(prefixo "mash_ctrl_" ignorado em SQLite :memory:).
"""

import uuid

from flask import Flask

# ==============================================================================
# Helpers
# ==============================================================================

def _register_bp(app: Flask) -> Flask:
    """Registra o blueprint de mash_routes se ainda não registrado."""
    if 'plugin_mash_control_mash_api' not in app.blueprints:
        from plugins.plugin_mash_control.api.routes.mash_routes import mash_bp
        app.register_blueprint(mash_bp, url_prefix='/api/mash_control')
    return app


# ==============================================================================
# Test: POST /api/mash_control/dashboard/layout  – criar/atualizar layout
# ==============================================================================

class TestCreateLayout:
    def test_create_minimal_layout(self, app, db, client):
        _register_bp(app)
        resp = client.post('/api/mash_control/dashboard/layout', json={
            'name': 'Meu Dashboard',
            'elements': [{'id': 'el1', 'type': 'kettle', 'x': 10, 'y': 20}]
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'id' in data
        assert data['message'] == 'Layout salvo'

    def test_create_layout_no_name(self, app, db, client):
        _register_bp(app)
        resp = client.post('/api/mash_control/dashboard/layout', json={
            'elements': [{'id': 'el1'}]
        })
        assert resp.status_code == 200  # aceita nome padrão
        data = resp.get_json()
        assert 'id' in data

    def test_create_layout_empty_elements(self, app, db, client):
        _register_bp(app)
        resp = client.post('/api/mash_control/dashboard/layout', json={
            'name': 'Vazio',
            'elements': []
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'id' in data


# ==============================================================================
# Test: GET /api/mash_control/dashboard/layout  – carregar layout
# ==============================================================================

class TestGetLayout:
    def test_get_default_layout_when_none(self, app, db, client):
        _register_bp(app)
        resp = client.get('/api/mash_control/dashboard/layout')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] is None
        assert data['elements'] == []

    def test_get_layout_by_id(self, app, db, client):
        _register_bp(app)
        # Criar layout primeiro
        create_resp = client.post('/api/mash_control/dashboard/layout', json={
            'name': 'Por ID',
            'elements': [{'id': 'x1', 'type': 'pump'}]
        })
        layout_id = create_resp.get_json()['id']

        # Buscar por ID
        resp = client.get(f'/api/mash_control/dashboard/layout?layout_id={layout_id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == layout_id
        assert len(data['elements']) == 1
        assert data['elements'][0]['id'] == 'x1'

    def test_get_layout_not_found(self, app, db, client):
        _register_bp(app)
        resp = client.get('/api/mash_control/dashboard/layout?layout_id=nonexistent')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] is None  # fallback para layout vazio


# ==============================================================================
# Test: GET /api/mash_control/dashboard/layouts  – listar layouts
# ==============================================================================

class TestListLayouts:
    def test_list_layouts_empty(self, app, db, client):
        _register_bp(app)
        resp = client.get('/api/mash_control/dashboard/layouts')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == []

    def test_list_layouts_with_data(self, app, db, client):
        _register_bp(app)
        # Criar dois layouts
        client.post('/api/mash_control/dashboard/layout', json={
            'name': 'Layout A',
            'elements': [{'id': 'a1'}]
        })
        client.post('/api/mash_control/dashboard/layout', json={
            'name': 'Layout B',
            'elements': [{'id': 'b1'}]
        })

        resp = client.get('/api/mash_control/dashboard/layouts')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 2
        names = [d['name'] for d in data]
        assert 'Layout A' in names
        assert 'Layout B' in names


# ==============================================================================
# Test: POST /api/mash_control/dashboard/layout/<id>/set-default
# ==============================================================================

class TestSetDefaultLayout:
    def test_set_default(self, app, db, client):
        _register_bp(app)
        # Criar dois layouts
        r1 = client.post('/api/mash_control/dashboard/layout', json={
            'name': 'First', 'elements': [], 'is_default': True
        })
        r2 = client.post('/api/mash_control/dashboard/layout', json={
            'name': 'Second', 'elements': [], 'is_default': False
        })
        r1.get_json()['id']
        id2 = r2.get_json()['id']

        # Definir o segundo como padrão
        resp = client.post(f'/api/mash_control/dashboard/layout/{id2}/set-default')
        assert resp.status_code == 200

        # Verificar que o layout padrão agora é o segundo
        default_resp = client.get('/api/mash_control/dashboard/layout')
        assert default_resp.get_json()['id'] == id2

    def test_set_default_not_found(self, app, db, client):
        _register_bp(app)
        resp = client.post('/api/mash_control/dashboard/layout/nonexistent/set-default')
        assert resp.status_code == 500


# ==============================================================================
# Test: DELETE /api/mash_control/dashboard/layout/<id>
# ==============================================================================

class TestDeleteLayout:
    def test_delete_layout(self, app, db, client):
        _register_bp(app)
        r = client.post('/api/mash_control/dashboard/layout', json={
            'name': 'Para Deletar', 'elements': []
        })
        layout_id = r.get_json()['id']

        resp = client.delete(f'/api/mash_control/dashboard/layout/{layout_id}')
        assert resp.status_code == 200
        assert resp.get_json()['message'] == 'Dashboard deletado'

        # Verificar que não está mais na lista
        list_resp = client.get('/api/mash_control/dashboard/layouts')
        ids = [d['id'] for d in list_resp.get_json()]
        assert layout_id not in ids

    def test_delete_not_found(self, app, db, client):
        _register_bp(app)
        resp = client.delete('/api/mash_control/dashboard/layout/nonexistent')
        assert resp.status_code == 500


# ==============================================================================
# Test: GET /api/mash_control/dashboard/components  – listar SVGs
# ==============================================================================

class TestGetComponents:
    def test_list_components(self, app, db, client):
        _register_bp(app)
        resp = client.get('/api/mash_control/dashboard/components')
        assert resp.status_code == 200
        data = resp.get_json()
        # Deve ter pelo menos alguns componentes SVG
        assert len(data) > 0
        # Cada componente deve ter os campos esperados
        for comp in data:
            assert 'type' in comp
            assert 'name' in comp
            assert 'label' in comp
            assert 'category' in comp
            assert 'default_size' in comp


# ==============================================================================
# Test: PUT /api/mash_control/dashboard/layout/<id>/element/<el>/position
# ==============================================================================

class TestElementPosition:
    def test_update_position(self, app, db, client):
        _register_bp(app)
        r = client.post('/api/mash_control/dashboard/layout', json={
            'name': 'PosTest',
            'elements': [{'id': 'movel', 'type': 'sensor', 'x': 0, 'y': 0}]
        })
        layout_id = r.get_json()['id']

        resp = client.put(
            f'/api/mash_control/dashboard/layout/{layout_id}/element/movel/position',
            json={'x': 100, 'y': 200}
        )
        assert resp.status_code == 200

        # Verificar que a posição foi atualizada
        layout_resp = client.get(f'/api/mash_control/dashboard/layout?layout_id={layout_id}')
        element = layout_resp.get_json()['elements'][0]
        assert element['x'] == 100
        assert element['y'] == 200

    def test_update_position_missing_coords(self, app, db, client):
        _register_bp(app)
        resp = client.put(
            '/api/mash_control/dashboard/layout/lid/element/eid/position',
            json={'x': 10}  # sem 'y'
        )
        assert resp.status_code == 400


# ==============================================================================
# Test: POST /api/mash_control/dashboard/layout/<id>/element/<el>/link-device
# ==============================================================================

class TestLinkDevice:
    def test_link_device(self, app, db, client):
        _register_bp(app)
        r = client.post('/api/mash_control/dashboard/layout', json={
            'name': 'LinkTest',
            'elements': [{'id': 'elink', 'type': 'kettle'}]
        })
        layout_id = r.get_json()['id']

        resp = client.post(
            f'/api/mash_control/dashboard/layout/{layout_id}/element/elink/link-device',
            json={'device_id': 'dev-123'}
        )
        assert resp.status_code == 200

    def test_link_device_missing_id(self, app, db, client):
        _register_bp(app)
        resp = client.post(
            '/api/mash_control/dashboard/layout/lid/element/eid/link-device',
            json={}
        )
        assert resp.status_code == 400


# ==============================================================================
# Test: GET /api/mash_control/dashboard/status
# ==============================================================================

class TestDashboardStatus:
    def test_status_empty(self, app, db, client):
        _register_bp(app)
        resp = client.get('/api/mash_control/dashboard/status')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'active_sessions' in data
        assert 'paused_sessions' in data
        assert 'total_sessions' in data

    def test_status_with_session(self, app, db, client):
        _register_bp(app)
        # Criar uma BrewSession manualmente
        from db.database import db
        from plugins.plugin_mash_control.model.mash_models import BrewSession

        session = BrewSession(
            id=str(uuid.uuid4()),
            name='Test Session',
            status='running',
            recipe_id=str(uuid.uuid4())
        )
        db.session.add(session)
        db.session.commit()

        resp = client.get('/api/mash_control/dashboard/status')
        data = resp.get_json()
        assert data['active_sessions'] >= 1

    def test_status_with_paused_session(self, app, db, client):
        _register_bp(app)
        from db.database import db
        from plugins.plugin_mash_control.model.mash_models import BrewSession

        session = BrewSession(
            id=str(uuid.uuid4()),
            name='Paused Session',
            status='paused',
            recipe_id=str(uuid.uuid4())
        )
        db.session.add(session)
        db.session.commit()

        resp = client.get('/api/mash_control/dashboard/status')
        data = resp.get_json()
        assert data['paused_sessions'] >= 1
        assert data['total_sessions'] >= 1


# ==============================================================================
# Test: GET /api/mash_control/dashboard/layout/<id>/telemetry
# ==============================================================================

class TestLayoutTelemetry:
    def test_telemetry_unlinked(self, app, db, client):
        _register_bp(app)
        r = client.post('/api/mash_control/dashboard/layout', json={
            'name': 'TelemetryTest',
            'elements': [{'id': 't1', 'type': 'sensor'}]  # sem device_id
        })
        layout_id = r.get_json()['id']

        resp = client.get(f'/api/mash_control/dashboard/layout/{layout_id}/telemetry')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'elements' in data
        assert data['elements'][0]['status'] == 'unlinked'

    def test_telemetry_layout_not_found(self, app, db, client):
        _register_bp(app)
        resp = client.get('/api/mash_control/dashboard/layout/nonexistent/telemetry')
        assert resp.status_code == 404
