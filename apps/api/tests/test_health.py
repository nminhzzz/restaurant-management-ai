from fastapi.testclient import TestClient

from app.main import MODULE_ROUTERS


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_reports_the_payment_gateway_without_secrets(client: TestClient) -> None:
    payment = client.get("/health").json()["payment"]

    assert payment["gateway"] == "simulator"
    assert payment["live"] is False
    assert "webhook_api_key" not in payment


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
