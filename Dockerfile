FROM python:3.14-slim

# Copiar el binario oficial de uv para instalación ultrarrápida de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Optimizaciones de uv y Python
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Copiar descriptores de dependencias primero para aprovechar el caché de Docker
COPY pyproject.toml uv.lock ./

# Instalar dependencias (incluyendo dev para permitir ejecutar pytest dentro del contenedor)
RUN uv sync --frozen --dev --no-install-project

# Copiar código fuente, tests y documentación
COPY src/ ./src/
COPY tests/ ./tests/
COPY README.md ./

# Sincronizar e instalar el paquete en el entorno virtual
RUN uv sync --frozen --dev

# Configurar el PATH para usar directamente el entorno virtual de uv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "tm_simulator.api:app", "--host", "0.0.0.0", "--port", "8000"]
