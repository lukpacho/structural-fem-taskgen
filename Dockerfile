# ---------- Stage 0 : build image -----------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# ----- 1️⃣ OS layer: TeX only --------------------------------------
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-luatex \
        texlive-fonts-recommended \
        ghostscript \
        make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ----- 2️⃣ Python deps ---------------------------------------------
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# ----- 3️⃣ Project source ------------------------------------------
COPY . .

# ---------- Stage 1 : runtime image --------------------------------
FROM python:3.11-slim

# copy the virtual-env from the builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app .

ENTRYPOINT ["python", "-m", "taskgen.cli"]