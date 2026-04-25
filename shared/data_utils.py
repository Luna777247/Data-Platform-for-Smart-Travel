import hashlib

def generate_unique_key(name: str, lat: float, lon: float) -> str:
    """
    Generate a unique, deterministic key for a place based on name and coordinates.
    Round coordinates to 4 decimal places (~11m precision) to handle slight GPS noise.
    """
    if not name:
        name = "unnamed"
    
    # Normalize name and round coordinates
    clean_name = name.lower().strip()
    round_lat = round(float(lat), 4)
    round_lon = round(float(lon), 4)
    
    key_base = f"{clean_name}_{round_lat}_{round_lon}"
    return hashlib.md5(key_base.encode()).hexdigest()

def normalize_city_name(city_name: str) -> str:
    return city_name.lower().strip().replace(" ", "")
