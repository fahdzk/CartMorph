#!/usr/bin/env bash
# CartMorph — Test runner
# Ensures hermetic test environment matching CI expectations.

set -euo pipefail

# Use project venv if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Hermetic environment
export TZ=UTC
export LANG=C.UTF-8
unset REQUESTS_CA_BUNDLE

# Determine test targets
if [ $# -eq 0 ]; then
    TARGET="tests/"
else
    TARGET="$*"
fi

echo "Running: pytest ${TARGET} -v --tb=short -n 2"
pytest ${TARGET} -v --tb=short -n 2 \
    --override-ini="addopts=" \
    -p no:cacheprovider \
    -q
