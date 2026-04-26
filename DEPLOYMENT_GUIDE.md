# 🚀 Guide Triển Khai: Smart Travel Data Platform (Phase 1)

Chào mừng bạn đến với hệ thống thu thập và xử lý dữ liệu du lịch thông minh. Tài liệu này hướng dẫn cách vận hành hệ thống từ con số 0 đến khi có dữ liệu sạch trong Database.

---

## 🏗 1. Kiến Trúc Medallion (Lakehouse)

Hệ thống vận hành theo 3 tầng dữ liệu để đảm bảo tính toàn vẹn:

- **Bronze (Raw)**: Dữ liệu nguyên bản từ OSM (JSON) và Google (JSON).
- **Silver (Cleaned)**: Dữ liệu đã khử trùng lặp, chuẩn hóa schema và "cứu vãn" tên `unknown` bằng Parquet.
- **Gold (Business)**: Dữ liệu sẵn sàng cho Analytics và API Serving (PostgreSQL/PostGIS).

---

## 🛠 2. Chuẩn Bị Môi Trường

### Yêu cầu hệ thống

- **Python**: 3.10+
- **Database**: PostgreSQL với extension PostGIS.
- **Storage**: Cục bộ (`storage/`) hoặc MinIO.

### Cài đặt thư viện

```bash
pip install pandas pyarrow httpx python-dotenv psycopg2-binary
```

### Cấu hình biến môi trường (`.env`)

Bạn cần ít nhất 1-13 Key từ RapidAPI (Google Map Places).

```env
# Google API Keys (Xoay vòng tự động)
RAPID_API_KEY1=xxx...
RAPID_API_KEY2=yyy...
...

# Database Configuration
DB_HOST=localhost
DB_NAME=smart_travel
DB_USER=postgres
DB_PASS=yourpassword
```

---

## 🔄 3. Luồng Vận Hành (Step-by-Step)

### Bước 1: Thu thập dữ liệu OSM (Bronze)

Quét toàn bộ dữ liệu địa lý cơ bản từ OpenStreetMap cho 9 thành phố lớn.

```bash
python scripts/run_bronze.py
```

*Kết quả: Lưu tại `storage/bronze/osm/{city}/`*

### Bước 2: Dọn dẹp sơ bộ (Silver Initial)

Khử trùng lặp dựa trên `u_key` (Location Hash) để chuẩn bị danh sách làm giàu.

```bash
python scripts/run_silver.py
```

*Kết quả: File Parquet tại `storage/silver/pois_cleaned/{city}/data.parquet`*

### Bước 3: Làm giàu dữ liệu từ Google (Enrichment)

Đây là bước quan trọng nhất để lấy Rating, Review và Số điện thoại.

```bash
# Kiểm tra sức khỏe Key trước khi chạy
python scripts/debug_keys.py

# Chạy làm giàu (Tự động checkpoint nếu hết quota)
python scripts/run_google_enrichment.py
```

*Kết quả: Toàn bộ dữ liệu thô Google lưu tại `storage/bronze/google/{city}/`*

### Bước 4: Hợp nhất & Cứu vãn dữ liệu (Silver Final)

Chạy lại Silver để kích hoạt logic: **Lấy dữ liệu Google đè lên bản ghi `unknown` của OSM**.

```bash
python scripts/run_silver.py
```

### Bước 5: Nạp dữ liệu vào Database (Gold)

Đưa toàn bộ dữ liệu sạch từ Parquet vào PostgreSQL.

```bash
python scripts/run_postgres_loader.py
```

---

## 🛡 4. Cơ Chế Bền Bỉ (Resilience Features)

- **SmartKeyManager**: Tự động xoay vòng 13 Key. Nếu một Key bị lỗi (429/403), nó sẽ bị "cách ly" 1 giờ trước khi thử lại.
- **Incremental Loading**: Mọi file Google Bronze đều được lưu theo `u_key`. Nếu bạn dừng script nửa chừng, ngày mai chỉ cần chạy lại, hệ thống sẽ tự bỏ qua những gì đã xong.
- **Local Fallback**: Nếu hệ thống MinIO không khả dụng, dữ liệu tự động lưu vào ổ cứng cục bộ để không gián đoạn Pipeline.

---

## 📊 5. Giám Sát & Maintenance

- **Báo cáo Key**: Chạy `python debug_keys.py` để xem Key nào còn quota.
- **Kiểm tra dữ liệu**: Toàn bộ dữ liệu Silver được lưu dạng Parquet, có thể đọc nhanh bằng `pandas`.

---
*Tài liệu được cập nhật lần cuối vào: 26/04/2026 bởi Antigravity AI.*
