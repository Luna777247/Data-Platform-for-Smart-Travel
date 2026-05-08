import pytest
from unittest.mock import AsyncMock
from motor.motor_asyncio import AsyncIOMotorClient
from src.transformers.bronze_processor import BronzeProcessor
from src.transformers.silver_processor import SilverTransformer
from src.shared.data_contracts import BronzePlace
from datetime import datetime


@pytest.mark.asyncio
async def test_bronze_processor():
    # Mock MongoDB client
    mock_client = AsyncMock()
    mock_collection = AsyncMock()
    mock_client.smart_travel.places_bronze = mock_collection
    mock_result = AsyncMock()
    mock_result.inserted_ids = ["id1", "id2"]
    mock_collection.insert_many.return_value = mock_result

    processor = BronzeProcessor(mock_client)

    places = [
        BronzePlace(
            source_id="test1",
            raw_data={"test": "data"},
            collected_at=datetime.utcnow(),
            city="hanoi",
            source="osm",
        )
    ]

    count = await processor.process(places)

    assert count == 2
    mock_collection.insert_many.assert_called_once()


@pytest.mark.asyncio
async def test_silver_processor_deduplication():
    mock_client = AsyncMock()
    mock_bronze = AsyncMock()
    mock_silver = AsyncMock()

    mock_client.smart_travel.places_bronze = mock_bronze
    mock_client.smart_travel.places_silver = mock_silver

    # Mock bronze data with duplicates
    mock_bronze.find.return_value.to_list.return_value = [
        {
            "_id": "1",
            "source_id": "osm1",
            "raw_data": {
                "tags": {"name": "Test Place", "tourism": "attraction"},
                "center": {"lat": 21.0, "lon": 105.0},
            },
            "collected_at": datetime.utcnow(),
            "city": "hanoi",
            "source": "osm",
        },
        {
            "_id": "2",
            "source_id": "google1",
            "raw_data": {
                "name": "Test Place",
                "formatted_address": "123 St",
                "geometry": {"location": {"lat": 21.001, "lng": 105.001}},
            },
            "collected_at": datetime.utcnow(),
            "city": "hanoi",
            "source": "google",
        },
    ]

    transformer = SilverTransformer(mock_client)
    count = await transformer.process("hanoi")

    # Should deduplicate to 1 place if normalization logic matches
    assert count == 1
    mock_silver.insert_many.assert_called_once()
