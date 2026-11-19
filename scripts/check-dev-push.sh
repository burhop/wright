#!/bin/sh
set -eu
exec "${PYTHON:-python3}" "$(dirname "$0")/../.github/test_distribution.py" --check-dev-push
