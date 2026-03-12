#!/bin/bash
# =============================================================================
# RUN ALL TESTS
# =============================================================================
#
# This script runs all the tests for the Dating Profile Photo Analyzer.
# It shows colorful, verbose output so you can see exactly what's passing
# and what's failing.
#
# Usage:
#   ./run_tests.sh          Run all tests
#   ./run_tests.sh -k foo   Run only tests with "foo" in the name
#
# =============================================================================

echo ""
echo "============================================="
echo "  Dating Profile Photo Analyzer — Tests"
echo "============================================="
echo ""

cd "$(dirname "$0")"

python -m pytest backend/tests/ \
    -v \
    --tb=short \
    -s \
    --no-header \
    "$@"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "============================================="
    echo "  ALL TESTS PASSED"
    echo "============================================="
else
    echo "============================================="
    echo "  SOME TESTS FAILED (exit code: $EXIT_CODE)"
    echo "============================================="
fi
echo ""

exit $EXIT_CODE
