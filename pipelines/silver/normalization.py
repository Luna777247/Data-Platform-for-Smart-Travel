"""
Normalization Module
===================

Data normalization cho Silver layer.
Theo RECOMMENDED_STRUCTURE.md - pipelines/silver/normalization.py
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, time

from src.utils.validation_utils import validate_phone, validate_email, validate_url

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Normalize POI data cho Silver layer.
    
    Normalizations:
    1. Text normalization (names, descriptions)
    2. Phone number normalization
    3. Address normalization
    4. Category normalization
    5. Opening hours normalization
    6. Coordinate normalization
    """
    
    def __init__(self):
        self.category_mappings = self._load_category_mappings()
        logger.info("DataNormalizer initialized")
    
    def _load_category_mappings(self) -> Dict[str, str]:
        """Load category normalization mappings."""
        return {
            # Restaurant variations
            "restaurant": "restaurant",
            "restaurants": "restaurant",
            "dining": "restaurant",
            "food": "restaurant",
            "eatery": "restaurant",
            
            # Hotel variations
            "hotel": "hotel",
            "hotels": "hotel",
            "lodging": "hotel",
            "accommodation": "hotel",
            "motel": "hotel",
            
            # Attraction variations
            "tourist_attraction": "tourist_attraction",
            "attraction": "tourist_attraction",
            "sightseeing": "tourist_attraction",
            "landmark": "tourist_attraction",
            "monument": "tourist_attraction",
            
            # Cafe variations
            "cafe": "cafe",
            "coffee": "cafe",
            "coffee_shop": "cafe",
            "café": "cafe",
            
            # Shopping variations
            "shopping": "shopping_mall",
            "shop": "shopping_mall",
            "store": "shopping_mall",
            "mall": "shopping_mall",
            "shopping_mall": "shopping_mall",
            
            # Park variations
            "park": "park",
            "parks": "park",
            "garden": "park",
            "recreation": "park",
        }
    
    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize một POI record.
        
        Args:
            record: Raw POI record
            
        Returns:
            Normalized record
        """
        normalized = record.copy()
        
        # Normalize các fields
        normalized["name"] = self.normalize_name(record.get("name", ""))
        normalized["phone"] = self.normalize_phone(record.get("phone"))
        normalized["website"] = self.normalize_website(record.get("website"))
        normalized["categories"] = self.normalize_categories(
            record.get("categories", [])
        )
        normalized["address"] = self.normalize_address(record.get("address", {}))
        normalized["opening_hours"] = self.normalize_opening_hours(
            record.get("opening_hours")
        )
        
        # Add normalization metadata
        normalized["normalized"] = True
        normalized["normalized_at"] = datetime.utcnow().isoformat()
        
        return normalized
    
    def normalize_records(
        self,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize nhiều records."""
        return [self.normalize_record(r) for r in records]
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize tên POI.
        
        - Trim whitespace
        - Title case
        - Remove extra spaces
        - Handle special characters
        """
        if not name:
            return ""
        
        # Basic cleanup
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)  # Remove extra spaces
        
        # Title case (preserve acronyms)
        words = name.split()
        normalized_words = []
        
        for word in words:
            # Keep acronyms uppercase (e.g., "IBM", "ABC")
            if word.isupper() and len(word) <= 4:
                normalized_words.append(word)
            else:
                normalized_words.append(word.capitalize())
        
        return ' '.join(normalized_words)
    
    def normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """
        Normalize phone number.
        
        - Remove non-numeric characters
        - Add country code if missing
        - Validate format
        """
        if not phone:
            return None
        
        # Remove all non-numeric characters
        digits = re.sub(r'\D', '', phone)
        
        if not digits:
            return None
        
        # Basic validation
        if len(digits) < 8 or len(digits) > 15:
            logger.warning(f"Invalid phone number length: {len(digits)}")
            return phone  # Return original if invalid
        
        # Format: +[country][number]
        if not digits.startswith('+'):
            # Assume Vietnam if starts with 0
            if digits.startswith('0'):
                digits = '84' + digits[1:]
            
            digits = '+' + digits
        
        return digits
    
    def normalize_website(self, website: Optional[str]) -> Optional[str]:
        """
        Normalize website URL.
        
        - Add https:// if missing
        - Remove trailing slash
        - Validate format
        """
        if not website:
            return None
        
        website = website.strip().lower()
        
        # Add protocol if missing
        if not website.startswith('http://') and not website.startswith('https://'):
            website = 'https://' + website
        
        # Remove trailing slash
        website = website.rstrip('/')
        
        # Basic validation
        if not validate_url(website):
            logger.warning(f"Invalid website URL: {website}")
            return website  # Return anyway
        
        return website
    
    def normalize_categories(
        self,
        categories: List[str] or str
    ) -> List[str]:
        """
        Normalize categories.
        
        - Map to canonical names
        - Remove duplicates
        - Sort alphabetically
        """
        if not categories:
            return []
        
        # Convert to list if string
        if isinstance(categories, str):
            categories = [categories]
        
        normalized = set()
        
        for cat in categories:
            if not cat:
                continue
            
            cat_lower = cat.lower().strip()
            
            # Map to canonical name
            canonical = self.category_mappings.get(cat_lower, cat_lower)
            normalized.add(canonical)
        
        return sorted(list(normalized))
    
    def normalize_address(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize address components.
        """
        if not address:
            return {}
        
        normalized = {}
        
        # Normalize each component
        if "street" in address:
            normalized["street"] = self._normalize_street(address["street"])
        
        if "city" in address:
            normalized["city"] = address["city"].strip().title()
        
        if "district" in address:
            normalized["district"] = address["district"].strip().title()
        
        if "country" in address:
            normalized["country"] = address["country"].strip().upper()
        
        if "postal_code" in address:
            normalized["postal_code"] = str(address["postal_code"]).strip()
        
        return normalized
    
    def _normalize_street(self, street: str) -> str:
        """Normalize street address."""
        if not street:
            return ""
        
        # Common abbreviations
        abbreviations = {
            r'\bSt\b': 'Street',
            r'\bSt\.': 'Street',
            r'\bRd\b': 'Road',
            r'\bRd\.': 'Road',
            r'\bAve\b': 'Avenue',
            r'\bAve\.': 'Avenue',
            r'\bBlvd\b': 'Boulevard',
            r'\bBlvd\.': 'Boulevard',
        }
        
        street = street.strip()
        
        for abbr, full in abbreviations.items():
            street = re.sub(abbr, full, street, flags=re.IGNORECASE)
        
        return street.title()
    
    def normalize_opening_hours(
        self,
        opening_hours: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize opening hours.
        
        Input formats:
        - OSM format: "Mo-Fr 09:00-18:00; Sa 10:00-16:00"
        - Structured: {"monday": "09:00-18:00", ...}
        """
        if not opening_hours:
            return None
        
        # If already structured, validate
        if isinstance(opening_hours, dict):
            return self._validate_structured_hours(opening_hours)
        
        # If string, parse OSM format
        if isinstance(opening_hours, str):
            return self._parse_osm_hours(opening_hours)
        
        return None
    
    def _validate_structured_hours(
        self,
        hours: Dict[str, str]
    ) -> Dict[str, str]:
        """Validate and normalize structured hours."""
        days = ["monday", "tuesday", "wednesday", "thursday", 
                "friday", "saturday", "sunday"]
        
        validated = {}
        
        for day in days:
            if day in hours:
                time_range = hours[day]
                
                # Validate format
                if self._is_valid_time_range(time_range):
                    validated[day] = time_range
                elif time_range.lower() in ["closed", "24/7", "open"]:
                    validated[day] = time_range
        
        return validated
    
    def _parse_osm_hours(self, hours_str: str) -> Dict[str, str]:
        """Parse OSM opening hours format."""
        # Simplified parser cho common patterns
        result = {}
        
        # Map day abbreviations
        day_map = {
            'mo': 'monday', 'tu': 'tuesday', 'we': 'wednesday',
            'th': 'thursday', 'fr': 'friday', 'sa': 'saturday', 'su': 'sunday'
        }
        
        # Split by semicolon
        parts = hours_str.split(';')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Try to parse
            if '-' in part:
                day_part, time_part = part.split(' ', 1)
                
                # Handle day ranges
                if '-' in day_part:
                    start_day, end_day = day_part.split('-')
                    start_day = day_map.get(start_day.lower(), start_day.lower())
                    end_day = day_map.get(end_day.lower(), end_day.lower())
                    
                    # Add to all days in range
                    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 
                                 'friday', 'saturday', 'sunday']
                    
                    if start_day in days_order and end_day in days_order:
                        start_idx = days_order.index(start_day)
                        end_idx = days_order.index(end_day)
                        
                        for i in range(start_idx, end_idx + 1):
                            result[days_order[i]] = time_part
                else:
                    day = day_map.get(day_part.lower(), day_part.lower())
                    result[day] = time_part
        
        return result
    
    def _is_valid_time_range(self, time_range: str) -> bool:
        """Validate time range format."""
        # Pattern: HH:MM-HH:MM hoặc HH:MM - HH:MM
        pattern = r'^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}$'
        return bool(re.match(pattern, time_range))
