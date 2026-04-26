import hashlib
import unicodedata
import re
import math

def make_ukey(name: str, lat: float, lon: float) -> str:
    """
    Tạo u_key chuẩn hóa:
    - Làm tròn tọa độ về 4 chữ số thập phân (~11m).
    - Chuẩn hóa tên: Lower, Xóa dấu Tiếng Việt, Xóa khoảng trắng.
    - SHA1 hash (lấy 16 ký tự đầu).
    """
    if not name:
        name = "unnamed"
    
    # 1. Chuẩn hóa tên & XÓA DẤU (Để khớp "Hồ Gươm" với "Ho Guom")
    name_norm = unicodedata.normalize('NFKD', name.lower())
    name_norm = "".join([c for c in name_norm if not unicodedata.combining(c)])
    name_norm = re.sub(r'\s+', '_', name_norm.strip())
    
    # 2. Làm tròn tọa độ
    lat_r = round(float(lat), 4)
    lon_r = round(float(lon), 4)
    
    # 3. Hash SHA1
    raw = f"{name_norm}|{lat_r}|{lon_r}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]

def haversine_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách mét giữa 2 điểm (Haversine formula)."""
    R = 6371000  # Bán kính Trái đất tính bằng mét
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def find_existing_fuzzy(lat, lon, name, existing_data, radius_m=30):
    """
    Tìm địa điểm gần đúng trong bộ dữ liệu hiện tại (Dùng cho Offline JSON).
    """
    if not existing_data: return None
    
    # 1. Thử tìm chính xác bằng u_key mới trước
    new_key = make_ukey(name, lat, lon)
    if new_key in existing_data:
        return new_key
    
    # 2. Nếu không thấy, duyệt tìm trong bán kính radius_m
    name_norm = unicodedata.normalize('NFD', name.lower()).strip()
    
    for u_key, poi in existing_data.items():
        if "location" not in poi: continue
        p_lat = poi["location"]["lat"]
        p_lon = poi["location"]["lon"]
        dist = haversine_distance(lat, lon, p_lat, p_lon)
        
        if dist <= radius_m:
            # Kiểm tra độ tương đồng tên (Fuzzy basic)
            p_name_norm = unicodedata.normalize('NFD', poi["name"].lower()).strip()
            if name_norm in p_name_norm or p_name_norm in name_norm:
                return u_key
                
    return None

def calculate_content_hash(data: dict) -> str:
    """Tạo hash toàn bộ nội dung (đã có)."""
    content = str(sorted(data.items())).encode()
    return hashlib.sha256(content).hexdigest()

def compute_poi_hash(poi: dict) -> str:
    """
    Tạo hash đặc thù cho các trường hay biến động (rating, reviews, status).
    Dùng để phát hiện xem có cần cập nhật bản ghi hay không.
    """
    # Tập trung vào các trường quan trọng theo đề xuất của User
    fields = [
        poi.get('rating', 0),
        poi.get('reviews', 0),
        poi.get('status', 'operational'),
        poi.get('price_level', 0)
    ]
    return hashlib.md5(str(fields).encode()).hexdigest()
