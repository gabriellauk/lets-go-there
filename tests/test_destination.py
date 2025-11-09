import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_create_destination() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        request_body = {
            "name": "Alhambra",
            "description": "Granada, Spain",
            "imageId": "img_123",
            "notes": "A beautiful palace",
        }

        response = await ac.post("/destination/", json=request_body)

    assert response.status_code == 200
    response_json = response.json()
    assert "id" in response_json
    assert response_json["name"] == request_body["name"]
    assert response_json["description"] == request_body["description"]
    assert response_json["imageId"] == request_body["imageId"]
    assert response_json["notes"] == request_body["notes"]
