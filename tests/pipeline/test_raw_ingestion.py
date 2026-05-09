"""
Test Raw Ingestion Pipeline
============================
Unit tests cho raw ingestion pipeline components

Test Coverage:
- OSMIngestionEngine initialization và configuration
- Data fetching từ external APIs
- Bronze record creation và validation
- Error handling và retry mechanisms
"""

# Import pytest cho testing framework
import pytest

# Import datetime cho timestamp handling
from datetime import datetime

# Import typing cho type hints
from typing import Dict, Any, List

# Import unittest.mock cho mocking external calls
from unittest.mock import Mock, patch, AsyncMock

# Import pydantic cho validation testing
from pydantic import ValidationError

# Import ingestion engine cần test
from pipelines.ingestion.osm_ingestion import OSMIngestionEngine

# Import shared utilities
from pipelines.shared.utils import setup_logging, make_ukey


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
# Fixture cung cấp logger instance cho tests
def logger():
    """Provide configured logger for tests."""
    return setup_logging()


@pytest.fixture
# Fixture cung cấp sample city configuration
def sample_city_config():
    """Provide sample city configuration for testing."""
    return {
        "id": "tokyo",  # ID của thành phố
        "name": "Tokyo",  # Tên hiển thị
        "country": "Japan",  # Quốc gia
        "coordinates": {  # Tọa độ trung tâm
            "lat": 35.6762,
            "lon": 139.6503
        },
        "bounding_box": {  # Bounding box cho queries
            "min_lat": 35.5011,
            "max_lat": 35.8115,
            "min_lon": 139.5859,
            "max_lon": 139.9229
        }
    }


@pytest.fixture
# Fixture cung cấp sample POI type configuration
def sample_poi_config():
    """Provide sample POI type configuration for testing."""
    return {
        "id": "hotel",  # ID của loại POI
        "name": "Hotels & Accommodation",  # Tên hiển thị
        "osm_tags": ["tourism=hotel", "tourism=hostel"],  # OSM tags
        "enabled": True  # Trạng thái enabled
    }


@pytest.fixture
# Fixture cung cấp sample OSM API response
def sample_osm_response():
    """Provide sample OSM API response for mocking."""
    return {
        "version": 0.6,
        "generator": "Overpass API",
        "elements": [
            {
                "type": "node",
                "id": 12345,
                "lat": 35.6762,
                "lon": 139.6503,
                "tags": {
                    "name": "Test Hotel",
                    "tourism": "hotel",
                    "addr:city": "Tokyo"
                }
            }
        ]
    }


@pytest.fixture
# Fixture khởi tạo OSMIngestionEngine instance
def ingestion_engine(logger):
    """Create OSMIngestionEngine instance for testing."""
    engine = OSMIngestionEngine()
    return engine


# =============================================================================
# Test Class: OSMIngestionEngine Initialization
# =============================================================================

class TestOSMIngestionEngineInit:
    """Test OSMIngestionEngine initialization và configuration."""
    
    def test_engine_initialization(self, logger):
        """Test rằng engine được khởi tạo đúng cách."""
        # Khởi tạo engine
        engine = OSMIngestionEngine()
        
        # Assert engine được tạo thành công
        assert engine is not None
        
        # Assert engine có logger
        assert engine.logger is not None
        
        # Assert các thuộc tính mặc định
        assert engine.configs_dir == "pipelines/config"
        assert engine.bronze_dir == "storage/bronze"
    
    def test_engine_with_custom_config(self, logger):
        """Test engine khởi tạo với custom config."""
        # Khởi tạo với custom directories
        engine = OSMIngestionEngine(
            configs_dir="custom/configs",
            bronze_dir="custom/bronze"
        )
        
        # Assert custom config được áp dụng
        assert engine.configs_dir == "custom/configs"
        assert engine.bronze_dir == "custom/bronze"


# =============================================================================
# Test Class: Configuration Loading
# =============================================================================

class TestConfigurationLoading:
    """Test configuration loading từ JSON files."""
    
    @pytest.mark.asyncio
    async def test_load_city_configs(self, ingestion_engine):
        """Test loading city configurations."""
        # Load city configs
        cities = await ingestion_engine._load_city_configs()
        
        # Assert cities là list
        assert isinstance(cities, list)
        
        # Assert có ít nhất một city được load
        assert len(cities) > 0
        
        # Assert mỗi city có required fields
        for city in cities:
            assert "id" in city
            assert "name" in city
            assert "coordinates" in city
    
    @pytest.mark.asyncio
    async def test_load_poi_type_configs(self, ingestion_engine):
        """Test loading POI type configurations."""
        # Load POI type configs
        poi_types = await ingestion_engine._load_poi_type_configs()
        
        # Assert poi_types là list
        assert isinstance(poi_types, list)
        
        # Assert có ít nhất một POI type được load
        assert len(poi_types) > 0
        
        # Assert mỗi POI type có required fields
        for poi_type in poi_types:
            assert "id" in poi_type
            assert "name" in poi_type
            assert "osm_tags" in poi_type


# =============================================================================
# Test Class: Bronze Record Creation
# =============================================================================

class TestBronzeRecordCreation:
    """Test bronze record creation từ OSM data."""
    
    def test_create_bronze_record_valid_data(self, ingestion_engine):
        """Test creating bronze record với valid OSM data."""
        # Sample OSM element
        osm_element = {
            "type": "node",
            "id": 12345,
            "lat": 35.6762,
            "lon": 139.6503,
            "tags": {
                "name": "Test Hotel",
                "tourism": "hotel"
            }
        }
        
        # Tạo bronze record
        record = ingestion_engine._create_bronze_record(
            element=osm_element,
            city_id="tokyo",
            category="hotel",
            source="osm"
        )
        
        # Assert record được tạo
        assert record is not None
        
        # Assert các trường bắt buộc
        assert record["source_id"] == "osm:node:12345"
        assert record["city"] == "tokyo"
        assert record["category"] == "hotel"
        assert record["raw_data"] == osm_element
        assert "ingestion_timestamp" in record
        assert "data_version" in record
    
    def test_create_bronze_record_missing_coordinates(self, ingestion_engine):
        """Test creating bronze record với missing coordinates."""
        # OSM element without coordinates
        osm_element = {
            "type": "node",
            "id": 12345,
            "tags": {
                "name": "Test Hotel"
            }
        }
        
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            ingestion_engine._create_bronze_record(
                element=osm_element,
                city_id="tokyo",
                category="hotel",
                source="osm"
            )
        
        # Assert error message
        assert "Missing coordinates" in str(exc_info.value)


# =============================================================================
# Test Class: Data Validation
# =============================================================================

class TestDataValidation:
    """Test data validation trong ingestion pipeline."""
    
    def test_validate_osm_element_valid(self, ingestion_engine):
        """Test validating valid OSM element."""
        # Valid OSM element
        element = {
            "type": "node",
            "id": 12345,
            "lat": 35.6762,
            "lon": 139.6503,
            "tags": {"name": "Test"}
        }
        
        # Should not raise exception
        result = ingestion_engine._validate_osm_element(element)
        assert result is True
    
    def test_validate_osm_element_invalid_type(self, ingestion_engine):
        """Test validating OSM element với invalid type."""
        # Element with invalid type
        element = {
            "type": "relation",  # Relation không được hỗ trợ
            "id": 12345,
            "lat": 35.6762,
            "lon": 139.6503
        }
        
        # Should return False
        result = ingestion_engine._validate_osm_element(element)
        assert result is False
    
    def test_validate_osm_element_missing_id(self, ingestion_engine):
        """Test validating OSM element thiếu ID."""
        # Element without ID
        element = {
            "type": "node",
            "lat": 35.6762,
            "lon": 139.6503
        }
        
        # Should return False
        result = ingestion_engine._validate_osm_element(element)
        assert result is False


# =============================================================================
# Test Class: Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling trong ingestion pipeline."""
    
    @pytest.mark.asyncio
    async def test_fetch_data_network_error(self, ingestion_engine):
        """Test handling network errors khi fetch data."""
        # Mock HTTP client để raise exception
        with patch.object(
            ingestion_engine,
            '_fetch_overpass_data',
            side_effect=Exception("Network error")
        ):
            # Should raise exception
            with pytest.raises(Exception) as exc_info:
                await ingestion_engine._fetch_overpass_data(
                    city_id="tokyo",
                    poi_type="hotel"
                )
            
            # Assert error message
            assert "Network error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, ingestion_engine):
        """Test retry mechanism cho failed requests."""
        # Mock với 2 failures rồi success
        call_count = 0
        
        async def mock_fetch(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")
            return {"elements": []}
        
        # Patch fetch method
        with patch.object(
            ingestion_engine,
            '_fetch_overpass_data',
            side_effect=mock_fetch
        ):
            # Call method
            result = await ingestion_engine._fetch_overpass_data(
                city_id="tokyo",
                poi_type="hotel"
            )
            
            # Assert retry happened
            assert call_count == 3
            assert result is not None


# =============================================================================
# Test Class: Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests cho complete ingestion flow."""
    
    @pytest.mark.asyncio
    async def test_full_ingestion_flow(self, ingestion_engine, sample_osm_response):
        """Test complete ingestion flow từ fetch đến storage."""
        # Mock fetch để return sample data
        with patch.object(
            ingestion_engine,
            '_fetch_overpass_data',
            return_value=sample_osm_response
        ):
            # Mock storage save
            with patch.object(
                ingestion_engine,
                '_save_bronze_records',
                return_value=True
            ) as mock_save:
                # Run ingestion
                result = await ingestion_engine.run_ingestion(
                    city_id="tokyo",
                    category="hotel"
                )
                
                # Assert success
                assert result["status"] == "success"
                assert result["records_processed"] == 1
                
                # Assert save được gọi
                mock_save.assert_called_once()


# =============================================================================
# Test Utilities
# =============================================================================

class TestUtilities:
    """Test utility functions."""
    
    def test_make_ukey_consistency(self):
        """Test rằng make_ukey tạo consistent keys."""
        # Tạo key với cùng inputs
        key1 = make_ukey("tokyo", "hotel", "Test Hotel", 35.6762, 139.6503)
        key2 = make_ukey("tokyo", "hotel", "Test Hotel", 35.6762, 139.6503)
        
        # Assert keys giống nhau
        assert key1 == key2
        
        # Tạo key với inputs khác
        key3 = make_ukey("bangkok", "hotel", "Test Hotel", 13.7563, 100.5018)
        
        # Assert keys khác nhau
        assert key1 != key3
    
    def test_setup_logging(self):
        """Test setup logging configuration."""
        # Setup logging
        logger = setup_logging()
        
        # Assert logger được tạo
        assert logger is not None
        
        # Assert logger có handlers
        assert len(logger.handlers) > 0
