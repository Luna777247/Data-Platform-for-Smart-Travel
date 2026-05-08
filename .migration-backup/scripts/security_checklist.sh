#!/usr/bin/env bash
#
# Smart Travel Data Platform - Production Security Checklist
#
# Run this before production deployment
# Usage: bash scripts/security_checklist.sh

echo "🔐 Smart Travel Platform - Production Security Checklist"
echo "=========================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED=0
WARNINGS=0
PASSED=0

# Helper functions
pass_check() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASSED++))
}

fail_check() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED++))
}

warn_check() {
    echo -e "${YELLOW}⚠️${NC} $1"
    ((WARNINGS++))
}

# ============================================================================
# FILE & ENCODING CHECKS
# ============================================================================
echo -e "${BLUE}=== FILE INTEGRITY ===${NC}"
echo ""

# Check UTF-8 encoding
if file README.md | grep -q "UTF-8"; then
    pass_check "README.md is UTF-8 encoded"
else
    fail_check "README.md has encoding issues"
fi

if file infra/docker-compose.yml | grep -q "UTF-8"; then
    pass_check "infra/docker-compose.yml is UTF-8 encoded"
else
    fail_check "docker-compose.yml has encoding issues"
fi

# ============================================================================
# ENVIRONMENT & SECRETS
# ============================================================================
echo ""
echo -e "${BLUE}=== SECRETS MANAGEMENT ===${NC}"
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    pass_check ".env file created"
else
    fail_check ".env file NOT found - Create from .env.example"
fi

# Check for hardcoded secrets in code
if grep -r "secret_password\|password='" apps/ src/ infra/ --include="*.py" --include="*.yml" --include="*.yaml" 2>/dev/null | grep -v ".env"; then
    fail_check "Hardcoded secrets found in source code"
else
    pass_check "No hardcoded secrets in source code"
fi

# Check .env is in .gitignore
if grep -q "^\.env" .gitignore 2>/dev/null; then
    pass_check ".env is in .gitignore"
else
    fail_check ".env is NOT in .gitignore"
fi

# ============================================================================
# DOCKER & COMPOSE
# ============================================================================
echo ""
echo -e "${BLUE}=== DOCKER CONFIGURATION ===${NC}"
echo ""

# Check docker-compose structure
if [ -f "docker-compose.yml" ] && [ -f "docker-compose.dev.yml" ] && [ -f "docker-compose.prod.yml" ]; then
    pass_check "Docker-compose files properly organized"
else
    fail_check "Docker-compose structure incomplete"
fi

# Check NGINX configuration
if [ -f "infra/nginx/nginx.conf" ]; then
    pass_check "NGINX configuration exists"
    if grep -q "ssl_certificate\|ssl_protocols" infra/nginx/nginx.conf; then
        pass_check "NGINX has SSL/TLS configuration"
    else
        warn_check "NGINX SSL/TLS not configured"
    fi
else
    fail_check "NGINX configuration missing"
fi

# ============================================================================
# API SECURITY
# ============================================================================
echo ""
echo -e "${BLUE}=== API SECURITY ===${NC}"
echo ""

# Check for CORS configuration
if grep -q "ALLOWED_ORIGINS\|allowed_origins_list" apps/backend/app/main.py; then
    pass_check "CORS configured from environment"
else
    warn_check "CORS may still use hardcoded origins"
fi

# Check for rate limiting
if grep -q "RateLimiter\|rate_limit" apps/backend/app/core/security_middleware.py; then
    pass_check "Rate limiting middleware implemented"
else
    fail_check "Rate limiting NOT implemented"
fi

# Check for security headers
if grep -q "X-Content-Type-Options\|X-Frame-Options\|Strict-Transport-Security" apps/backend/app/core/security_middleware.py; then
    pass_check "Security headers middleware implemented"
else
    fail_check "Security headers NOT implemented"
fi

# Check for audit logging
if grep -q "AuditLogger\|Audit" apps/backend/app/main.py; then
    pass_check "Audit logging implemented"
else
    fail_check "Audit logging NOT implemented"
fi

# Check for JWT validation
if grep -q "TokenManager\|verify_token" apps/backend/app/core/security_middleware.py; then
    pass_check "JWT token management implemented"
else
    warn_check "JWT token management needs review"
fi

# ============================================================================
# CI/CD PIPELINES
# ============================================================================
echo ""
echo -e "${BLUE}=== CI/CD PIPELINES ===${NC}"
echo ""

# Check GitHub Actions workflows
if [ -f ".github/workflows/ci.yml" ]; then
    pass_check "CI workflow exists"
else
    fail_check "CI workflow (.github/workflows/ci.yml) missing"
fi

if [ -f ".github/workflows/cd.yml" ]; then
    pass_check "CD workflow exists"
else
    fail_check "CD workflow (.github/workflows/cd.yml) missing"
fi

if [ -f ".github/workflows/security.yml" ]; then
    pass_check "Security scanning workflow exists"
else
    fail_check "Security workflow (.github/workflows/security.yml) missing"
fi

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
echo ""
echo -e "${BLUE}=== DATABASE CONFIGURATION ===${NC}"
echo ""

# Check for environment variable configuration (look for ${VAR} style usage)
if grep -qE '\$\{(MONGODB_PASSWORD|POSTGRES_PASSWORD|REDIS_PASSWORD)' docker-compose.yml; then
    pass_check "Database passwords use environment variables"
else
    fail_check "Database passwords may be hardcoded"
fi

# Check data versioning
if [ -f "src/shared/data_versioning.py" ]; then
    pass_check "Data versioning schema exists"
else
    warn_check "Data versioning schema missing"
fi

# ============================================================================
# AIRFLOW CONFIGURATION
# ============================================================================
echo ""
echo -e "${BLUE}=== AIRFLOW CONFIGURATION ===${NC}"
echo ""

# Check for sys.path hacks
if grep -q "sys.path.insert" dags/smart_travel_pipeline.py; then
    fail_check "Airflow DAG still uses sys.path hacks"
else
    pass_check "Airflow DAG imports are clean"
fi

# ============================================================================
# MONITORING & LOGGING
# ============================================================================
echo ""
echo -e "${BLUE}=== MONITORING & LOGGING ===${NC}"
echo ""

# Check for Prometheus metrics
if grep -q "Instrumentator\|/metrics" apps/backend/app/main.py; then
    pass_check "Prometheus metrics configured"
else
    fail_check "Prometheus metrics NOT configured"
fi

# Check for structured logging
if grep -q "setup_logging\|logger\|LOG_LEVEL" apps/backend/app/main.py; then
    pass_check "Structured logging configured"
else
    fail_check "Structured logging NOT configured"
fi

# ============================================================================
# CODE QUALITY
# ============================================================================
echo ""
echo -e "${BLUE}=== CODE QUALITY ===${NC}"
echo ""

# Check for linting config
if [ -f "pyproject.toml" ]; then
    pass_check "Python project configuration (pyproject.toml) exists"
    if grep -q "black\|flake8\|mypy" pyproject.toml; then
        pass_check "Linting tools configured"
    else
        warn_check "Linting tools configuration incomplete"
    fi
else
    fail_check "pyproject.toml NOT found"
fi

# Check for test configuration
if [ -f "pytest.ini" ]; then
    pass_check "Pytest configuration exists"
else
    warn_check "pytest.ini NOT found - Tests may not run properly"
fi

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================
echo ""
echo "=========================================================="
echo -e "${BLUE}📊 SECURITY CHECKLIST RESULTS${NC}"
echo "=========================================================="
echo ""
echo -e "  ${GREEN}✅ Passed:${NC}  $PASSED checks"
echo -e "  ${YELLOW}⚠️  Warnings:${NC} $WARNINGS checks"
echo -e "  ${RED}❌ Failed:${NC}  $FAILED checks"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}🚨 CRITICAL: $FAILED issues must be fixed before production!${NC}"
    echo ""
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warnings - Review before production${NC}"
    echo ""
    exit 0
else
    echo -e "${GREEN}✅ ALL CHECKS PASSED - READY FOR PRODUCTION!${NC}"
    echo ""
    exit 0
fi
