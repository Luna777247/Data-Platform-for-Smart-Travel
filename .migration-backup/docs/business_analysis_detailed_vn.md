# Tài liệu Phân tích Nghiệp vụ Chi tiết (Detailed Business Analysis)

## Dự án: Smart Travel Data Platform (Hệ thống Nền tảng Dữ liệu Du lịch Thông minh)

---

### 1. Conceptual Model: Bức tranh tổng quan (BACCM Framework)

Hệ thống được phân tích dựa trên khung **BACCM (Business Analysis Core Concept Model)** để đảm bảo bao quát toàn bộ giá trị nghiệp vụ.

#### 1.1. Contexts: Ngữ cảnh dự án

- **Mục tiêu chiến lược:** Chuyển đổi từ thu thập dữ liệu rời rạc sang xây dựng tài sản dữ liệu du lịch tập trung, có khả năng thương mại hóa và hỗ trợ ra quyết định.
- **Bối cảnh dự án:** Sự bùng nổ của du lịch tự túc sau đại dịch yêu cầu dữ liệu chính xác về địa điểm, giá cả và dịch vụ thực tế hơn là thông tin quảng cáo.
- **Tầm nhìn:** Trở thành "bộ não" dữ liệu cho ngành du lịch Việt Nam, bắt đầu từ thị trường Hà Nội.
- **Khách hàng:** Các công ty du lịch (OTA), startup du lịch, và các cơ quan quy hoạch đô thị.
- **Cạnh tranh:** Khác biệt với các nền tảng cũ bằng cách tích hợp AI (Gemini) để phân tích cảm xúc và làm giàu dữ liệu tự động.
- **Quy định:** Tuân thủ GDPR/Nghị định 13 về bảo vệ dữ liệu cá nhân (đối với thông tin Review của User).
- **Công nghệ:** Sử dụng Modern Data Stack (Airflow, MinIO, MongoDB, FastAPI).

#### 1.2. Stakeholders: Nhóm liên quan

| Nhóm Stakeholders | Vai trò | Mối quan tâm | Giá trị kỳ vọng | Chiến lược |
| :--- | :--- | :--- | :--- | :--- |
| **Ban Giám đốc** | Quyết định đầu tư | ROI, Tốc độ chiếm lĩnh thị trường | Dữ liệu độc quyền, báo cáo chiến lược | Cung cấp dashboard Real-time |
| **Đội ngũ Data Engineer** | Xây dựng hệ thống | Tính ổn định, Khả năng mở rộng | Pipeline không lỗi, Code sạch | Automation và CI/CD |
| **Đội ngũ Vận hành (Ops)** | Quản trị dữ liệu | Chất lượng dữ liệu, Chi phí API | Dữ liệu không trùng, Key Google không tốn phí | Cấu hình tự động và cảnh báo |
| **Người dùng cuối (Analysts)** | Khai thác dữ liệu | Độ chính xác, Tính trực quan | Truy vấn nhanh, dữ liệu đã làm sạch | API chuẩn RESTful/PostGIS |

#### 1.3. Need: Nhu cầu thực tế

- Cần một kho dữ liệu "Đầy đủ - Cập nhật" về POIs (Point of Interests).
- Khả năng truy vết nguồn gốc dữ liệu (Data Lineage) để đảm bảo độ tin cậy.
- Nhu cầu về một Admin Center tập trung để quản lý hàng trăm nghìn bản ghi.

#### 1.4. Changes: Sự thay đổi

- **Tư duy & Chính sách:** Từ "Lấy được càng nhiều càng tốt" sang "Dữ liệu chất lượng và tuân thủ".
- **Quy trình & Tổ chức:** Chuyển từ xử lý thủ công sang quy trình tự động hoàn toàn (Airflow Orchestrated).
- **Trạng thái hiện tại:** Dữ liệu nằm rải rác ở OSM, Google, không có sự liên kết.
- **Trạng thái mong muốn:** Một nền tảng Lakehouse duy nhất, dữ liệu được gộp (Merge) thông minh bằng AI.

#### 1.5. Solutions: Giải pháp

- **Model:** Kiến trúc Medallion (Bronze -> Silver -> Gold).
- **Chức năng chính:** Ingestion tự động, AI Enrichment, Deduplication, Geospatial Analytics.

#### 1.6. Values: Giá trị mang lại & KPIs

- **Nhóm hiệu quả:** Giảm 80% thời gian thu thập dữ liệu bằng tay. (KPI: Thời gian xử lý 10,000 POI < 1 giờ).
- **Nhóm chất lượng:** Độ chính xác dữ liệu đạt > 95%. (KPI: Tỉ lệ bản ghi hoàn thiện u_key đạt 100%).
- **Tác động:** Giúp doanh nghiệp lữ hành tăng 30% hiệu quả lập kế hoạch tour nhờ dữ liệu thị trường thực tế.

---

### 2. Business Life Cycle: Bản đồ giá trị dữ liệu

Dữ liệu đi qua các trạng thái (Stages) cốt lõi của một vòng đời dữ liệu doanh nghiệp:

**Capture (Thu thập) → Ingest (Nạp) → Process (Xử lý) → Enrich (Làm giàu) → Serve (Phục vụ) → Archive (Lưu trữ)**

- **Create/Capture:** Thu thập raw POI từ OSM/Scrapers.
- **Review/Inspect:** Silver Layer kiểm tra chất lượng (Data Quality Check).
- **Approve/Approve:** Dữ liệu đạt ngưỡng (Score > 0.7) mới được đẩy lên Gold Layer.
- **Pay/Utilize:** Dữ liệu được tiêu thụ bởi Dashboard hoặc API thương mại.
- **Close/Archive:** Dữ liệu cũ được nén và lưu trữ lạnh để truy vết lịch sử (Data Lineage).

---

### 3. Domain, Glossary, Rule: Thành phần kiến trúc

#### 3.1. Domain: Các miền nghiệp vụ

- **Geospatial Domain:** Tọa độ, BBox, District, City.
- **Engagement Domain:** Rating, Review, Social Media Tags.
- **Technical Domain:** API Keys, Scraper Status, Pipeline Health.

#### 3.2. Glossary: Thuật ngữ chuyên môn

- **POI (Point of Interest):** Địa điểm quan tâm (Nhà hàng, khách sạn, di tích).
- **u_key:** Khóa định danh duy nhất được hệ thống tự tạo để khử trùng (Deduplication).
- **BBox (Bounding Box):** Khung tọa độ (Lat/Lon) giới hạn khu vực thu thập dữ liệu.
- **Lineage:** Dòng vết, thể hiện bản ghi này được lấy từ nguồn nào, qua bước nào.

#### 3.3. Rules: Quy tắc nghiệp vụ

- **Rule 1 (Deduplication):** Nếu 2 POI có cùng `u_key` (tính từ tên chuẩn hóa + tọa độ làm tròn), hệ thống chỉ giữ lại 1 bản ghi và gộp thuộc tính (Merge attributes).
- **Rule 2 (Quality Guardrail):** Các bản ghi thiếu Tên hoặc Tọa độ sẽ bị đẩy vào vùng "Error Zone" trong Silver Layer để xử lý sau.
- **Rule 3 (Security):** Admin chỉ được xem thông tin User, không được xem mật khẩu (Hashed).

---

### 4. Actor và Action: Chủ thể và hành động

| Actor | Action (Hành động) | Trigger (Tác nhân) | Event (Sự kiện sinh ra) |
| :--- | :--- | :--- | :--- |
| **System Admin** | Cấu hình BBox | Nhu cầu mở rộng thị trường | `ConfigUpdated` |
| **System Admin** | Quản lý API Keys | Key chính bị hết hạn (Signal) | `KeyPairRotated` |
| **Airflow Scheduler** | Kích hoạt Ingestion | Đến giờ định kỳ (Event-based) | `PipelineStarted` |
| **Silver Processor** | Clean & Deduplicate | Dữ liệu mới vào Bronze | `DataNormalized` |
| **End User** | Truy vấn Dashboard | Muốn xem báo cáo | `ReportGenerated` |

**Flow tiêu chuẩn:**
`Actor (Admin)` → `Action (Submit Job)` → `Rule (Check Key Health)` → `Event (IngestionSucceeded)`

---

### 5. Object và attribute: Đối tượng và thuộc tính

Hệ thống được thiết kế theo mô hình tài liệu (Cơ sở dữ liệu NoSQL - MongoDB):

#### 5.1. Object: Place (Địa điểm)

- **Attribute:** `u_key`, `name`, `city`, `type`, `rating`, `location` (GeoJSON), `reviews`, `photos`, `_lineage_source`.
- **Relationship:** 1-N với Review, 1-1 với PipelineStatus.

#### 5.2. Object: User (Người dùng quản trị)

- **Attribute:** `id`, `email`, `role` (Admin/Operator), `status` (Active/Inactive).

#### 5.3. Object: PipelineStatus

- **Attribute:** `city`, `last_run`, `records_count`, `quality_score`.

---

### 6. Workflow và Data flow: Luồng công việc và Dữ liệu

#### 6.1. Workflow (Business Flow)

Cấu trúc theo tiêu chuẩn BPMN:
`Start` → `Define City/BBox` → `Run Ingestion` → `Quality Audit` → `Enrich with Google/AI` → `Approve to Gold` → `End`

#### 6.2. Data Flow (Luồng dữ liệu kỹ thuật)

Luồng dữ liệu được thiết kế theo mô hình kiến trúc hướng sự kiện (Event-driven) và vi dịch vụ (Microservices):

1. **UI (Frontend Admin):** Người dùng nhập tham số (City, BBox) và nhấn nút "Run Pipeline".
2. **API (FastAPI Backend):** Tiếp nhận request, thực hiện xác thực JWT và kiểm tra quyền RBAC.
3. **Service (Airflow/Worker):** FastAPI gọi Airflow REST API để kích hoạt DAG. Worker bắt đầu fetch dữ liệu.
4. **Store (Bronze - MinIO):** Dữ liệu thô JSON được lưu trữ ngay lập tức để làm bằng chứng (Auditing).
5. **Process (Silver Processor):** Đọc từ Bronze, thực hiện logic nghiệp vụ (Deduplication, Normalize).
6. **DB (Gold - MongoDB):** Dữ liệu sạch được ghi vào MongoDB để phục vụ truy vấn thời gian thực.
7. **Event (Status Updated):** Sau khi nạp xong, hệ thống sinh ra sự kiện `DataReadyEvent`.
8. **Service khác (Dashboard/Notification):** Dashboard nhận sự kiện để làm mới cache, dịch vụ thông báo gửi Alert cho Admin qua Telegram/Email.

**Tóm tắt 4 bước tiêu chuẩn:**
`Input (Source APIs)` -> `Process (Transformation & AI)` -> `Store (Lakehouse Layers)` -> `Output (Visualized Insights)`

---
*Tài liệu này là tài sản nghiệp vụ của Smart Travel Data Platform, dùng để hướng dẫn phát triển và kiểm soát chất lượng dữ liệu.*
