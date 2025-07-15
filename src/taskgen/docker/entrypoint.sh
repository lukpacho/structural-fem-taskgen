#!/usr/bin/env bash
# entrypoint.sh

set -euo pipefail

OUT_DIR=/out
HOST_UID=${HOST_UID:-1000}
HOST_GID=${HOST_GID:-1000}

# ── 1. make /out writable by the caller ───────────────────────────────────
cur_uid=$(stat -c %u "${OUT_DIR}" || echo 0)
cur_gid=$(stat -c %g "${OUT_DIR}" || echo 0)

if [[ $cur_uid == 0 && $cur_gid == 0 ]]; then
    echo "[entrypoint] Adopting ${OUT_DIR} for UID:GID ${HOST_UID}:${HOST_GID}"
    chown -R "${HOST_UID}:${HOST_GID}" "${OUT_DIR}" || true
    cur_uid=$HOST_UID; cur_gid=$HOST_GID
fi

# ── 2. ensure those ids exist inside the container ────────────────────────
getent group  "$cur_gid" >/dev/null 2>&1 || addgroup --gid "$cur_gid" hostgrp
getent passwd "$cur_uid" >/dev/null 2>&1 || \
    adduser --uid "$cur_uid" --gid "$cur_gid" --disabled-password --gecos "" hostusr

# ── 3. point both taskgen *and* tectonic at the writable cache ────────────
CACHE_ROOT="${OUT_DIR}/.taskgen-cache"
mkdir -p "${CACHE_ROOT}"
chown -R "${cur_uid}:${cur_gid}" "${CACHE_ROOT}"

# ── 4. drop privileges and run the command ────────────────────────────────
echo "[entrypoint] Running as UID:GID ${cur_uid}:${cur_gid}: $*"
exec gosu "${cur_uid}:${cur_gid}" "$@"
