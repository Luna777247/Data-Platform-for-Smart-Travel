"""
Plugin Base Classes
===================
Abstract base classes cho plugin system.

Định nghĩa interface mà tất cả plugins phải implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BasePlugin(ABC):
    """Base class cho tất cả plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._initialized_at = datetime.now()
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Unique identifier cho plugin"""
        pass
    
    @property
    @abstractmethod
    def plugin_version(self) -> str:
        """Semantic version (e.g., '1.0.0')"""
        pass
    
    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """'source' | 'transformer' | 'enricher'"""
        pass
    
    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration trước khi sử dụng.
        
        Args:
            config: Plugin configuration dict
            
        Returns:
            True nếu config hợp lệ
            
        Raises:
            ValueError: Nếu config không hợp lệ
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Kiểm tra plugin health.
        
        Returns:
            {"status": "healthy", "message": "..."}
        """
        pass


class BaseCollector(BasePlugin):
    """
    Abstract base class cho data collectors.
    
    Tất cả source collectors (OSM, Google Places, TripAdvisor, etc.)
    phải inherit từ class này.
    
    Example:
        class TripAdvisorCollector(BaseCollector):
            @property
            def plugin_name(self) -> str:
                return "tripadvisor"
            
            async def collect(self, city, category, **kwargs):
                # Implementation
                return data
    """
    
    @property
    def plugin_type(self) -> str:
        return "source"
    
    @abstractmethod
    async def collect(
        self, 
        city: str, 
        category: str, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Thu thập dữ liệu từ nguồn.
        
        Args:
            city: Tên thành phố (e.g., "hanoi", "tokyo")
            category: Loại POI (e.g., "restaurant", "hotel")
            **kwargs: Additional parameters (lat, lng, radius, etc.)
            
        Returns:
            List of raw data dictionaries
            
        Example:
            [
                {
                    "place_id": "ChIJ...",
                    "name": "Place Name",
                    "location": {"lat": 21.0, "lng": 105.8},
                    ...
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    async def search_nearby(
        self,
        lat: float,
        lng: float,
        radius: int = 2000,
        place_type: Optional[str] = None,
        max_results: int = 60,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm POI gần một location.
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Bán kính tìm kiếm (meters)
            place_type: Loại địa điểm
            max_results: Số kết quả tối đa
            
        Returns:
            List of place dictionaries
        """
        pass
    
    async def enrich(self, poi_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Làm giàu dữ liệu POI (optional).
        
        Args:
            poi_data: POI data cần enrich
            
        Returns:
            Enriched POI data
        """
        # Default: return as-is
        return poi_data


class BaseTransformer(BasePlugin):
    """
    Abstract base class cho data transformers/enrichers.
    
    Transform data từ format này sang format khác,
    hoặc thêm thông tin bổ sung.
    """
    
    @property
    def plugin_type(self) -> str:
        return "transformer"
    
    @abstractmethod
    async def transform(
        self, 
        data: List[Dict[str, Any]], 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Transform danh sách data.
        
        Args:
            data: List of data dictionaries
            **kwargs: Transform options
            
        Returns:
            Transformed data list
        """
        pass


class BaseEnricher(BaseTransformer):
    """
    Base class cho data enrichers (là một loại transformer).
    
    Enrichers thêm thông tin vào data hiện có
    (rating, categories, geospatial data, etc.)
    """
    
    @property
    def plugin_type(self) -> str:
        return "enricher"
    
    @abstractmethod
    async def enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich một single record.
        
        Args:
            data: Single data record
            
        Returns:
            Enriched record
        """
        pass
    
    async def transform(
        self, 
        data: List[Dict[str, Any]], 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Transform by enriching all records.
        
        Args:
            data: List of records
            
        Returns:
            Enriched list
        """
        enriched = []
        for record in data:
            try:
                enriched_record = await self.enrich(record)
                enriched.append(enriched_record)
            except Exception as e:
                # Log error but continue
                enriched.append(record)  # Keep original
        return enriched


class PluginConfig:
    """
    Configuration schema cho plugin.
    
    Define expected config parameters và validation rules.
    """
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
    
    def validate(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate config against schema.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        for field, rules in self.schema.items():
            if rules.get("required", False) and field not in config:
                errors.append(f"Missing required field: {field}")
                continue
            
            if field in config:
                value = config[field]
                field_type = rules.get("type")
                
                if field_type == "string" and not isinstance(value, str):
                    errors.append(f"{field} must be string")
                elif field_type == "integer" and not isinstance(value, int):
                    errors.append(f"{field} must be integer")
                elif field_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"{field} must be boolean")
        
        return len(errors) == 0, errors


__all__ = [
    'BasePlugin',
    'BaseCollector',
    'BaseTransformer',
    'BaseEnricher',
    'PluginConfig'
]
