import pytest
from unittest.mock import AsyncMock, patch
from src.collectors.osm_collector import OSMCollector
from src.collectors.google_enricher import GoogleEnricher


@pytest.mark.asyncio
async def test_osm_collector():
    collector = OSMCollector("hanoi")

    # Mock the HTTP response
    mock_response = {
        "elements": [
            {
                "id": 123,
                "tags": {"name": "Test Place", "tourism": "attraction"},
                "center": {"lat": 21.0285, "lon": 105.8542},
            }
        ]
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.post.return_value.json.return_value = mock_response
        mock_client.return_value = mock_instance

        places = await collector.collect()

        assert len(places) == 1
        assert places[0].raw_data["tags"]["name"] == "Test Place"
        assert places[0].city == "hanoi"
        assert places[0].source == "osm"


@pytest.mark.asyncio
async def test_google_enricher():
    enricher = GoogleEnricher("hanoi", "fake-api-key")

    mock_response = {
        "results": [
            {
                "place_id": "test123",
                "name": "Test Google Place",
                "formatted_address": "123 Test St, Hanoi",
                "geometry": {"location": {"lat": 21.0285, "lng": 105.8542}},
                "types": ["restaurant", "food"],
            }
        ]
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.get.return_value.json.return_value = mock_response
        mock_client.return_value = mock_instance

        places = await enricher.enrich()

        assert len(places) == 1
        assert places[0].raw_data["name"] == "Test Google Place"
        assert places[0].source == "google"
