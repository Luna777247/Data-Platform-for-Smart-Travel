#!/bin/bash
# setup.sh - Environment Setup Script
# =====================================
# Script thiết lập môi trường development cho Smart Tourism Data Platform
# 
# Usage: ./scripts/setup.sh

set -e  # Exit on error

echo "🚀 Smart Tourism Data Platform - Setup Script"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    print_warning "Running on Windows. Some commands may need adjustment."
fi

# 1. Check Python version
print_status "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
print_status "✓ Python version: $python_version"

# 2. Create virtual environment
print_status "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    print_status "✓ Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# 3. Activate virtual environment
print_status "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
print_status "✓ Virtual environment activated"

# 4. Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# 5. Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt
print_status "✓ Dependencies installed"

# 6. Install development dependencies
print_status "Installing development dependencies..."
pip install pytest pytest-asyncio pytest-cov black flake8 mypy
print_status "✓ Development dependencies installed"

# 7. Create .env file if it doesn't exist
print_status "Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status "✓ .env file created from .env.example"
    print_warning "Please edit .env file with your actual configuration values"
else
    print_warning ".env file already exists"
fi

# 8. Create necessary directories
print_status "Creating project directories..."
mkdir -p storage/bronze storage/silver storage/gold
mkdir -p storage/configs
mkdir -p storage/logs
mkdir -p storage/reports
print_status "✓ Project directories created"

# 9. Run pre-commit hooks setup (optional)
if command -v pre-commit &> /dev/null; then
    print_status "Setting up pre-commit hooks..."
    pre-commit install
    print_status "✓ Pre-commit hooks installed"
else
    print_warning "pre-commit not found. Skipping pre-commit setup."
fi

# 10. Verify installation
print_status "Verifying installation..."
python -c "from src.core.config import settings; print('✓ Configuration loaded successfully')"

# Summary
echo ""
echo "=============================================="
echo "✅ Setup completed successfully!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start MongoDB and Redis (or use Docker)"
echo "3. Run: docker-compose up -d"
echo "4. Access API at: http://localhost:8000"
echo "5. API docs at: http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  source venv/bin/activate  # Activate virtual env"
echo "  pytest                    # Run tests"
echo "  black src/                # Format code"
echo "  flake8 src/               # Lint code"
echo ""
