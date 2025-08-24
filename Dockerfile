# Etapa base: Python + uv
FROM python:3.12-slim AS base

# Instalar dependencias de sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl wget gnupg ca-certificates \
    # dependencias de chromium
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libasound2 libxshmfence1 libx11-xcb1 libx11-6 libxcb1 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv (https://github.com/astral-sh/uv)
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copiar definición de dependencias
COPY pyproject.toml ./
COPY uv.lock* ./

# Instalar dependencias en un venv manejado por uv
RUN uv sync --frozen --no-cache

# Instalar navegadores de Playwright (solo chromium con sus deps)
RUN uv run playwright install --with-deps chromium

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto del servidor
EXPOSE 8000

# Comando por defecto: levantar FastAPI con uvicorn
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
