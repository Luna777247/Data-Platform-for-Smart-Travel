"""
Shared Utilities Module - Common Functions cho Data Pipeline
==========================================================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - pipelines/shared/ section

Mục đích:
- Cung cấp các utility functions dùng chung cho toàn bộ pipeline
- Xử lý common tasks: logging, file I/O, data transformation
- Standardize naming conventions và data formats
- Helper functions cho validation và normalization

Function Categories:
1. Logging: setup_logging() - Cấu hình structured logging
2. Data Processing: make_ukey(), normalize_coordinates(), extract_name_from_tags()
3. Category Mapping: normalize_category() - OSM tags → canonical categories
4. File I/O: load_json_file(), save_json_file() - JSON persistence
5. String Processing: clean_address(), generate_search_keywords()
6. Quality Scoring: calculate_quality_score() - Data quality assessment

Usage:
    >>> from pipelines.shared.utils import setup_logging, make_ukey
    >>> logger = setup_logging(__name__)
    >>> ukey = make_ukey("node123", "tokyo", "restaurant")
    >>> print(ukey)  # a1b2c3d4e5f6g7h8
"""

# Import logging module để cấu hình loggers
import logging

# Import hashlib để tạo MD5 hashes cho unique keys
import hashlib

# Import json cho serialization/deserialization
import json

# Import os cho filesystem operations
import os

# Import datetime classes cho timestamps
from datetime import datetime, timezone

# Import Path cho cross-platform file paths
from pathlib import Path

# Import type hints cho type checking và documentation
from typing import Any, Dict, List, Optional, Union

# Import re cho regular expressions (string cleaning, validation)
import re

# Import POICategory enum từ schemas cho category mapping
from pipelines.shared.schemas import POICategory


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup logging với format chuẩn"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger


def make_ukey(source_id: str, city: str, category: str = "") -> str:
    """Tạo unique key từ source_id, city, và category"""
    if not source_id:
        source_id = "unknown"
    
    # Clean và normalize
    source_id = str(source_id).strip().lower()
    city = city.strip().lower()
    category = category.strip().lower()
    
    # Create hash để đảm bảo uniqueness
    combined = f"{source_id}_{city}_{category}"
    return hashlib.md5(combined.encode()).hexdigest()[:16]


def normalize_coordinates(lat: Any, lon: Any) -> Optional[Dict[str, float]]:
    """Normalize và validate coordinates"""
    try:
        lat_float = float(lat)
        lon_float = float(lon)
        
        # Validate range
        if not (-90 <= lat_float <= 90) or not (-180 <= lon_float <= 180):
            return None
        
        return {"lat": lat_float, "lon": lon_float}
    except (ValueError, TypeError):
        return None


def extract_name_from_tags(tags: Dict[str, Any], preferred_langs: List[str] = None) -> str:
    """Extract tên từ OSM tags theo priority language"""
    if preferred_langs is None:
        preferred_langs = ["vi", "en", "name"]
    
    # Priority order for name extraction
    name_fields = []
    for lang in preferred_langs:
        name_fields.extend([f"name:{lang}", f"name:{lang.upper()}"])
    name_fields.append("name")
    
    for field in name_fields:
        if field in tags and tags[field]:
            name = str(tags[field]).strip()
            if name:
                return name
    
    return "Unnamed"


def normalize_category(tags: Dict[str, Any]) -> Optional[POICategory]:
    """Map OSM tags sang standardized category"""
    # Tourism category mapping
    tourism_mapping = {
        "attraction": POICategory.TOURIST_ATTRACTION,
        "hotel": POICategory.HOTEL,
        "museum": POICategory.MUSEUM,
        "artwork": POICategory.TOURIST_ATTRACTION,
        "viewpoint": POICategory.TOURIST_ATTRACTION,
        "picnic_site": POICategory.PARK,
        "camp_site": POICategory.PARK,
        "theme_park": POICategory.TOURIST_ATTRACTION,
        "zoo": POICategory.TOURIST_ATTRACTION,
        "aquarium": POICategory.TOURIST_ATTRACTION
    }
    
    # Shop category mapping
    shop_mapping = {
        "mall": POICategory.SHOPPING_MALL,
        "supermarket": POICategory.SHOPPING_MALL,
        "department_store": POICategory.SHOPPING_MALL
    }
    
    # Food category mapping
    food_mapping = {
        "restaurant": POICategory.RESTAURANT,
        "fast_food": POICategory.RESTAURANT,
        "cafe": POICategory.CAFE,
        "bar": POICategory.CAFE,
        "pub": POICategory.CAFE
    }
    
    # Entertainment category mapping
    entertainment_mapping = {
        "cinema": POICategory.CINEMA,
        "theatre": POICategory.CINEMA,
        "concert_hall": POICategory.CINEMA
    }
    
    # Check in order of priority
    for tag_key, category in {
        **tourism_mapping,
        **shop_mapping,
        **food_mapping,
        **entertainment_mapping
    }.items():
        if tags.get(tag_key):
            return category
    
    # Check amenity
    amenity = tags.get("amenity", "")
    if amenity in ["restaurant", "cafe", "bar", "pub"]:
        if amenity == "cafe":
            return POICategory.CAFE
        else:
            return POICategory.RESTAURANT
    
    # Check leisure
    leisure = tags.get("leisure", "")
    if leisure in ["park", "garden", "playground"]:
        return POICategory.PARK
    
    return None


def clean_address(tags: Dict[str, Any]) -> str:
    """Extract và clean address từ OSM tags"""
    address_parts = []
    
    # Priority order for address components
    address_fields = [
        "addr:housenumber",
        "addr:street",
        "addr:city",
        "addr:suburb",
        "addr:district",
        "addr:province",
        "addr:postcode"
    ]
    
    for field in address_fields:
        if field in tags and tags[field]:
            address_parts.append(str(tags[field]).strip())
    
    # Try full address field
    if "addr" in tags and tags["addr"]:
        address_parts.insert(0, str(tags["addr"]).strip())
    
    return ", ".join(address_parts)


def generate_search_keywords(name: str, tags: Dict[str, Any], category: POICategory) -> List[str]:
    """Generate search keywords từ name và tags"""
    keywords = set()
    
    # Add name variations
    if name:
        # Original name
        keywords.add(name.lower())
        # Name without special characters
        clean_name = re.sub(r'[^\w\s]', '', name.lower())
        keywords.add(clean_name)
        # Words from name
        words = [word.strip() for word in clean_name.split() if len(word.strip()) > 2]
        keywords.update(words)
    
    # Add category keywords
    category_keywords = {
        POICategory.TOURIST_ATTRACTION: ["điểm du lịch", "thắng cảnh", "di tích", "attraction", "tourist"],
        POICategory.RESTAURANT: ["nhà hàng", "quán ăn", "restaurant", "food", "ẩm thực"],
        POICategory.HOTEL: ["khách sạn", "hotel", "lưu trú", "accommodation"],
        POICategory.CAFE: ["quán cà phê", "cafe", "coffee", "cà phê"],
        POICategory.SHOPPING_MALL: ["trung tâm thương mại", "mall", "shopping", "mua sắm"],
        POICategory.PARK: ["công viên", "park", "sân chơi", "giải trí"],
        POICategory.CINEMA: ["rạp chiếu phim", "cinema", "movie", "phim"],
        POICategory.MUSEUM: ["bảo tàng", "museum", "lịch sử", "văn hóa"]
    }
    
    if category in category_keywords:
        keywords.update(category_keywords[category])
    
    # Add tags as keywords
    for key, value in tags.items():
        if key.startswith("name:") or key in ["cuisine", "shop", "amenity", "tourism"]:
            if isinstance(value, str) and len(value.strip()) > 1:
                keywords.add(value.lower().strip())
    
    return list(keywords)


def calculate_quality_score(
    name: str,
    address: str,
    coordinates: Dict[str, float],
    tags: Dict[str, Any],
    category: POICategory
) -> float:
    """Calculate quality score (0-1) cho POI"""
    score = 0.0
    max_score = 1.0
    
    # Name quality (30%)
    if name and name != "Unnamed" and len(name.strip()) >= 3:
        score += 0.3
    
    # Address quality (20%)
    if address and len(address.strip()) >= 5:
        score += 0.2
    
    # Coordinates quality (20%)
    if coordinates and "lat" in coordinates and "lon" in coordinates:
        score += 0.2
    
    # Tags completeness (20%)
    important_tags = ["name", "amenity", "shop", "tourism", "cuisine"]
    tag_count = sum(1 for tag in important_tags if tag in tags)
    score += (tag_count / len(important_tags)) * 0.2
    
    # Category confidence (10%)
    if category:
        score += 0.1
    
    return min(score, max_score)


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists"""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def load_json_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Load JSON file với error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error loading {file_path}: {e}")
        return None


def save_json_file(data: Any, file_path: Union[str, Path], indent: int = 2) -> bool:
    """Save data to JSON file với error handling"""
    try:
        ensure_directory(file_path.parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, default=str)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Error saving {file_path}: {e}")
        return False


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in MB"""
    try:
        return Path(file_path).stat().st_size / (1024 * 1024)
    except:
        return 0.0


def format_duration(seconds: float) -> str:
    """Format duration thành human readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m{secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h{minutes}m"
