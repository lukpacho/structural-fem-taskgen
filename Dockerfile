# Dockerfile
# ---------- Stage 0 : build image -----------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy sources and build wheel
COPY pyproject.toml requirements.txt README.md ./
COPY src/ src/

RUN pip install build && \
    python -m build --wheel --outdir /dist

# ---------- Stage 1 : runtime image --------------------------------
FROM python:3.11-slim

# system libs, gmesh deps and gosu
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        ca-certificates curl gosu \
        libfontconfig1 libgl1 libglu1-mesa libxcursor1 \
        libxft2 libxrender1 libxi6 libxrandr2 libxinerama1 \
        libgomp1 ghostscript libgraphite2-3 libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*

# --- install Tectonic
RUN set -eux; \
    url=$(curl -s https://api.github.com/repos/tectonic-typesetting/tectonic/releases/latest \
          | grep browser_download_url \
          | grep x86_64-unknown-linux-gnu.tar.gz \
          | cut -d '"' -f 4); \
    curl -L "$url" -o /tmp/tectonic.tar.gz; \
    mkdir /tmp/tectonic && \
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