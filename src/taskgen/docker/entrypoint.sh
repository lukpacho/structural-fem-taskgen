#!/usr/bin/env bash
# entrypoint.sh

set -euo pipefail

OUT_DIR=/out
HOST_UID=${HOST_UID:-1000}
HOST_GID=${HOST_GID:-1000}

# ── 0.  Decide whether we really need /out directory ───────────────────────
cmd=${2:-}            # identify the first meaningful flag/sub-command
if [[ "$cmd" == "--out-root" || "$cmd" == "-o" ]]; then
    cmd=${4:-}
fi

case "$cmd" in
  # Pure information request -> skip all the /out logic
  ""|--help|-h|--version|-V)  exec "$@" ;;
  # The regular generation of PDFs, hence, /out needed and we need to fall through
  beam|plane2d)  ;;
  # Any other sub-command skips /out handling by default
  *)  exec "$@" ;;
esac

# From here on we *require* that /out exists and is writable
if [ ! -d "$OUT_DIR" ]; then
    echo "[entrypoint] error: /out is missing."
    echo "           run the container with:   -v \"\$PWD/out:/out\""
    exit 1
fi

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
