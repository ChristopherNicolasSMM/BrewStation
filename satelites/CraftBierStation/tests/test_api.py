from src.interfaces.rest_api import RESTAPI


def test_health_endpoint():
    api = RESTAPI({'host': '127.0.0.1', 'port': 5002}, {}, {})
    client = api.app.test_client()
    resp = client.get('/api/health')
    assert resp.status_code == 200
