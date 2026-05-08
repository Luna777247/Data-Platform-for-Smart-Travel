#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0
WARNINGS=0
PASSED=0

pass() { echo -e "${GREEN}✅${NC} $1"; PASSED=$((PASSED + 1)); }
warn() { echo -e "${YELLOW}⚠️${NC} $1"; WARNINGS=$((WARNINGS + 1)); }
fail() { echo -e "${RED}❌${NC} $1"; FAILED=$((FAILED + 1)); }

check_absent() {
  local pattern="$1"
  local description="$2"
  local matches
  matches="$(grep -RInE "$pattern" infra apps scripts .github --include='*.yml' --include='*.yaml' --include='*.py' --include='*.sh' --include='*.ps1' 2>/dev/null || true)"
  if [ -n "$matches" ]; then
    echo "$matches"
    fail "$description"
  else
    pass "$description"
  fi
}

echo "Kubernetes secret audit"
echo "======================="

echo
check_absent 'envsubst' 'No envsubst usage in Kubernetes secret flow'
check_absent 'stringData:' 'No plaintext stringData in Kubernetes Secret manifests'
check_absent 'kind: Secret' 'No plain Secret manifests tracked for Kubernetes production path'
check_absent 'password[[:space:]]*:[[:space:]]*"[^"]+"|password[[:space:]]*:[[:space:]]*[^[:space:]]+' 'No plaintext password fields in repo manifests'
check_absent 'MONGO_INITDB_ROOT_PASSWORD|POSTGRES_PASSWORD|REDIS_PASSWORD|SECRET_KEY|JWT_SECRET|MINIO_SECRET_KEY|GOOGLE_PLACES_API_KEY' 'No accidental hardcoded secret values in repo files'
check_absent 'AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z\-_]{35}|sk-[A-Za-z0-9]{20,}' 'No exposed cloud/API keys in repo files'
check_absent '[A-Za-z0-9+/]{32,}={0,2}' 'No suspicious base64 secret blobs in Kubernetes manifests'
check_absent 'kubectl apply -f .*secrets.yaml|secrets.yaml' 'No deployment instructions referencing plaintext secrets.yaml'

if command -v gitleaks >/dev/null 2>&1; then
  if gitleaks detect --no-git --redact --source . --report-format sarif --report-path /tmp/gitleaks.sarif >/dev/null 2>&1; then
    pass 'Gitleaks scan passed'
  else
    fail 'Gitleaks scan found secrets'
  fi
else
  warn 'gitleaks not installed; skipped gitleaks scan'
fi

if command -v trufflehog >/dev/null 2>&1; then
  if trufflehog filesystem . --no-update --fail --json >/dev/null 2>&1; then
    pass 'TruffleHog scan passed'
  else
    fail 'TruffleHog scan found secrets'
  fi
else
  warn 'trufflehog not installed; skipped trufflehog scan'
fi

echo
cat <<EOF
Summary
-------
Passed:  $PASSED
Warnings: $WARNINGS
Failed:  $FAILED
EOF

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
exit 0