FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --frozen --no-install-project

COPY src/ ./src/
COPY config.yaml ./

RUN uv sync --frozen

CMD ["uv", "run", "nijimarutto-monitor"]
