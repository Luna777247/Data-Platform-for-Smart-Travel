# Frontend Next.js - No-Code API Connector

> Giao diện người dùng hiện đại cho nền tảng kết nối API không cần code, được xây dựng bằng Next.js 15 với TypeScript.

## 🚀 Khởi chạy nhanh

### Yêu cầu hệ thống
- Node.js 18+ (khuyến nghị 20+)
- npm hoặc yarn
- Docker & Docker Compose (cho chế độ container)

### Chạy cục bộ (Development)

```bash
# Di chuyển vào thư mục frontend
cd frontendphp

# Cài đặt dependencies
npm install

# Chạy chế độ phát triển (port 3000)
npm run dev

# Truy cập: http://localhost:3000
```

### Chạy production

```bash
# Build ứng dụng
npm run build

# Chạy server production
npm start
```
<!-- 
### Chạy bằng Docker

```bash
# Từ thư mục gốc dự án
docker-compose up -d frontend

# Hoặc chỉ build và chạy container frontend
docker build -t frontendphp ./frontendphp
docker run -p 3000:3000 frontendphp
```

## 📋 Kiến trúc

```
frontendphp/
├── app/                    # Next.js App Router
├── components/             # React components
│   ├── client-*.jsx        # Client-side components
│   └── ui/                 # Reusable UI components (shadcn/ui)
├── hooks/                  # Custom React hooks
├── lib/                    # Utility functions
├── services/               # API client và services
│   └── apiClient.js        # Axios client với caching
├── public/                 # Static assets
└── styles/                 # Global styles
```

### Tính năng chính
- **Dashboard Analytics**: Hiển thị dữ liệu từ Smart Travel API với biểu đồ tương tác
- **API Client**: Axios với timeout 120s và caching 5 phút cho dashboard APIs
- **UI Components**: Shadcn/ui với Radix UI primitives
- **TypeScript**: Type safety cho toàn bộ codebase
- **Responsive Design**: Tailwind CSS cho giao diện hiện đại

## 🔧 Cấu hình

### Biến môi trường
Tạo file `.env.local` trong thư mục `frontendphp`:

```env
# API Backend URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Các biến khác nếu cần
```

### API Endpoints được sử dụng
- `GET /api/smart-travel/dashboard/overview` - Tổng quan dashboard
- `GET /api/smart-travel/dashboard/city-ranking` - Xếp hạng thành phố
- `GET /api/smart-travel/dashboard/city-category-matrix` - Ma trận danh mục
- `GET /api/smart-travel/dashboard/map-data` - Dữ liệu bản đồ

## 📖 Sử dụng

### Dashboard Smart Travel
- **Parallel Loading**: API calls được nhóm và tải song song để tối ưu hiệu suất
- **Caching**: Response được cache 5 phút để giảm tải server
- **Error Handling**: Fallback tự động và logging chi tiết
- **Charts**: Sử dụng Recharts cho biểu đồ tương tác

### Development Scripts

```bash
# Phát triển
npm run dev

# Build
npm run build

# Lint code
npm run lint

# Type checking
npm run type-check
```

## 🔗 Tích hợp với Backend

Frontend kết nối với backend PHP qua HTTP REST API:
- **Base URL**: http://localhost:8000
- **Authentication**: Không yêu cầu (cho development)
- **CORS**: Đã cấu hình cho localhost

### Workflow phát triển
1. Backend chạy trên port 8000
2. Frontend chạy trên port 3000
3. API calls từ frontend đến backend
4. Airflow xử lý scheduling (port 8080)

## 🐳 Docker

### Build image
```bash
docker build -t no-code-api-connector-frontend ./frontendphp
```

### Chạy container
```bash
docker run -d \
  --name frontend \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 \
  no-code-api-connector-frontend
```
 -->

## 📚 Tài liệu bổ sung

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Shadcn/ui Components](https://ui.shadcn.com/)
- [Backend API Docs](../backendphp/README.md)

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.