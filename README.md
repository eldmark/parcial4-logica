# Simulador de Máquinas de Turing (`tm-simulator`)

Simulador de Máquinas deterministas de Turing de una cinta infinita con registro de memoria caché (`mem_cache_value`), desarrollado con Python 3.14, FastAPI y React + TypeScript.

Permite definir Máquinas de Turing en formato YAML, validar estructural y semánticamente su configuración, simular cadenas paso a paso obteniendo la secuencia completa de descripciones instantáneas (IDs) e inspeccionar visualmente el estado de la cinta y del cabezal desde una interfaz web.

> [!IMPORTANT]
> **Sobre esta copia (Lógica Matemática, parcial 4).** Este proyecto se desarrolló originalmente para el curso de **Teoría de la Computación**. Por las políticas de esa clase, el repositorio original no se puede hacer público, así que esta es una copia del proyecto con su historial de commits. El trabajo original lo hicimos los tres integrantes que aparecen abajo. En esta copia solo se cambió un poco la interfaz de usuario para que la página sea responsive (se adapta a teléfonos, tabletas y pantallas anchas) y sea más cómoda de usar. La lógica del simulador, la API y las pruebas no cambiaron.
>
> El uso de inteligencia artificial está declarado en [AI_USAGE.md](AI_USAGE.md).

## Integrantes
- Marco Alejandro Díaz Castañeda ([@eldmark](https://github.com/eldmark))
- Jackelyn Nicolle Girón Villacinda ([@gnicoool](https://github.com/gnicoool))
- Sergio Estuardo Tan Coromac ([@stan-2021131](https://github.com/stan-2021131))

### Cambios de interfaz en esta copia

- El editor YAML y el diagrama de estados se muestran lado a lado en pantallas anchas; en pantallas angostas se apilan.
- En teléfono, los botones ocupan el ancho disponible y tienen un tamaño cómodo para tocar, y el botón *Simular* ocupa toda la fila.
- Las pestañas de resultados quedan en una sola fila que se desplaza horizontalmente.
- Las celdas de la cinta son más pequeñas en teléfono, y la tabla de descripciones instantáneas se desplaza dentro de su recuadro sin romper el ancho de la página.
- Hay un encabezado con una breve descripción, sombras suaves en los paneles y un contorno visible al navegar con el teclado.

> Para consultar el detalle técnico de la arquitectura por capas, los modelos de dominio y el contrato de simulación, revisa [docs/arquitectura_y_configuracion.md](docs/arquitectura_y_configuracion.md).

## Características principales

- **Carga y validación YAML**: Lectura segura en UTF-8 (`yaml.safe_load`), normalización del símbolo blanco y validación estructural/semántica con reporte detallado de errores por ruta (`code`, `path`, `message`).
- **Motor de simulación determinista**: Ejecución sobre una cinta infinita con registro paso a paso de descripciones instantáneas (`Snapshot` / `TapeView`), estado, memoria caché y transiciones aplicadas, determinando aceptación (`accepted`), rechazo (`no_transition`) o límite de pasos (`step_limit`).
- **API REST en FastAPI**: Endpoints para ejecutar simulaciones completas por lote o cadena individual, y para consultar descripciones instantáneas por número de paso.
- **Interfaz web interactiva**: Editor YAML con selector de máquinas de ejemplo, ejecución de `simulation_strings` o entradas personalizadas, visualización de la cinta con la posición del cabezal, controles de reproducción paso a paso y tabla completa de descripciones instantáneas (IDs).
- **CLI de diagnóstico**: Validación rápida de archivos YAML desde la terminal.

## Requisitos

- **Python**: `>=3.14,<3.15`
- **Gestor de Python**: [`uv`](https://docs.astral.sh/uv/)
- **Frontend**: Node.js y `npm`
- **Docker**: (Opcional) Docker y Docker Compose para levantar todo el proyecto con un solo comando.

## Ejecución con Docker (Construcción con un comando)

Para construir y levantar todo el sistema (Backend FastAPI + Frontend React con proxy Nginx) en **un solo comando**:

```bash
docker compose up --build
```

Si únicamente deseas compilar las imágenes sin iniciar los contenedores:

```bash
docker compose build
```

- **Interfaz web**: [http://localhost:5174](http://localhost:5174)
- **Documentación Swagger UI**: [http://localhost:8001/docs](http://localhost:8001/docs) (también disponible en [http://localhost:5174/docs](http://localhost:5174/docs))

> [!NOTE]
> Los puertos se configuran por defecto en `8001` (backend) y `5174` (frontend) para evitar colisiones con otros servicios del host. Puedes ajustarlos modificando `.env` o mediante variables de entorno:
> ```bash
> BACKEND_PORT=8000 FRONTEND_PORT=5173 docker compose up --build
> ```

### Pruebas y CLI mediante Docker

```bash
# Ejecutar la suite de pruebas unitarias y reporte de cobertura dentro del contenedor
docker compose run --rm backend pytest

# Ejecutar el CLI de validación de máquinas de Turing
docker compose run --rm backend python -m tm_simulator tests/fixtures/yaml/recognizer_w_hash_w.yaml
```

## Instalación local (sin Docker)

Desde la raíz del repositorio:

```bash
# Instalar dependencias del backend y herramientas de desarrollo
uv sync --dev

# Instalar dependencias del frontend
cd frontend
npm install
cd ..
```

## Ejecución de la aplicación (API + Frontend)

Abre **dos terminales** en la raíz del proyecto:

### Terminal 1 — Backend (FastAPI + Uvicorn)

```bash
uv run uvicorn tm_simulator.api:app --reload
```

- Servidor disponible en `http://127.0.0.1:8000`
- Documentación interactiva de la API (Swagger UI) en `http://127.0.0.1:8000/docs`

### Terminal 2 — Frontend (React + Vite)

```bash
cd frontend
npm run dev
```

- Aplicación web disponible en `http://localhost:5173`
- El servidor de desarrollo de Vite redirige automáticamente las peticiones `/api` hacia `http://127.0.0.1:8000` (`frontend/vite.config.ts`).

### Ejecución del backend sin `uv` (`venv` + `pip`)

```bash
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

python -m pip install -e ".[dev]"
uvicorn tm_simulator.api:app --reload
```

## Uso del CLI de validación YAML

Para validar un archivo YAML desde la línea de comandos y obtener el resumen de la máquina configurada:

```bash
uv run python -m tm_simulator tests/fixtures/yaml/recognizer_w_hash_w.yaml
```

## Máquinas de ejemplo incluidas

En `tests/fixtures/yaml/` se incluyen configuraciones listas para cargar en el simulador (también disponibles desde el selector de ejemplos del frontend):

- **`recognizer_w_hash_w.yaml`**: Máquina reconocedora para $L = \{ w\#w \mid w \in \{a, b\}^+ \}$.
- **`alterer_complement_ab.yaml`**: Máquina alteradora que invierte los símbolos `a` ↔ `b` sobre la cinta.
- **`alterer_reverse_ab.yaml`**: Máquina alteradora que invierte el orden de una cadena sobre `{a, b}`.
- **`MTpersonalizado.yaml`** y **`valid_minimal.yaml`**: Configuraciones adicionales de ejemplo y prueba.

## Formato YAML admitido

### Estructura general

```yaml
q_states:
  q_list:
    - "0"
    - "1"
    - "2"
  initial: "0"
  final: "2"

alphabet:
  - a
  - b

tape_alphabet:
  - a
  - b
  - X
  -

delta:
  - params:
      initial_state: "0"
      mem_cache_value:
      tape_input: a
    output:
      final_state: "1"
      mem_cache_value: a
      tape_output: X
      tape_displacement: R

simulation_strings:
  - aabab
  - abbab
```

### Reglas sobre el símbolo blanco y `#`

- **Símbolo blanco (`blank`)**: Se representa internamente con `None`. En campos de símbolo de cinta o memoria (`tape_alphabet`, `mem_cache_value`, `tape_input`, `tape_output`) se reconocen como blanco: entrada YAML vacía, `null`, `~` y el texto `None` (sin distinguir mayúsculas/minúsculas). `tape_alphabet` debe incluir exactamente una representación del blanco y `alphabet` no puede contenerlo.
- **Carácter `#`**: En YAML, un `#` sin comillas inicia un comentario. Cuando `#` forme parte del alfabeto o de una transición, debe escribirse entre comillas (`"#"`).

## Endpoints de la API

- **`POST /api/v1/simulations`**: Recibe `{ yaml, input?, max_steps }` (si `input` es `null` o se omite, ejecuta todas las cadenas de `simulation_strings`). Devuelve la lista de resultados con `status` (`accepted` | `rejected` | `indeterminate`), `halt_reason`, `steps`, `final_tape`, `snapshots` (descripciones instantáneas) y `transitions`.
- **`POST /api/v1/simulations/step`**: Recibe `{ yaml, input, step, max_steps }` y calcula la descripción instantánea (`snapshot`), `halt_reason` y `transition` correspondientes al índice `step`.

## Pruebas y verificación

```bash
# Pruebas unitarias e integración con reporte de cobertura
uv run pytest

# Análisis estático con Ruff
uv run ruff check .

# Verificación de tipos y build de producción del frontend
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

## Estructura del proyecto

```text
.
├── .python-version
├── pyproject.toml
├── uv.lock
├── README.md
├── docs/
│   ├── Proyecto No 3.pdf
│   └── arquitectura_y_configuracion.md
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── examples.ts
│       ├── format.ts
│       ├── main.tsx
│       ├── styles.css
│       ├── usePlayer.ts
│       ├── api/
│       └── components/
├── src/
│   └── tm_simulator/
│       ├── __init__.py
│       ├── __main__.py
│       ├── api.py
│       ├── simulation.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── errors.py
│       │   └── models.py
│       └── configuration/
│           ├── __init__.py
│           ├── pipeline.py
│           ├── step_01_load_yaml.py
│           ├── step_02_normalize.py
│           ├── step_03_validate.py
│           └── step_04_build_machine.py
└── tests/
    ├── fixtures/yaml/
    ├── test_api.py
    ├── test_cli.py
    ├── test_configuration_pipeline.py
    ├── test_machine_builder.py
    ├── test_normalizer.py
    ├── test_simulation.py
    ├── test_validator.py
    └── test_yaml_loader.py
```
