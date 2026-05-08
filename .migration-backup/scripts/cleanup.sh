#!/bin/bash
#
# Smart Travel Data Platform - Cleanup Script
#
# Removes unused files and configurations
# Usage: bash scripts/cleanup.sh

echo "🧹 Smart Travel Platform Cleanup"
echo "=================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track removed files
REMOVED_COUNT=0

# Function to safely remove file
remove_file() {
    if [ -f "$1" ]; then
        echo -e "${YELLOW}Removing:${NC} $1"
        rm -f "$1"
        ((REMOVED_COUNT++))
    fi
}

# Function to safely remove directory
remove_dir() {
    if [ -d "$1" ]; then
        echo -e "${YELLOW}Removing:${NC} $1"
        rm -rf "$1"
        ((REMOVED_COUNT++))
    fi
}

# ============================================================================
# REMOVE UNUSED FILES
# ============================================================================

echo "🔍 Scanning for unused files..."
echo ""

# Temporary/debug files
remove_file "apps/backend/tmp_check.py"
remove_file "apps/frontend/test_axios_response.js"
remove_file "apps/frontend/convert-ts-to-js.js"
remove_file "temp_log.txt"
remove_file "test_e2e_out.txt"
remove_file "test_lifecycle_err.txt"
remove_file "test_out.txt"

# Old backup files
remove_file "apps/backend/app/main_old.py"
remove_file "dags/smart_travel_pipeline_old.py"

# ============================================================================
# CLEAN UP GIT STATE
# ============================================================================

echo ""
echo "🔧 Cleaning git state..."

# Remove deleted files from git tracking
git rm --cached --quiet $(git ls-files --deleted) 2>/dev/null

# Add cleanup to git
git add -A

# ============================================================================
# REMOVE DUPLICATE DEPENDENCIES
# ============================================================================

echo ""
echo "📦 Checking dependencies..."

if [ -f "apps/frontend/package-lock.json" ] && [ -f "apps/frontend/pnpm-lock.yaml" ]; then
    echo -e "${YELLOW}Both package-lock.json and pnpm-lock.yaml found${NC}"
    echo "Recommendation: Use only npm (keep package-lock.json)"
    echo "To use pnpm: add '.npmrc' with 'shamefully-hoist=false'"
fi

# ============================================================================
# CLEANUP DOCKER LAYERS
# ============================================================================

echo ""
echo "🐳 Docker cleanup options:"
echo "   Run: docker system prune -a"
echo "   This will remove dangling images and unused layers"

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "=================================="
echo -e "${GREEN}✅ Cleanup completed!${NC}"
echo ""
echo "📊 Summary:"
echo "   Files removed: $REMOVED_COUNT"
echo "   Git state: Updated"
echo ""

# Verify no hardcoded secrets
echo "🔐 Checking for hardcoded secrets..."
SECRETS_FOUND=0

# Check for common patterns
for pattern in "password='secret" "password=\"secret" "api_key=" "private_key=" "secret_key="; do
    if grep -r "$pattern" . --include="*.py" --include="*.js" --include="*.yaml" --include="*.yml" 2>/dev/null | grep -v ".env\|.gitignore"; then
        ((SECRETS_FOUND++))
        echo -e "${RED}⚠️  Possible hardcoded secret found!${NC}"
    fi
done

if [ $SECRETS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ No hardcoded secrets detected${NC}"
fi

echo ""
echo "Next steps:"
echo "   1. Review removed files: git diff --cached"
echo "   2. Commit cleanup: git commit -m 'chore: cleanup unused files and configs'"
echo "   3. Deploy: docker-compose up -d"
echo ""
