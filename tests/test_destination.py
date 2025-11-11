import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_destination(client: AsyncClient, session: AsyncSession) -> None:
    request_body = {
        "name": "Alhambra",
        "description": "Granada, Spain",
        "imageId": "img_123",
        "notes": "A beautiful palace",
    }

    response = await client.post("/destination/", json=request_body)

    assert response.status_code == 200
    response_json = response.json()
    assert "id" in response_json
    assert response_json["name"] == request_body["name"]
    assert response_json["description"] == request_body["description"]
    assert response_json["imageId"] == request_body["imageId"]
    assert response_json["notes"] == request_body["notes"]
