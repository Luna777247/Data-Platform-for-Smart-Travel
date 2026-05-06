import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

class SmartKeyManager:
    def __init__(self, keys: list[str], daily_limit=500):
        # Mặc định mỗi key Free của RapidAPI cho ~500 requests/day
        self.keys = {k: {'used': 0, 'errors': 0, 'blocked_until': None}
                     for k in keys}
        self.daily_limit = daily_limit
        self.global_cooldown_until = None
        logger.info(f"🔑 KeyManager initialized with {len(keys)} potential keys.")
    
    def get_best_key(self) -> str | None:
        """Tìm key có ít usage nhất và không bị block."""
        now = datetime.now(timezone.utc)
        
        available = [
            (k, v) for k, v in self.keys.items()
            if v['used'] < self.daily_limit
            and (v['blocked_until'] is None or v['blocked_until'] < now)
        ]
        
        if not available:
            # Chỉ khi thực sự hết sạch key mới kiểm tra Global Cooldown để log warning
            if self.global_cooldown_until and self.global_cooldown_until > now:
                logger.warning(f"🕒 All keys exhausted/blocked. Global cooldown active until {self.global_cooldown_until.strftime('%H:%M:%S')}")
            
            logger.critical("🚨 TẤT CẢ API KEYS ĐỀU ĐANG BẬN HOẶC HẾT HẠN MỨC:")
            for k, v in self.keys.items():
                status = "EXHAUSTED" if v['used'] >= self.daily_limit else f"BLOCKED until {v['blocked_until'].strftime('%H:%M:%S')}" if v['blocked_until'] and v['blocked_until'] > now else "READY (but something is wrong)"
                logger.info(f"   - Key {k[:8]}... | Used: {v['used']}/{self.daily_limit} | Status: {status}")
            return None
            
        # Chọn key có số lần sử dụng ít nhất (Least Used)
        best_key = min(available, key=lambda x: x[1]['used'])[0]
        return best_key
    
    def record_usage(self, key: str):
        """Ghi nhận một lần sử dụng thành công."""
        if key in self.keys:
            self.keys[key]['used'] += 1

    def report_error(self, key: str, status_code: int):
        """Xử lý lỗi và kích hoạt Circuit Breaker nếu cần."""
        if key not in self.keys: return
        
        self.keys[key]['errors'] += 1
        
        if status_code == 429:
            # Block key 1 giờ khi bị rate limit (Circuit Breaker)
            logger.warning(f"⚠️ Key {key[:8]}... rate limited (429). Blocking for 1 hour.")
            self.keys[key]['blocked_until'] = datetime.now(timezone.utc) + timedelta(hours=1)
            
            # Nếu > 80% số key bị block cùng lúc -> Kích hoạt Global Cooldown 15p
            blocked_count = sum(1 for v in self.keys.values() if v['blocked_until'] and v['blocked_until'] > datetime.now(timezone.utc))
            if blocked_count >= len(self.keys) * 0.8:
                logger.critical("🚨 EXTREME ERROR RATE! 80% keys blocked. Activating 15min Global Cooldown.")
                self.global_cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        elif status_code in [401, 403]:
            # Key sai hoặc không có quyền truy cập -> Block 24h
            logger.error(f"🚫 Key {key[:8]}... unauthorized/forbidden ({status_code}). Blocking for 24 hours.")
            self.keys[key]['blocked_until'] = datetime.now(timezone.utc) + timedelta(hours=24)
                
        elif status_code >= 500:
            # Lỗi server có thể tạm block 5 phút
            self.keys[key]['blocked_until'] = datetime.now(timezone.utc) + timedelta(minutes=5)
            
    def get_stats(self):
        """Trả về thống kê sử dụng để hiển thị trên Dashboard sau này."""
        return self.keys
