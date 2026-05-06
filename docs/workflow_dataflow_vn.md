# Tài liệu Luồng dữ liệu và Quy trình Hệ thống (Workflow & Dataflow)

Tài liệu này mô tả chi tiết cách thức dữ liệu di chuyển trong hệ thống **Smart Travel Data Platform** và các quy trình tự động hóa đi kèm.

## 1. Luồng dữ liệu (Dataflow - Medallion Architecture)

Hệ thống sử dụng kiến trúc **Medallion (Bronze -> Silver -> Gold)** để quản lý vòng đời dữ liệu.

### Tầng Bronze (Dữ liệu Thô - Raw Zone)

* **Nguồn:** Dữ liệu được thu thập từ bộ sưu tập Overpass API (OSM) và Google Places API.
* **Quy trình:**
    1. Dữ liệu JSON thô được tải về.
    2. Hệ thống gán mã định danh duy nhất `u_key` dựa trên (Tên + Vị trí).
    3. Lưu trữ nguyên bản vào **MinIO** (mục `lakehouse/bronze/`) hoặc local disk làm bản sao lưu.
* **Mục tiêu:** Lưu trữ lịch sử thu thập, cho phép tái xử lý (re-process) nếu thuật toán thay đổi.

### Tầng Silver (Dữ liệu Sạch - Trusted Zone)

* **Quy trình xử lý (`SilverProcessor`):**
    1. Đọc dữ liệu từ Bronze.
    2. Chuẩn hóa kiểu dữ liệu (ví dụ: chuyển rating từ chuỗi sang số).
    3. Loại bỏ bản ghi trùng lặp (Deduplication) dựa trên `u_key`.
    4. **Hợp nhất OSM & Google:** Kết hợp thông tin địa lý từ OSM với các đánh giá (Reviews/Rating) từ Google.
* **Định dạng:** Lưu trữ dưới dạng **Parquet** để tối ưu hiệu suất truy vấn.

### Tầng Gold (Dữ liệu Phục vụ - Serving Zone)

* **Quy trình:**
    1. Dữ liệu sạch từ lớp Silver được đẩy vào **MongoDB Atlas** (collection `places`).
    2. Các trường địa lý được chuyển đổi sang định dạng `2dsphere` để hỗ trợ tìm kiếm quanh vị trí người dùng.
* **Mục tiêu:** Cung cấp dữ liệu đã sẵn sàng cho API và Dashboard hiển thị.

---

## 2. Quy trình Công việc (Workflows)

### 2.1. Quy trình Thu thập và Tích hợp API

* **Thành phần:** `OSMCollector`, `GoogleEnrichor`, `SmartKeyManager`.
* **Luồng hoạt động:**
    1. Người dùng chọn Thành phố và Loại địa điểm trên giao diện.
    2. Backend gửi tín hiệu kích hoạt DAG tương ứng trong Airflow.
    3. `SmartKeyManager` luân chuyển API Key để tránh bị giới hạn (Rate Limit).
    4. Dữ liệu được đẩy vào tầng Bronze.

### 2.2. Quy trình Xử lý Batch (Định kỳ)

* **Thành phần:** Apache Airflow Scheduler.
* **Luồng hoạt động:**
    1. DAG chạy theo lịch trình (ví dụ: hàng ngày).
    2. Tự động quét các folder mới trong Bronze.
    3. Chạy `SilverProcessor` để cập nhật dữ liệu mới vào lớp Silver.
    4. Trigger cập nhật lại bộ chỉ số Heatmap trên Dashboard.

### 2.3. Quy trình Dashboard & Analytics

* **Thành phần:** FastAPI Dashboard Adapter.
* **Luồng hoạt động:**
    1. Frontend gửi yêu cầu thống kê (Stats Request).
    2. FastAPI thực hiện **Aggregation Pipeline** trên MongoDB để tính toán các ma trận dữ liệu.
    3. Áp dụng thuật toán **Weighted Rating** (Trung bình trọng số) để đưa ra bảng xếp hạng thực tế hơn so với chỉ số raw.
    4. Trả về dữ liệu dạng GeoJSON hoặc ma trận cho Heatmap.

---

## 3. Bản đồ Hạ tầng Kỹ thuật

Hệ thống vận hành trên Docker Compose với 5 thành phần chính:

1. **Orchestration:** Apache Airflow (Dags/Scheduler).
2. **Storage:** MinIO (Bronze Layer).
3. **Database:** MongoDB Atlas (Gold Layer) & PostgreSQL (Analytics).
4. **Backend:** FastAPI (Data Processing & Serving).
5. **Frontend:** Next.js (Visual Interface).
