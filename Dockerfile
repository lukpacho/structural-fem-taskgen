# Dockerfile
# ---------- Stage 0 : build image -----------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy sources and build wheel
COPY pyproject.toml LICENSE README.md ./
COPY src/ src/

RUN pip install --no-cache-dir build \
  && python -m build --wheel --outdir /dist

# ---------- Stage 1 : runtime image --------------------------------
FROM python:3.11-slim

# --- system libs, gmesh deps and gosu
RUN set -eux; \
    apt-get update -y; \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        ca-certificates curl gosu adduser \
        libfontconfig1 libgl1 libglu1-mesa libxcursor1 \
        libxft2 libxrender1 libxi6 libxrandr2 libxinerama1 \
        libgomp1 ghostscript libgraphite2-3 libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*

# --- install Tectonic
ARG TECTONIC_SHA256="875fbbc9ab48560d7776088c608e0beee49197b57ab4a2f6c5385b2c661c842f"
RUN set -eux; \
    curl -L -o /tmp/tectonic.tar.gz \
      "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz"; \
    echo "${TECTONIC_SHA256}  /tmp/tectonic.tar.gz" | sha256sum -c -; \
    mkdir /tmp/tectonic; \
    tar -xzf /tmp/tectonic.tar.gz -C /tmp/tectonic; \
    install -m 0755 /tmp/tectonic/tectonic /usr/local/bin/; \
    rm -rf /tmp/tectonic /tmp/tectonic.tar.gz

# --- install wheel
COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

# head-less matplotlib
ENV MPLBACKEND=Agg

# 3. Entrypoint
COPY src/taskgen/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh", "taskgen"]
CMD ["--help"]