import app2
import pytest

@pytest.fixture
def client():
    app2.app.config['TESTING'] = True
    with app2.app.test_client() as client:
        yield client

def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Your name" in response.data
