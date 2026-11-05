#!/usr/bin/env bash
# Shared by GitHub Actions and Snapstead's disposable installed-snap test VM.
set -euo pipefail
mkdir -p artifacts
timeout 30 snap run piqueserver --version | tee artifacts/snap-version.log
python3 - <<'PY'
from pathlib import Path
import re

recipe = Path('snap/snapcraft.yaml').read_text()
expected = re.search(r"(?m)^version: '([^']+)'$", recipe).group(1)
reported = Path('artifacts/snap-version.log').read_text().strip()
assert reported == 'piqueserver ' + expected, (expected, reported)
PY
sudo -n snap restart piqueserver.piqueserver
sleep 10
sudo -n snap services piqueserver | tee artifacts/snap-services.log
sudo -n snap logs -n=100 piqueserver.piqueserver | tee artifacts/snap-service.log
test -f /var/snap/piqueserver/common/config.toml
grep -q 'Config: /var/snap/piqueserver/common/config.toml' artifacts/snap-service.log
awk 'NR > 1 && $1 == "piqueserver.piqueserver" && $3 == "active" { found = 1 } END { exit found ? 0 : 1 }' artifacts/snap-services.log
