#!/usr/bin/env bash
set -uo pipefail
mkdir -p /logs/verifier

if pytest --help 2>/dev/null | grep -q -- '--ctrf-json-report'; then
  pytest /tests/test_outputs.py --ctrf-json-report --ctrf-json-report-file=/logs/verifier/ctrf.json
  status=$?
else
  pytest /tests/test_outputs.py
  status=$?
  cat > /logs/verifier/ctrf.json <<'JSON'
{"results":{"tool":{"name":"pytest"}},"summary":{"tests":0,"passed":0,"failed":0}}
JSON
fi

if [ "$status" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

exit 0
