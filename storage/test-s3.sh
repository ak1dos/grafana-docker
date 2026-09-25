#!/bin/sh
# Synthetic objects only. Execute against the isolated smoke deployment.
set -eu
umask 077
export RC_HOST_admin="http://${RUSTFS_ACCESS_KEY}:${RUSTFS_SECRET_KEY}@${S3_ENDPOINT}"
export RC_HOST_app="http://${S3_ACCESS_KEY}:${S3_SECRET_KEY}@${S3_ENDPOINT}"
probe="smoke-$(date +%s)-$$"
printf 'rustfs-roundtrip\n' | rc pipe "app/loki/$probe" >/dev/null
[ "$(rc cat "app/loki/$probe")" = rustfs-roundtrip ]
rc stat "app/loki/$probe" >/dev/null
rc rm "app/loki/$probe" >/dev/null
if rc stat "app/loki/$probe" >/dev/null 2>&1; then echo 'Delete failed' >&2; exit 1; fi
rc bucket create "admin/$probe" >/dev/null
printf 'private\n' | rc pipe "admin/$probe/object" >/dev/null
if rc cat "app/$probe/object" >/dev/null 2>&1; then echo 'Bucket isolation failed' >&2; exit 1; fi
rc rm "admin/$probe/object" >/dev/null
rc rb "admin/$probe" >/dev/null
printf 'PASS: S3 PUT/GET/HEAD/DELETE and cross-bucket access denied\n'
