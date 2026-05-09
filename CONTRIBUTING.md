# Contributing to Smart Tourism Data Platform

Cảm ơn bạn đã quan tâm đến việc đóng góp cho Smart Tourism Data Platform! 🎉

## 📋 Mục lục

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

Dự án này tuân thủ [Code of Conduct](CODE_OF_CONDUCT.md). Bằng việc tham gia, bạn đồng ý tuân thủ các quy tắc này.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker và Docker Compose
- Git

### Setup Development Environment

```bash
# 1. Fork repository về GitHub account của bạn
# 2. Clone repository
git clone https://github.com/YOUR_USERNAME/Data-Platform-for-Smart-Travel.git
cd Data-Platform-for-Smart-Travel

# 3. Chạy setup script
./scripts/setup.sh

# 4. Activate virtual environment
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# 5. Start services
docker-compose up -d

# 6. Verify setup
curl http://localhost:8000/health
```

## Development Workflow

### 1. Tạo Branch

```bash
# Pull latest changes
git checkout main
git pull origin main

# Tạo feature branch
git checkout -b feature/your-feature-name

# Hoặc bugfix branch
git checkout -b fix/bug-description
```

### 2. Naming Conventions

**Branch Names:**
- `feature/description` - Tính năng mới
- `fix/description` - Bug fix
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Tests
- `chore/description` - Maintenance

**Ví dụ:**
- `feature/add-pipeline-retry-logic`
- `fix/mongodb-connection-timeout`
- `docs/update-api-examples`

### 3. Development

```bash
# Làm việc trên code...
# Sau khi hoàn thành:

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Run type checking
mypy src/

# Run tests
pytest

# Run tests với coverage
pytest --cov=src --cov-report=html
```

## Coding Standards

### Python Code Style

**Tuân thủ PEP 8 với các quy định bổ sung:**

```python
# 1. Line length: 100 characters max
# 2. Imports: Được sắp xếp theo thứ tự
import os                    # Standard library
from typing import List      # Typing

import httpx                 # Third-party
from fastapi import FastAPI  # Framework

from src.core.config import settings  # Local imports

# 3. Type hints bắt buộc cho function parameters và return types
def calculate_score(ratings: List[float]) -> float:
    """Calculate average rating score."""
    if not ratings:
        return 0.0
    return sum(ratings) / len(ratings)

# 4. Docstrings cho tất cả public functions/classes
class POIManager:
    """
    Manager class for POI operations.
    
    This class handles CRUD operations for Points of Interest
    và cung cấp các phương thức để query và filter POIs.
    
    Attributes:
        db: MongoDB database instance
        collection: POI collection name
    """
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize POI manager."""
        self.db = db
        self.collection = "pois"

# 5. Error handling rõ ràng
try:
    result = await process_data(data)
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")

# 6. Logging thay vì print
from src.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing started", extra={"records": len(data)})
logger.debug("Detailed debug info", extra={"data": data})
```

### Comment Standards

**Mọi dòng code phải có comment giải thích bằng tiếng Việt hoặc tiếng Anh:**

```python
# Import các thư viện cần thiết cho FastAPI
from fastapi import FastAPI, HTTPException, Depends

# Khởi tạo ứng dụng FastAPI với metadata
app = FastAPI(
    title="Smart Tourism API",  # Tiêu đề API
    version="1.0.0",            # Phiên bản hiện tại
)

# Lấy logger instance để ghi log
logger = get_logger(__name__)

# Định nghĩa route cho health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Kiểm tra trạng thái sức khỏe của API."""
    return {"status": "healthy"}  # Trả về status healthy
```

### Async/Await Patterns

```python
# Luôn sử dụng async cho I/O operations
async def fetch_data(url: str) -> dict:
    """Fetch data from external API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)  # Non-blocking I/O
        response.raise_for_status()
        return response.json()

# Database operations
async def get_poi_by_id(poi_id: str) -> Optional[POI]:
    """Get POI by ID from database."""
    db = get_database()
    doc = await db.pois.find_one({"poi_id": poi_id})  # Async query
    return POI(**doc) if doc else None
```

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: Tính năng mới
- `fix`: Bug fix
- `docs`: Thay đổi documentation
- `style`: Code style changes (formatting, missing semi colons, etc)
- `refactor`: Code refactoring
- `test`: Thêm tests
- `chore`: Maintenance tasks

### Examples

```
feat(pipeline): Add retry mechanism cho failed tasks

Implement exponential backoff retry logic cho pipeline tasks
để xử lý transient failures từ external APIs.

- Add RetryConfig dataclass
- Implement retry decorator
- Add unit tests

Fixes #123
```

```
fix(api): Resolve MongoDB connection timeout issue

Increase connection timeout và add connection pool settings
trong database configuration.

- Update MongoDB client options
- Add connection health checks
- Update documentation

Closes #456
```

```
docs(readme): Update API documentation với new endpoints

Thêm documentation cho monitoring và admin endpoints.
Update example requests và responses.
```

## Pull Request Process

### 1. Before Submitting

```bash
# Đảm bảo code được format
black src/ tests/

# Kiểm tra linting
flake8 src/ tests/

# Chạy type checking
mypy src/

# Chạy tất cả tests
pytest

# Kiểm tra test coverage
pytest --cov=src --cov-report=html
```

### 2. PR Template

```markdown
## Description
Mô tả ngắn gọn về thay đổi.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added cho complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] All tests pass

## Related Issues
Fixes #(issue number)
```

### 3. Review Process

1. **Tự review** trước khi submit
2. **Automated checks** phải pass (CI/CD)
3. **Code review** bởi ít nhất 1 reviewer
4. **Address feedback** và update PR
5. **Merge** sau khi approved

## Testing

### Test Structure

```
tests/
├── conftest.py              # Test configuration
├── unit/                    # Unit tests
│   ├── test_core/          # Core module tests
│   ├── test_services/      # Service tests
│   └── test_utils/         # Utility tests
├── integration/             # Integration tests
│   ├── test_api/           # API endpoint tests
│   ├── test_db/            # Database tests
│   └── test_pipeline/      # Pipeline tests
└── fixtures/               # Test data
    ├── sample_data.json
    └── mock_responses.json
```

### Writing Tests

```python
# tests/unit/test_services/test_pipeline.py
import pytest
from src.services.pipeline_management_service import PipelineManagementService

@pytest.fixture
def pipeline_service():
    """Create pipeline service instance."""
    return PipelineManagementService()

@pytest.mark.asyncio
async def test_start_pipeline_success(pipeline_service):
    """Test successful pipeline start."""
    # Arrange
    request = PipelineExecutionRequest(
        pipeline_id="test_pipeline",
        config={"city": "tokyo"}
    )
    
    # Act
    result = await pipeline_service.start_pipeline(request)
    
    # Assert
    assert result.status == "STARTED"
    assert result.execution_id is not None

@pytest.mark.asyncio
async def test_start_pipeline_invalid_config(pipeline_service):
    """Test pipeline start với invalid config."""
    # Arrange
    request = PipelineExecutionRequest(
        pipeline_id="invalid_pipeline",
        config={}
    )
    
    # Act & Assert
    with pytest.raises(ValidationError):
        await pipeline_service.start_pipeline(request)
```

### Running Tests

```bash
# Run all tests
pytest

# Run với verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_config.py

# Run specific test
pytest tests/unit/test_config.py::test_settings_singleton

# Run với coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run integration tests only
pytest tests/integration/

# Run unit tests only
pytest tests/unit/
```

## Documentation

### Code Documentation

- **Module docstrings**: Mô tả purpose và usage
- **Class docstrings**: Mô tả attributes và methods
- **Function docstrings**: Args, Returns, Raises, Examples
- **Inline comments**: Giải thích complex logic

### API Documentation

- OpenAPI specification trong `docs/api/openapi.yaml`
- FastAPI auto-generated docs tại `/docs`
- Postman collection trong `docs/api/postman_collection.json`

### User Documentation

- Update `README.md` nếu thay đổi major features
- Update `docs/` cho detailed guides
- Thêm examples cho new features

## Release Process

### Version Numbering

Tuân thủ [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Steps

1. **Update version** trong `src/__init__.py`
2. **Update CHANGELOG.md** với new version
3. **Create release branch**: `git checkout -b release/v1.1.0`
4. **Final testing** và bug fixes
5. **Merge to main**: Create PR và merge
6. **Create Git tag**: `git tag -a v1.1.0 -m "Release v1.1.0"`
7. **Push tags**: `git push origin v1.1.0`
8. **Create GitHub release** với notes

## Getting Help

- **General questions**: Tạo GitHub Discussion
- **Bug reports**: Tạo GitHub Issue với bug template
- **Feature requests**: Tạo GitHub Issue với feature template
- **Security issues**: Email security@smarttourism.vn

## Recognition

Contributors sẽ được ghi nhận trong:
- `CONTRIBUTORS.md` file
- Release notes
- Project documentation

---

**Cảm ơn bạn đã đóng góp cho Smart Tourism Data Platform! 🚀**
