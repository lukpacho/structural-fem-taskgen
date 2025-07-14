# ---------- Stage 0 : build image -----------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# 1. OS layer – TeX
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-luatex \
        texlive-fonts-recommended \
        ghostscript \
        make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Copy sources and build wheel
COPY pyproject.toml requirements.txt README.md ./
COPY src/ src/

RUN pip install build && \
    python -m build --wheel --outdir /dist

# ---------- Stage 1 : runtime image --------------------------------
FROM python:3.11-slim

# 1. Install the wheel produced in stage 0
COPY --from=builder /dist/*.whl /tmp/
RUN pip install /tmp/*.whl && rm -rf /tmp/*.whl

# 2. TeX & gmesh runtime deps
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-luatex \
        texlive-fonts-recommended \
        ghostscript \
        libgl1 \
        libglu1-mesa && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Entrypoint
ENTRYPOINT ["taskgen"]
CMD ["--help"]