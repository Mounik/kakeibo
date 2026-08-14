#!/bin/bash
set -euo pipefail

python -c "
import sys, urllib.request
try:
    urllib.request.urlopen('http://127.0.0.1:5000/api/ping', timeout=5)
    print('App: OK')
except Exception as e:
    print(f'App: FAILED - {e}')
    sys.exit(1)
"
