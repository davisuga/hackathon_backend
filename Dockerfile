# Etapa base: Python + uv
FROM python:3.12-slim AS base

# Instalar dependencias del sistema necesarias (ejemplo: libpq-dev si usas Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv (https://github.com/astral-sh/uv)
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copiar definición de dependencias
COPY pyproject.toml ./
COPY uv.lock* ./

# Instalar dependencias en un venv manejado por uv
RUN uv sync --frozen --no-cache

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto del servidor
EXPOSE 8000

# Comando por defecto: levantar FastAPI con uvicorn
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
