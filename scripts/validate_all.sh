#!/usr/bin/env bash
# validate_all.sh — run tests for every Python and R package in the phil ecosystem.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
SKIP=0
RESULTS=()

separator() {
    printf '\n%s\n' "────────────────────────────────────────────────────────"
}

record() {
    local name="$1" status="$2"
    RESULTS+=("${status}  ${name}")
    if [[ "$status" == "PASS" ]]; then
        ((PASS++))
    elif [[ "$status" == "FAIL" ]]; then
        ((FAIL++))
    else
        ((SKIP++))
    fi
}

# ── Python packages ─────────────────────────────────────────────────────────

echo "=== Python packages ==="
for pkg_dir in "$ROOT"/python/*/; do
    pkg_name="$(basename "$pkg_dir")"
    separator
    echo "▶ $pkg_name"

    if [[ ! -f "$pkg_dir/pyproject.toml" && ! -f "$pkg_dir/setup.py" && ! -f "$pkg_dir/setup.cfg" ]]; then
        echo "  (no pyproject.toml / setup.py — skipping)"
        record "$pkg_name" "SKIP"
        continue
    fi

    if python -m pytest "$pkg_dir" --tb=short -q 2>&1; then
        record "$pkg_name" "PASS"
    else
        record "$pkg_name" "FAIL"
    fi
done

# ── Integration tests ───────────────────────────────────────────────────────

separator
echo "▶ integration tests"
if python -m pytest "$ROOT/tests/" --tb=short -q 2>&1; then
    record "tests/integration" "PASS"
else
    record "tests/integration" "FAIL"
fi

# ── R packages ──────────────────────────────────────────────────────────────

echo ""
echo "=== R packages ==="
for pkg_dir in "$ROOT"/r/*/; do
    pkg_name="$(basename "$pkg_dir")"
    separator
    echo "▶ $pkg_name"

    if [[ ! -f "$pkg_dir/DESCRIPTION" ]]; then
        echo "  (no DESCRIPTION — skipping)"
        record "$pkg_name (R)" "SKIP"
        continue
    fi

    if command -v R >/dev/null 2>&1; then
        if R CMD check --no-manual --no-vignettes "$pkg_dir" 2>&1; then
            record "$pkg_name (R)" "PASS"
        else
            record "$pkg_name (R)" "FAIL"
        fi
    else
        echo "  (R not found — skipping)"
        record "$pkg_name (R)" "SKIP"
    fi
done

# ── Summary ─────────────────────────────────────────────────────────────────

separator
echo ""
echo "=== Summary ==="
printf '  PASS: %d  |  FAIL: %d  |  SKIP: %d\n' "$PASS" "$FAIL" "$SKIP"
echo ""
for line in "${RESULTS[@]}"; do
    echo "  $line"
done
echo ""

if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
