from django.urls import reverse


def test_health_endpoint(client):
    response = client.get(reverse("api_v1:health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_schema_endpoint(client):
    response = client.get(reverse("api_v1:schema"))

    assert response.status_code == 200
    assert "application/vnd.oai.openapi" in response["Content-Type"]
    assert "openapi:" in response.content.decode()


def test_docs_endpoint(client):
    response = client.get(reverse("api_v1:docs"))

    assert response.status_code == 200
    assert "swagger-ui" in response.content.decode().lower()
