#!/bin/sh
set -eu
# The parent bind proves that the expected ZFS dataset is mounted, not an SSD fallback.
awk '$5 == "/das" && / - zfs tank\/observability / { found=1 } END { exit !found }' /proc/self/mountinfo || {
  echo 'Refusing RustFS startup: tank/observability is not mounted on /das' >&2
  exit 1
}
exec /entrypoint.sh rustfs
