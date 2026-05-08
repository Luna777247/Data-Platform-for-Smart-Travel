# Đặc tả Chi tiết Giao diện & Nghiệp vụ Hệ thống (v2.0)

**Dự án: Smart Travel Data Platform**

Tài liệu này mô tả chi tiết cách chuyển đổi toàn bộ các tính năng hiện có sang cấu trúc mới, đảm bảo tính kế thừa và tối ưu hóa trải nghiệm người dùng.

---

## I. Cấu trúc Tổng thể (Master Layout)

Hệ thống sẽ chuyển sang mô hình **"App-Centric"** với Sidebar cố định.

### 1. Sidebar (Menu Điều hướng Dọc)

- **Nhóm 1: Giám sát chiến lược (Executive)**
  - **Tổng quan (Overview):** Chứa các chỉ số Uptime, Uptime healthy status, và các biểu đồ 24h Runs.
  - **Phân tích Du lịch (Travel Analytics):** Kế thừa từ `Smart Travel Demo`, hiển thị bản đồ POI và thống kê Rating.
- **Nhóm 2: Vận hành dữ liệu (Data Operations)**
  - **Kết nối API (Connectors):** Kế thừa từ `API Connections`, nơi cấu hình Endpoint và Auth.
  - **Sơ đồ Ánh xạ (Mappings):** Kế thừa từ `Field Mappings`, cấu hình cách JSON API đổ vào Database.
  - **Lập lịch (Automation):** Kế thừa từ `Schedules`, quản lý CRON jobs.
  - **Lịch sử chạy (Pipeline Logs):** Kế thừa từ `Run History`.
- **Nhóm 3: Tài nguyên & Quản trị (Admin)**
  - **Admin Portal:** Gộp 3 tab: Key Manager, OSM Config, Enrichment Config.
  - **Hệ thống (Settings):** Quản lý Backup, Users và Roles.

---

## II. Chi tiết từng Module & Chức năng

### 1. Module Dashboard Overview (Trang chủ mới)

* **Chỉ số Uptime & Health:** Hiển thị dạng Badge lớn ở góc trên cùng. `✓ Healthy` xanh lá nếu API Backend phản hồi tốt.
- **Biểu đồ Hiệu suất (Performance Charts):**
  - Thay thế `Total Runs (72)` và `24h Runs (61)` bằng một biểu đồ đường (Line chart) để thấy xu hướng theo giờ.
  - **Success Rate (481%):** Hiển thị dạng Progress Ring hoặc Gauge Chart (đồng hồ đo) để cảnh báo khi tỷ lệ này sụt giảm.
- **Khu vực "Getting Started":** Giữ nguyên nút `[Create First Connection]` nhưng thu nhỏ lại thành một Banner hướng dẫn ở cuối trang cho người mới.

### 2. Module Ingestion Lab (Xử lý OSM)

* **Quy trình (Workflow):**
  - Search thành phố -> Kiểm tra BBox -> Chọn loại POI -> Trigger Lấy dữ liệu.
- **Tính năng Dynamic Parameters:** Tích hợp trực tiếp vào form thu thập (Date ranges, custom logic).
- **Hành động (Actions):**
  - `[Test Query]`: Chạy thử Overpass Query trước khi lưu chính thức.
  - `[Export Raw]`: Xuất dữ liệu Bronze Layer ra file CSV hoặc JSON.

### 3. Module Enrichment Lab (Làm giàu từ Google)

* **Quy trình (Workflow):**
  - Chọn dữ liệu từ Silver Layer -> Chọn Strategy (Fields, Language) -> Start Enrichment.
- **Tính năng Multi-Parameter Support:** Cho phép tích chọn đồng thời nhiều loại địa điểm (Cartesian product mode) để thực hiện làm giàu hàng loạt.
- **Hành động (Actions):**
  - `[Key Rotation Status]`: Xem key nào đang được "SmartKeyManager" ưu tiên sử dụng.

### 4. Module Data Explorer (Khám phá dữ liệu)

* **Quy trình (Workflow):**
  - Lọc dữ liệu theo Thành phố, Rating, Nguồn (OSM/Google).
- **Hành động (Actions):**
  - `[Visual Mapping]`: Xem trực tiếp cấu trúc JSON đã được `Automatic Schema Detection` xử lý.
  - `[Push to Gold]`: Đẩy dữ liệu đã làm sạch lên lớp Gold để phục vụ Dashboards.

---

## III. Đặc tả các Nút bấm (Button Interface)

| Button Name | Vị trí | Sự kiện (Event) | Chức năng chi tiết |
| :--- | :--- | :--- | :--- |
| **New Connection $[+]$** | Header (Toàn cục) | `OPEN_WIZARD` | Mở trình thuật sĩ cấu hình API mới chỉ với 3 bước. |
| **Trigger All Checks** | Admin > Keys | `VALIDATE_ALL` | Quét toàn bộ 18+ key để cập nhật trạng thái `Ready/Exhausted`. |
| **Sync BBox** | Admin > OSM | `MAP_SYNC` | Đồng bộ tọa độ từ bản đồ trực quan vào file cấu hình `cities.json`. |
| **Force Clean Cache** | Settings | `CLEAR_STORAGE` | Xóa các file rác trong `storage/tmp` để giải phóng bộ nhớ. |

---

## IV. Cải tiến Logic Ẩn (Hidden Logic)

- **Automatic Schema Detection:** Khi bạn nhập một URL API mới trong mục Connectors, hệ thống sẽ tự động gửi một request mẫu, phân tích cấu trúc JSON trả về và tự động gợi ý các Field Mapping tương ứng.
- **Comprehensive Logging:** Mỗi khi bạn nhấn nút `Trigger Harvest`, một `Run_ID` duy nhất sẽ được tạo ra, cho phép bạn theo dõi từ lúc dữ liệu là Bronze (thô) cho đến khi thành Gold (phân tích) mà không bị mất dấu vết.

---
*Tài liệu này đảm bảo mọi tính năng cũ đều được đặt vào đúng vị trí "tự nhiên" nhất, giúp người dùng làm việc hiệu quả hơn 200%.*
