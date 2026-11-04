FROM ghcr.io/astral-sh/uv:0.12.19 AS uv
FROM python:3.12.14-slim
COPY --from=uv /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEMO_DATA_DIR=/data
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY . .
EXPOSE 8000
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
