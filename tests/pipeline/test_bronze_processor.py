"""
Test Bronze Processor
=====================
Unit tests cho Bronze layer processing

Test Coverage:
- BronzeOSMProcessor initialization
- Data loading từ JSON files
- Data cleaning và normalization
- Quality scoring
- Error handling cho malformed data
"""

# Import pytest cho testing framework
import pytest

# Import typing cho type hints
from typing import Dict, Any, List, Optional

# Import datetime cho timestamp handling
from datetime import datetime

# Import unittest.mock cho mocking
from unittest.mock import Mock, patch, mock_open

# Import json cho JSON handling
import json

# Import processor cần test
from pipelines.bronze.osm_processor import BronzeOSMProcessor

# Import utilities
from pipelines.shared.utils import setup_logging, normalize_coordinates


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
# Fixture cung cấp logger instance
def logger():
    """Provide configured logger for tests."""
    return setup_logging()


@pytest.fixture
# Fixture cung cấp sample bronze data
def sample_bronze_data():
    """Provide sample bronze data for testing."""
    return [
        {
            "_id": "bronze_001",
            "source_id": "osm:node:12345",
            "source": "osm",
            "city": "tokyo",
            "category": "hotel",
            "raw_data": {
                "type": "node",
                "id": 12345,
                "lat": 35.6762,
                "lon": 139.6503,
                "tags": {
                    "name": "Hotel Tokyo",
                    "tourism": "hotel",
                    "addr:city": "Tokyo",
                    "addr:street": "Ginza"
                }
            },
            "ingestion_timestamp": "2026-01-01T00:00:00Z",
            "data_version": "1.0"
        },
        {
            "_id": "bronze_002",
            "source_id": "osm:node:12346",
            "source": "osm",
            "city": "tokyo",
            "category": "restaurant",
            "raw_data": {
                "type": "node",
                "id": 12346,
                "lat": 35.6586,
                "lon": 139.7454,
                "tags": {
                    "name": "Sushi Restaurant",
                    "amenity": "restaurant",
                    "cuisine": "sushi"
                }
            },
            "ingestion_timestamp": "2026-01-01T00:00:00Z",
            "data_version": "1.0"
        }
    ]


@pytest.fixture
# Fixture cung cấp sample malformed data
def malformed_bronze_data():
    """Provide malformed bronze data for error testing."""
    return [
        {
            "_id": "bronze_003",
            "source_id": "osm:node:99999",
            "source": "osm",
            "city": "tokyo",
            "category": "hotel",
            "raw_data": {
                "type": "node",
                "id": 99999,
                # Missing lat/lon
                "tags": {
                    "name": "Invalid Hotel"
                }
            },
            "ingestion_timestamp": "2026-01-01T00:00:00Z",
            "data_version": "1.0"
        }
    ]


@pytest.fixture
# Fixture khởi tạo BronzeOSMProcessor instance
def bronze_processor(logger):
    """Create BronzeOSMProcessor instance for testing."""
    processor = BronzeOSMProcessor(
        city_id="tokyo",
        category="hotel",
        bronze_dir="storage/bronze"
    )
    return processor


# =============================================================================
# Test Class: Processor Initialization
# =============================================================================

class TestBronzeProcessorInit:
    """Test BronzeOSMProcessor initialization."""
    
    def test_processor_initialization(self, logger):
        """Test processor được khởi tạo đúng cách."""
        # Khởi tạo processor
        processor = BronzeOSMProcessor(
            city_id="tokyo",
            category="hotel",
            bronze_dir="storage/bronze"
        )
        
        # Assert processor được tạo thành công
        assert processor is not None
        
        # Assert các thuộc tính được set đúng
        assert processor.city_id == "tokyo"
        assert processor.category == "hotel"
        assert processor.bronze_dir == "storage/bronze"
        assert processor.logger is not None
    
    def test_processor_with_defaults(self, logger):
        """Test processor với default values."""
        # Khởi tạo với minimal params
        processor = BronzeOSMProcessor(
            city_id="bangkok",
            category="restaurant"
        )
        
        # Assert default values
        assert processor.bronze_dir == "storage/bronze"
        assert processor.city_id == "bangkok"
        assert processor.category == "restaurant"


# =============================================================================
# Test Class: Data Loading
# =============================================================================

class TestDataLoading:
    """Test data loading từ JSON files."""
    
    @pytest.mark.asyncio
    async def test_load_bronze_data_success(self, bronze_processor, sample_bronze_data):
        """Test loading bronze data successfully."""
        # Mock file open để return sample data
        json_content = json.dumps(sample_bronze_data)
        
        with patch("builtins.open", mock_open(read_data=json_content)):
            # Load data
            result = await bronze_processor._load_bronze_data()
            
            # Assert success
            assert result is not None
            assert len(result) == 2
            assert result[0]["city"] == "tokyo"
    
    @pytest.mark.asyncio
    async def test_load_bronze_data_file_not_found(self, bronze_processor):
        """Test handling khi file không tồn tại."""
        # Patch os.path.exists để return False
        with patch("os.path.exists", return_value=False):
            # Load data
            result = await bronze_processor._load_bronze_data()
            
            # Assert empty list returned
            assert result == []
    
    @pytest.mark.asyncio
    async def test_load_bronze_data_invalid_json(self, bronze_processor):
        """Test handling khi JSON invalid."""
        # Invalid JSON content
        invalid_json = "{invalid json"
        
        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with patch("os.path.exists", return_value=True):
                # Should raise JSONDecodeError
                with pytest.raises(json.JSONDecodeError):
                    await bronze_processor._load_bronze_data()


# =============================================================================
# Test Class: Data Cleaning
# =============================================================================

class TestDataCleaning:
    """Test data cleaning operations."""
    
    def test_clean_record_valid_data(self, bronze_processor):
        """Test cleaning record với valid data."""
        # Sample raw record
        raw_record = {
            "raw_data": {
                "type": "node",
                "id": 12345,
                "lat": 35.6762,
                "lon": 139.6503,
                "tags": {
                    "name": "Hotel Tokyo",
                    "tourism": "hotel",
                    "addr:city": "Tokyo"
                }
            },
            "source_id": "osm:node:12345",
            "city": "tokyo",
            "category": "hotel"
        }
        
        # Clean record
        result = bronze_processor._clean_record(raw_record)
        
        # Assert cleaned data
        assert result["cleaned_data"]["name"] == "Hotel Tokyo"
        assert result["cleaned_data"]["category"] == "hotel"
        assert result["cleaned_data"]["city"] == "tokyo"
        assert "coordinates" in result["cleaned_data"]
    
    def test_clean_record_missing_name(self, bronze_processor):
        """Test cleaning record thiếu name."""
        # Record without name
        raw_record = {
            "raw_data": {
                "type": "node",
                "id": 12345,
                "lat": 35.6762,
                "lon": 139.6503,
                "tags": {
                    # Missing name
                    "tourism": "hotel"
                }
            },
            "source_id": "osm:node:12345",
            "city": "tokyo",
            "category": "hotel"
        }
        
        # Clean record
        result = bronze_processor._clean_record(raw_record)
        
        # Assert name được xử lý
        assert result["cleaned_data"]["name"] == "Unknown Hotel"
    
    def test_clean_record_missing_coordinates(self, bronze_processor):
        """Test cleaning record thiếu coordinates."""
        # Record without coordinates
        raw_record = {
            "raw_data": {
                "type": "node",
                "id": 12345,
                # Missing lat/lon
                "tags": {
                    "name": "Test Hotel",
                    "tourism": "hotel"
                }
            },
            "source_id": "osm:node:12345",
            "city": "tokyo",
            "category": "hotel"
        }
        
        # Should return None vì không có coordinates
        result = bronze_processor._clean_record(raw_record)
        
        # Assert record bị skip
        assert result is None


# =============================================================================
# Test Class: Data Normalization
# =============================================================================

class TestDataNormalization:
    """Test data normalization operations."""
    
    def test_normalize_coordinates_valid(self, bronze_processor):
        """Test normalizing valid coordinates."""
        # Valid coordinates
        lat, lon = 35.6762, 139.6503
        
        # Normalize
        result = bronze_processor._normalize_coordinates(lat, lon)
        
        # Assert normalized
        assert result is not None
        assert "lat" in result
        assert "lon" in result
        # Assert precision (6 decimal places)
        assert round(result["lat"], 6) == round(lat, 6)
        assert round(result["lon"], 6) == round(lon, 6)
    
    def test_normalize_coordinates_invalid(self, bronze_processor):
        """Test normalizing invalid coordinates."""
        # Invalid coordinates (out of range)
        lat, lon = 999.999, 999.999
        
        # Should return None
        result = bronze_processor._normalize_coordinates(lat, lon)
        
        # Assert None returned
        assert result is None
    
    def test_normalize_name(self, bronze_processor):
        """Test normalizing POI names."""
        # Test cases
        test_cases = [
            ("  Hotel Tokyo  ", "Hotel Tokyo"),  # Trim spaces
            ("HOTEL TOKYO", "Hotel Tokyo"),     # Title case
            ("hotel tokyo", "Hotel Tokyo"),       # Capitalize
            ("", None),                           # Empty -> None
        ]
        
        for input_name, expected in test_cases:
            result = bronze_processor._normalize_name(input_name)
            assert result == expected, f"Failed for input: {input_name}"


# =============================================================================
# Test Class: Quality Scoring
# =============================================================================

class TestQualityScoring:
    """Test data quality scoring."""
    
    def test_calculate_quality_score_high(self, bronze_processor):
        """Test quality score cho high quality data."""
        # High quality record (complete data)
        record = {
            "name": "Complete Hotel",
            "coordinates": {"lat": 35.6762, "lon": 139.6503},
            "address": {"city": "Tokyo", "street": "Ginza"},
            "phone": "+81-3-1234-5678",
            "website": "https://example.com",
            "opening_hours": "24/7"
        }
        
        # Calculate score
        score = bronze_processor._calculate_quality_score(record)
        
        # Assert high score (>= 0.8)
        assert score >= 0.8
        assert score <= 1.0
    
    def test_calculate_quality_score_low(self, bronze_processor):
        """Test quality score cho low quality data."""
        # Low quality record (minimal data)
        record = {
            "name": "Minimal Hotel",
            "coordinates": {"lat": 35.6762, "lon": 139.6503}
            # Missing other fields
        }
        
        # Calculate score
        score = bronze_processor._calculate_quality_score(record)
        
        # Assert lower score (< 0.5)
        assert score < 0.5
        assert score >= 0.0
    
    def test_calculate_quality_score_empty(self, bronze_processor):
        """Test quality score cho empty record."""
        # Empty record
        record = {}
        
        # Calculate score
        score = bronze_processor._calculate_quality_score(record)
        
        # Assert minimum score
        assert score == 0.0


# =============================================================================
# Test Class: Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests cho complete bronze processing flow."""
    
    @pytest.mark.asyncio
    async def test_full_processing_flow(self, bronze_processor, sample_bronze_data):
        """Test complete bronze processing flow."""
        # Mock data loading
        with patch.object(
            bronze_processor,
            '_load_bronze_data',
            return_value=sample_bronze_data
        ):
            # Mock file saving
            with patch.object(
                bronze_processor,
                '_save_processed_data',
                return_value=True
            ) as mock_save:
                # Run processing
                result = await bronze_processor.process()
                
                # Assert success
                assert result["status"] == "success"
                assert result["records_processed"] == 2
                assert result["records_failed"] == 0
                
                # Assert save được gọi
                mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_processing_with_malformed_data(
        self,
        bronze_processor,
        sample_bronze_data,
        malformed_bronze_data
    ):
        """Test processing với mix của valid và malformed data."""
        # Combine valid và malformed data
        mixed_data = sample_bronze_data + malformed_bronze_data
        
        # Mock data loading
        with patch.object(
            bronze_processor,
            '_load_bronze_data',
            return_value=mixed_data
        ):
            # Run processing
            result = await bronze_processor.process()
            
            # Assert partial success
            assert result["status"] == "success"
            assert result["records_processed"] == 2  # Valid records
            assert result["records_failed"] == 1     # Malformed record
