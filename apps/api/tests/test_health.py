from fastapi.testclient import TestClient

from app.main import MODULE_ROUTERS


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_every_business_module_is_mounted() -> None:
    prefixes = {router.prefix for router in MODULE_ROUTERS}

    assert prefixes == {
        "/catalog",
        "/sales",
        "/inventory",
        "/reports",
        "/settings",
        "/assistant",
    }
