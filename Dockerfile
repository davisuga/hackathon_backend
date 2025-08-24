# Imagen base oficial de Playwright con Python
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

# Instalar uv
RUN pip install --no-cache-dir uv

# Copiar definición de dependencias
COPY pyproject.toml ./
COPY uv.lock* ./

# Instalar dependencias del proyecto
RUN uv sync --frozen --no-cache

# Copiar el resto del proyecto
COPY . .

# Exponer puerto si usas FastAPI u otro servidor
EXPOSE 8000

# Comando por defecto
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
