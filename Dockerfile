# Dockerfile
# ---------- Stage 0 : build image -----------------------------------
FROM python:3.12-slim AS builder
WORKDIR /build

# Copy only metadata first
COPY pyproject.toml README.md LICENSE ./

# Install build tooling
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip \
    && pip install --upgrade build hatchling

# Copy the actual sources
COPY src/ src/

# Build wheel and install it into a temporary venv
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m build --wheel -o /tmp/dist \
 && pip install /tmp/dist/*.whl \
 && rm -rf /tmp/dist


# ---------- Stage 1 : runtime image --------------------------------
FROM python:3.12-slim

# Install system libs, gmesh deps and gosu
RUN set -eux; \
    apt-get update -y; \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        ca-certificates curl gosu adduser \
        libfontconfig1 libgl1 libglu1-mesa libxcursor1 \
        libxft2 libxrender1 libxi6 libxrandr2 libxinerama1 \
        libgomp1 ghostscript libgraphite2-3 libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic
ARG TECTONIC_SHA256="875fbbc9ab48560d7776088c608e0beee49197b57ab4a2f6c5385b2c661c842f"
RUN set -eux; \
    curl -L -o /tmp/tectonic.tar.gz \
      "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz"; \
    echo "${TECTONIC_SHA256}  /tmp/tectonic.tar.gz" | sha256sum -c -; \
    mkdir /tmp/tectonic; \
    tar -xzf /tmp/tectonic.tar.gz -C /tmp/tectonic; \
    install -m 0755 /tmp/tectonic/tectonic /usr/local/bin/; \
    rm -rf /tmp/tectonic /tmp/tectonic.tar.gz

# Copy wheel from builder stage
COPY --from=builder /usr/local /usr/local

# head-less matplotlib
ENV MPLBACKEND=Agg

# Entrypoint
COPY src/taskgen/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
CMD ["--help"]