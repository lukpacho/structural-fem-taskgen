#!/usr/bin/env bash
# entrypoint.sh
set -euo pipefail

# defaults
OUT_DIR=${OUT_DIR:-/out}
HOST_UID=${HOST_UID:-1000}
HOST_GID=${HOST_GID:-1000}

# 0. Skip /out handling for read-only commands
case "$1" in
  ""|--help|-h|--version|-V) exec taskgen "$@";;
esac

# 1. Ensure /out is present & owned by caller
if [[ ! -d "$OUT_DIR" ]]; then
  echo "[taskgen] creating $OUT_DIR"
  mkdir -p "$OUT_DIR"
fi

cur_uid=$(stat -c %u "${OUT_DIR}" || echo 0)
cur_gid=$(stat -c %g "${OUT_DIR}" || echo 0)

if [[ $cur_uid == 0 && $cur_gid == 0 ]]; then
    echo "[taskgen] Adopting ${OUT_DIR} for UID:GID ${HOST_UID}:${HOST_GID}"
    chown -R "${HOST_UID}:${HOST_GID}" "${OUT_DIR}" || true
    cur_uid=$HOST_UID; cur_gid=$HOST_GID
fi

# 2. Create matching user/group inside container (if needed)
getent group  "$cur_gid" >/dev/null 2>&1 || addgroup --gid "$cur_gid" hostgrp
getent passwd "$cur_uid" >/dev/null 2>&1 || \
    adduser --uid "$cur_uid" --gid "$cur_gid" --disabled-password --gecos "" hostusr

# 3. Point taskgen and tectonic at the writable cache
CACHE_ROOT="$OUT_DIR/.taskgen-cache"
mkdir -p "$CACHE_ROOT"

# 3.1 Create task sub-folders and give them to the caller
for sub in temp pdfs results; do
  mkdir -p "$OUT_DIR/$sub"
done
chown -R "$cur_uid:$cur_gid" "$OUT_DIR"

export TASKGEN_CACHE_DIR="$CACHE_ROOT"

# 4. Inject --out-root /out unless user already set one
ARGS=("$@")
for a in "${ARGS[@]}"; do
  [[ "$a" == "--out-root" || "$a" == "-o" ]] && FOUND=yes && break
done
if [[ -z ${FOUND:-} ]]; then
  ARGS=(--out-root "$OUT_DIR" "${ARGS[@]}")
fi

# 5. Drop privileges and run the command
echo "[taskgen] Running as UID:GID ${cur_uid}:${cur_gid}: taskgen ${ARGS[*]}"
exec gosu "${cur_uid}:${cur_gid}" taskgen "${ARGS[@]}"
