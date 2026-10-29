def test_root_endpoint(client):
    """Test GET / returns welcoming information and documentation link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "CrowdAhead"
    assert data["docs_url"] == "/docs"


def test_health_check(client):
    """Test GET /api/health returns healthy status and connected database."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "ByteTrack" in data["tracking_engine"]
