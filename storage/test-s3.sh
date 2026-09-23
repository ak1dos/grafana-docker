#!/bin/sh
# Synthetic objects only. Execute against the isolated smoke deployment.
set -eu
export MC_HOST_admin="http://${RUSTFS_ACCESS_KEY}:${RUSTFS_SECRET_KEY}@${S3_ENDPOINT}"
export MC_HOST_app="http://${S3_ACCESS_KEY}:${S3_SECRET_KEY}@${S3_ENDPOINT}"
probe="smoke-$(date +%s)-$$"
printf 'rustfs-roundtrip\n' | mc pipe "app/loki/$probe" >/dev/null
[ "$(mc cat "app/loki/$probe")" = rustfs-roundtrip ]
mc stat "app/loki/$probe" >/dev/null
mc rm "app/loki/$probe" >/dev/null
if mc stat "app/loki/$probe" >/dev/null 2>&1; then echo 'Delete failed' >&2; exit 1; fi
mc mb "admin/$probe" >/dev/null
printf 'private\n' | mc pipe "admin/$probe/object" >/dev/null
if mc cat "app/$probe/object" >/dev/null 2>&1; then echo 'Bucket isolation failed' >&2; exit 1; fi
mc rm "admin/$probe/object" >/dev/null
mc rb "admin/$probe" >/dev/null
printf 'PASS: S3 PUT/GET/HEAD/DELETE and cross-bucket access denied\n'
