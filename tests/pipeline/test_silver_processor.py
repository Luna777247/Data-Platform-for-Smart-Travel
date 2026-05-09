"""
Test Silver Processor
=====================
Unit tests cho Silver layer processing

Test Coverage:
- SilverProcessor initialization
- Deduplication logic
- Data merging và conflict resolution
- Business metrics calculation
- Silver record creation
"""

# Import pytest cho testing framework
import pytest

# Import typing cho type hints
from typing import Dict, Any, List, Optional

# Import datetime cho timestamp handling
from datetime import datetime

# Import unittest.mock cho mocking
from unittest.mock import Mock, patch

# Import processor cần test
from pipelines.silver.silver_processor import SilverProcessor

# Import utilities
from pipelines.shared.utils import setup_logging, make_ukey


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
# Fixture cung cấp logger instance
def logger():
    """Provide configured logger for tests."""
    return setup_logging()


@pytest.fixture
# Fixture cung cấp sample cleaned data từ bronze layer
def sample_cleaned_data():
    """Provide sample cleaned data for testing."""
    return [
        {
            "_id": "cleaned_001",
            "source_id": "osm:node:12345",
            "city": "tokyo",
            "cleaned_data": {
                "name": "Hotel Tokyo",
                "category": "hotel",
                "city": "tokyo",
                "coordinates": {"lat": 35.6762, "lon": 139.6503},
                "address": {"street": "Ginza", "city": "Tokyo"},
                "quality_score": 0.85
            },
            "processing_timestamp": "2026-01-01T01:00:00Z"
        },
        {
            "_id": "cleaned_002",
            "source_id": "google:ChIJ...",
            "city": "tokyo",
            "cleaned_data": {
                "name": "Tokyo Hotel Deluxe",
                "category": "hotel",
                "city": "tokyo",
                "coordinates": {"lat": 35.6763, "lon": 139.6504},  # Gần với record 001
                "address": {"street": "Ginza 1-chome", "city": "Tokyo"},
                "phone": "+81-3-1234-5678",
                "rating": 4.5,
                "quality_score": 0.90
            },
            "processing_timestamp": "2026-01-01T01:00:00Z"
        },
        {
            "_id": "cleaned_003",
            "source_id": "osm:node:67890",
            "city": "bangkok",
            "cleaned_data": {
                "name": "Bangkok Restaurant",
                "category": "restaurant",
                "city": "bangkok",
                "coordinates": {"lat": 13.7563, "lon": 100.5018},
                "cuisine": "thai",
                "quality_score": 0.75
            },
            "processing_timestamp": "2026-01-01T01:00:00Z"
        }
    ]


@pytest.fixture
# Fixture cung cấp sample duplicate data
def duplicate_data():
    """Provide sample duplicate data for deduplication testing."""
    return [
        {
            "_id": "dup_001",
            "source_id": "osm:node:111",
            "city": "tokyo",
            "cleaned_data": {
                "name": "Same Hotel",
                "category": "hotel",
                "coordinates": {"lat": 35.6762, "lon": 139.6503},
                "quality_score": 0.80
            }
        },
        {
            "_id": "dup_002",
            "source_id": "google:ChIJ...",
            "city": "tokyo",
            "cleaned_data": {
                "name": "Same Hotel",  # Same name
                "category": "hotel",
                "coordinates": {"lat": 35.67625, "lon": 139.65035},  # Very close
                "quality_score": 0.85  # Higher quality
            }
        }
    ]


@pytest.fixture
# Fixture khởi tạo SilverProcessor instance
def silver_processor(logger):
    """Create SilverProcessor instance for testing."""
    processor = SilverProcessor(
        city_id="tokyo",
        silver_dir="storage/silver"
    )
    return processor


# =============================================================================
# Test Class: Processor Initialization
# =============================================================================

class TestSilverProcessorInit:
    """Test SilverProcessor initialization."""
    
    def test_processor_initialization(self, logger):
        """Test processor được khởi tạo đúng cách."""
        # Khởi tạo processor
        processor = SilverProcessor(
            city_id="tokyo",
            silver_dir="storage/silver"
        )
        
        # Assert processor được tạo thành công
        assert processor is not None
        
        # Assert các thuộc tính được set đúng
        assert processor.city_id == "tokyo"
        assert processor.silver_dir == "storage/silver"
        assert processor.logger is not None
        
        # Assert deduplication parameters
        assert hasattr(processor, 'duplicate_distance_threshold')
        assert processor.duplicate_distance_threshold > 0
    
    def test_processor_with_defaults(self, logger):
        """Test processor với default values."""
        # Khởi tạo với minimal params
        processor = SilverProcessor(city_id="bangkok")
        
        # Assert default values
        assert processor.silver_dir == "storage/silver"
        assert processor.city_id == "bangkok"


# =============================================================================
# Test Class: Data Loading
# =============================================================================

class TestDataLoading:
    """Test data loading from bronze layer."""
    
    @pytest.mark.asyncio
    async def test_load_cleaned_data_success(self, silver_processor, sample_cleaned_data):
        """Test loading cleaned data successfully."""
        # Mock data loading
        with patch.object(
            silver_processor,
            '_load_cleaned_data',
            return_value=sample_cleaned_data
        ):
            # Load data
            result = await silver_processor._load_cleaned_data()
            
            # Assert success
            assert result is not None
            assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_load_cleaned_data_empty(self, silver_processor):
        """Test loading when no data available."""
        # Mock empty data
        with patch.object(
            silver_processor,
            '_load_cleaned_data',
            return_value=[]
        ):
            # Load data
            result = await silver_processor._load_cleaned_data()
            
            # Assert empty list
            assert result == []


# =============================================================================
# Test Class: Deduplication
# =============================================================================

class TestDeduplication:
    """Test deduplication logic."""
    
    def test_find_duplicates_with_duplicates(self, silver_processor, duplicate_data):
        """Test finding duplicates khi có duplicate data."""
        # Find duplicates
        duplicates = silver_processor._find_duplicates(duplicate_data)
        
        # Assert duplicates found
        assert len(duplicates) > 0
        
        # Assert duplicate group chứa cả 2 records
        for group in duplicates:
            assert len(group) >= 2
    
    def test_find_duplicates_no_duplicates(self, silver_processor, sample_cleaned_data):
        """Test finding duplicates khi không có duplicates."""
        # Tách data để tránh duplicates
        separated_data = [sample_cleaned_data[0], sample_cleaned_data[2]]
        
        # Find duplicates
        duplicates = silver_processor._find_duplicates(separated_data)
        
        # Assert no duplicates found
        assert len(duplicates) == 0
    
    def test_calculate_distance_same_location(self, silver_processor):
        """Test distance calculation cho same location."""
        # Same coordinates
        coord1 = {"lat": 35.6762, "lon": 139.6503}
        coord2 = {"lat": 35.6762, "lon": 139.6503}
        
        # Calculate distance
        distance = silver_processor._calculate_distance(coord1, coord2)
        
        # Assert distance is 0
        assert distance == 0.0
    
    def test_calculate_distance_nearby(self, silver_processor):
        """Test distance calculation cho nearby locations."""
        # Nearby coordinates (~10 meters apart)
        coord1 = {"lat": 35.6762, "lon": 139.6503}
        coord2 = {"lat": 35.6763, "lon": 139.6503}
        
        # Calculate distance
        distance = silver_processor._calculate_distance(coord1, coord2)
        
        # Assert small distance (< 100 meters)
        assert distance > 0
        assert distance < 100
    
    def test_calculate_distance_far(self, silver_processor):
        """Test distance calculation cho far locations."""
        # Far coordinates (Tokyo vs Bangkok)
        coord1 = {"lat": 35.6762, "lon": 139.6503}  # Tokyo
        coord2 = {"lat": 13.7563, "lon": 100.5018}  # Bangkok
        
        # Calculate distance
        distance = silver_processor._calculate_distance(coord1, coord2)
        
        # Assert large distance (> 4000 km)
        assert distance > 4000000  # meters


# =============================================================================
# Test Class: Data Merging
# =============================================================================

class TestDataMerging:
    """Test data merging và conflict resolution."""
    
    def test_merge_duplicate_records(self, silver_processor, duplicate_data):
        """Test merging duplicate records."""
        # Merge duplicates
        merged = silver_processor._merge_duplicate_records(duplicate_data)
        
        # Assert single merged record
        assert merged is not None
        
        # Assert merged record có data từ cả 2 sources
        assert "name" in merged
        assert "coordinates" in merged
        
        # Assert higher quality score được giữ lại
        assert merged.get("quality_score", 0) >= 0.85
    
    def test_resolve_field_conflict_higher_quality(self, silver_processor):
        """Test conflict resolution chọn higher quality data."""
        # Two values với different quality
        value1 = {"data": "Basic Name", "quality": 0.7}
        value2 = {"data": "Better Name", "quality": 0.9}
        
        # Resolve conflict
        result = silver_processor._resolve_field_conflict(value1, value2)
        
        # Assert higher quality value được chọn
        assert result == "Better Name"
    
    def test_resolve_field_conflict_longer_text(self, silver_processor):
        """Test conflict resolution chọn longer text khi quality equal."""
        # Two values với same quality
        value1 = {"data": "Hotel", "quality": 0.8}
        value2 = {"data": "Hotel Tokyo Deluxe", "quality": 0.8}
        
        # Resolve conflict
        result = silver_processor._resolve_field_conflict(value1, value2)
        
        # Assert longer text được chọn
        assert result == "Hotel Tokyo Deluxe"


# =============================================================================
# Test Class: Business Metrics
# =============================================================================

class TestBusinessMetrics:
    """Test business metrics calculation."""
    
    def test_calculate_popularity_score_with_rating(self, silver_processor):
        """Test popularity score calculation với rating data."""
        # Record với rating
        record = {
            "rating": 4.5,
            "review_count": 100
        }
        
        # Calculate score
        score = silver_processor._calculate_popularity_score(record)
        
        # Assert score trong valid range
        assert score >= 0.0
        assert score <= 1.0
        
        # Assert high rating cho high score
        assert score > 0.7  # 4.5/5 rating should be > 0.7
    
    def test_calculate_popularity_score_no_rating(self, silver_processor):
        """Test popularity score calculation without rating."""
        # Record không có rating
        record = {
            "name": "Some Hotel"
            # No rating
        }
        
        # Calculate score
        score = silver_processor._calculate_popularity_score(record)
        
        # Assert default/medium score
        assert score >= 0.0
        assert score <= 0.5  # Should be lower without rating
    
    def test_calculate_completeness_score_complete(self, silver_processor):
        """Test completeness score cho complete record."""
        # Complete record
        record = {
            "name": "Hotel",
            "category": "hotel",
            "coordinates": {"lat": 35.0, "lon": 139.0},
            "address": {"street": "Main St", "city": "Tokyo"},
            "phone": "123-456",
            "website": "https://example.com",
            "opening_hours": "24/7",
            "amenities": ["wifi", "parking"]
        }
        
        # Calculate score
        score = silver_processor._calculate_completeness_score(record)
        
        # Assert high score
        assert score >= 0.8
        assert score <= 1.0
    
    def test_calculate_completeness_score_incomplete(self, silver_processor):
        """Test completeness score cho incomplete record."""
        # Incomplete record
        record = {
            "name": "Hotel",
            "category": "hotel",
            "coordinates": {"lat": 35.0, "lon": 139.0}
            # Missing other fields
        }
        
        # Calculate score
        score = silver_processor._calculate_completeness_score(record)
        
        # Assert lower score
        assert score < 0.5
        assert score >= 0.0


# =============================================================================
# Test Class: Silver Record Creation
# =============================================================================

class TestSilverRecordCreation:
    """Test silver record creation."""
    
    def test_create_silver_record(self, silver_processor, sample_cleaned_data):
        """Test creating silver record từ cleaned data."""
        # Take first cleaned record
        cleaned_record = sample_cleaned_data[0]
        
        # Create silver record
        silver_record = silver_processor._create_silver_record(
            cleaned_record,
            merged_sources=[cleaned_record["source_id"]]
        )
        
        # Assert silver record structure
        assert silver_record is not None
        assert "poi_id" in silver_record
        assert "name" in silver_record
        assert "coordinates" in silver_record
        assert "metadata" in silver_record
        assert silver_record["metadata"]["version"] == "silver_v1"
    
    def test_create_silver_record_with_metrics(self, silver_processor, sample_cleaned_data):
        """Test silver record includes business metrics."""
        # Take record với rating
        cleaned_record = sample_cleaned_data[1]  # Has rating
        
        # Create silver record
        silver_record = silver_processor._create_silver_record(
            cleaned_record,
            merged_sources=[cleaned_record["source_id"]]
        )
        
        # Assert business metrics
        assert "business_metrics" in silver_record
        assert "popularity_score" in silver_record["business_metrics"]
        assert "completeness_score" in silver_record["business_metrics"]


# =============================================================================
# Test Class: Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests cho complete silver processing flow."""
    
    @pytest.mark.asyncio
    async def test_full_silver_processing(self, silver_processor, sample_cleaned_data):
        """Test complete silver processing flow."""
        # Mock data loading
        with patch.object(
            silver_processor,
            '_load_cleaned_data',
            return_value=sample_cleaned_data
        ):
            # Mock saving
            with patch.object(
                silver_processor,
                '_save_silver_records',
                return_value=True
            ) as mock_save:
                # Run processing
                result = await silver_processor.process()
                
                # Assert success
                assert result["status"] == "success"
                assert result["records_processed"] == 3
                
                # Assert save được gọi
                mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_silver_processing_with_deduplication(
        self,
        silver_processor,
        duplicate_data
    ):
        """Test silver processing với deduplication."""
        # Mock data loading với duplicates
        with patch.object(
            silver_processor,
            '_load_cleaned_data',
            return_value=duplicate_data
        ):
            # Mock saving
            with patch.object(
                silver_processor,
                '_save_silver_records',
                return_value=True
            ) as mock_save:
                # Run processing
                result = await silver_processor.process()
                
                # Assert success
                assert result["status"] == "success"
                
                # Assert duplicates được merged (2 input -> 1 output)
                assert result["records_deduplicated"] == 1
                assert result["records_processed"] == 1
