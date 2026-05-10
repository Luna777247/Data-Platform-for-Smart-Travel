"""
Utilities Package
==================

Shared utility functions cho Smart Tourism Data Platform.

Utilities:
- auth_utils: Authentication helpers
- date_utils: Date/time utilities
- geo_utils: Geospatial calculations
- validation_utils: Data validation
- monitoring_utils: Monitoring helpers
- notification_utils: Notification helpers
"""

from src.utils.date_utils import format_datetime, parse_datetime, now_utc, to_iso_format, from_iso_format
from src.utils.geo_utils import calculate_distance, validate_coordinates, get_bounding_box
from src.utils.validation_utils import validate_email, validate_url, validate_phone, validate_required, validate_length
from src.utils.auth_utils import generate_api_key, hash_token, mask_token, generate_nonce
from src.utils.monitoring_utils import timer, timed, calculate_percentile, format_bytes, format_duration
from src.utils.notification_utils import format_slack_message, format_email_alert, truncate_message, create_notification_id

__all__ = [
    # Date utils
    "format_datetime",
    "parse_datetime",
    "now_utc",
    "to_iso_format",
    "from_iso_format",
    # Geo utils
    "calculate_distance",
    "validate_coordinates",
    "get_bounding_box",
    # Validation utils
    "validate_email",
    "validate_url",
    "validate_phone",
    "validate_required",
    "validate_length",
    # Auth utils
    "generate_api_key",
    "hash_token",
    "mask_token",
    "generate_nonce",
    # Monitoring utils
    "timer",
    "timed",
    "calculate_percentile",
    "format_bytes",
    "format_duration",
    # Notification utils
    "format_slack_message",
    "format_email_alert",
    "truncate_message",
    "create_notification_id",
]