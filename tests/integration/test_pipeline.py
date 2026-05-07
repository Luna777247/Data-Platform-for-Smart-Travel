import pytest
from unittest.mock import AsyncMock, patch
from src.transformers.bronze_processor import BronzeProcessor
from src.transformers.silver_processor import SilverTransformer
from src.transformers.gold_processor import GoldProcessor


@pytest.mark.asyncio
async def test_full_pipeline_flow():
    """Test the complete Bronze → Silver → Gold pipeline"""

    # Mock MongoDB client
    mock_client = AsyncMock()

    # Mock collections
    mock_bronze = AsyncMock()
    mock_silver = AsyncMock()
    mock_gold = AsyncMock()

    mock_client.smart_travel.places_bronze = mock_bronze
    mock_client.smart_travel.places_silver = mock_silver
    mock_client.smart_travel.places_gold = mock_gold

    # Setup mock data for Silver to find
    mock_bronze.find.return_value.to_list.return_value = [
        {
            "_id": "test_id",
            "source_id": "osm1",
            "raw_data": {
                "tags": {"name": "Test Attraction", "tourism": "attraction"},
                "center": {"lat": 21.0, "lon": 105.0},
            },
            "collected_at": "2023-01-01T00:00:00",
            "city": "hanoi",
            "source": "osm",
        }
    ]

    # Setup mock data for Gold to find
    mock_silver.find.return_value.to_list.return_value = [
        {
            "_id": "silver_id",
            "source_id": "osm1",
            "raw_data": {
                "tags": {"name": "Test Attraction", "tourism": "attraction"},
                "center": {"lat": 21.0, "lon": 105.0},
            },
            "collected_at": "2023-01-01T00:00:00",
            "city": "hanoi",
            "source": "osm",
            "name": "Test Attraction",
            "address": "123 Test St",
            "latitude": 21.0,
            "longitude": 105.0,
            "categories": ["attraction"],
            "deduplication_key": "test_attraction_21.0_105.0",
        }
    ]

    # Test Bronze processor
    bronze_processor = BronzeProcessor(mock_client)
    bronze_count = await bronze_processor.process([])
    assert bronze_count == 0

    # Test Silver processor
    silver_transformer = SilverTransformer(mock_client)
    silver_count = await silver_transformer.process("hanoi")
    assert silver_count == 1

    # Test Gold processor
    gold_processor = GoldProcessor(mock_client)
    gold_count = await gold_processor.process("hanoi")
    assert gold_count == 1

    # Verify data was inserted into gold collection
    mock_gold.insert_many.assert_called_once()
    inserted_data = mock_gold.insert_many.call_args[0][0][0]

    assert inserted_data["name"] == "Test Attraction"
    assert inserted_data["city"] == "hanoi"
    assert "quality_score" in inserted_data
    assert "business_metrics" in inserted_data
