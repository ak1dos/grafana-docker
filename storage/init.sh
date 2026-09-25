#!/bin/sh
# One-shot bucket/IAM setup. No secret values are printed.
set -eu
umask 077
export RC_HOST_admin="http://${RUSTFS_ACCESS_KEY}:${RUSTFS_SECRET_KEY}@${S3_ENDPOINT}"
export RC_HOST_loki="http://${S3_ACCESS_KEY}:${S3_SECRET_KEY}@${S3_ENDPOINT}"
ready=false
for attempt in $(seq 1 60); do
  if rc ls admin >/dev/null 2>&1; then ready=true; break; fi
  sleep 2
done
[ "$ready" = true ] || { echo 'RustFS did not become ready' >&2; exit 1; }
rc bucket create --ignore-existing admin/loki >/dev/null
if ! rc admin user info admin "$S3_ACCESS_KEY" >/dev/null 2>&1; then
  rc admin user add admin "$S3_ACCESS_KEY" "$S3_SECRET_KEY" >/dev/null
fi
rc admin policy create admin homelab-loki /bootstrap/loki-policy.json >/dev/null
rc admin policy attach admin homelab-loki --user "$S3_ACCESS_KEY" >/dev/null
rc ls loki/loki >/dev/null
printf 'RustFS bucket and scoped Loki account ready.\n'
