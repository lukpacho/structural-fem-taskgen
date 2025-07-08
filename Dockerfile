FROM python:3.11-slim
LABEL authors="lukpacho"

# --- OS deps ---------------------------------------------------------------
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-luatex \
        texlive-fonts-recommended \
        ghostscript \
        make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Python deps -----------------------------------------------------------
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# --- Copy source & expose CLI ---------------------------------------------
COPY . .
ENTRYPOINT ["python", "-m", "taskgen.cli"]