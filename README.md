# Simulador de Máquinas de Turing (`tm-simulator`)

Simulador de Máquinas deterministas de Turing de una cinta con registro de memoria caché.

## Integrantes

- Marco Alejandro Díaz Castañeda
- Sergio Estuardo Tan Coromac
- Jackelyn Nicolle Girón Villacinda


## Funcionalidades implementadas

- **Parsing de la configuración**: lee el YAML de la MT (estados, estado inicial y final, alfabetos, funciones de transición y cadenas a simular), lo valida y construye una definición inmutable de la máquina.
- **Parsing de la entrada**: cada cadena se valida contra el alfabeto de entrada antes de colocarse en la cinta.
- **Simulación de MT de una cinta**: cinta infinita en ambos sentidos y registro de memoria, ejecutada con las funciones de transición del YAML.
- **Descripciones instantáneas (IDs)**: listado completo de IDs por cada cadena, visible en el frontend paso a paso.
- **Aceptación y rechazo**: la cadena es aceptada al llegar al estado final y rechazada si no existe una transición aplicable. Si se alcanza el límite de pasos, el resultado es indeterminado.
- **Máquinas de ejemplo**: una reconocedora (`w#w`) y una alteradora (complemento `a↔b`) con sus cadenas de prueba.
- **Interfaces**: CLI de validación, API HTTP y frontend web.
- **Pruebas automatizadas** con `pytest`.

## Requisitos

- **Python**: `>=3.14,<3.15`
- **Gestor de proyecto y dependencias**: [`uv`](https://docs.astral.sh/uv/)

## Instalación y uso con `uv`

### 1. Instalar dependencias

```bash
uv sync --dev
```

### 2. Ejecutar el CLI validador de YAML

Puedes validar cualquier archivo de configuración YAML y ver el resumen de la Máquina de Turing:

```bash
# Validar la máquina mínima de prueba
uv run python -m tm_simulator tests/fixtures/yaml/valid_minimal.yaml

# Validar la máquina reconocedora L = { w#w | w in {a,b}+ }
uv run python -m tm_simulator tests/fixtures/yaml/recognizer_w_hash_w.yaml

# Probar el reporte de errores con un archivo inválido
uv run python -m tm_simulator tests/fixtures/yaml/invalid_semantic.yaml
```

### 3. Ejecutar pruebas y verificar cobertura

```bash
uv run pytest
```

### 4. Servir la API para el frontend

```bash
uv run uvicorn tm_simulator.api:app --reload
```

El contrato OpenAPI está en `http://127.0.0.1:8000/openapi.json` y la documentación interactiva en `/docs`.

`POST /api/v1/simulations` recibe `{ "yaml": "...", "input": "aab#aab", "max_steps": 10000 }`. Si se omite `input`, ejecuta todas las `simulation_strings` del YAML. La cadena vacía se envía como `"input": ""`. Devuelve `results`, cada uno con `status` (`accepted`, `rejected`, `indeterminate`), `halt_reason` (`accepted`, `no_transition`, `step_limit`), `steps`, `final_tape`, `snapshots` y `transitions`.

`POST /api/v1/simulations/step` recibe los mismos campos más `step` (índice desde cero) y exige `input`. Devuelve `snapshot`, `transition` (la transición que llevó a esa ID, o `null` en el paso cero) y `halt_reason` si ya se detuvo. Un paso posterior a la detención responde 404. YAML o entrada inválida responden 422. Cada cinta se representa con `start`, `cells` (el blanco es `null`) y `head`; el índice real de `cells[i]` es `start + i`.

El límite `max_steps` evita ejecuciones sin fin. Al alcanzarlo, el resultado es `indeterminate`, ya que no prueba aceptación ni rechazo. Para un ejemplo, use `tests/fixtures/yaml/recognizer_w_hash_w.yaml` o `tests/fixtures/yaml/alterer_complement_ab.yaml`.

### 5. Ejecutar el frontend

Requiere [Node.js](https://nodejs.org/) y el backend corriendo (paso 4). En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre la URL que muestre Vite (normalmente `http://localhost:5173`). Elige un ejemplo, escribe tu propio YAML en **Personalizado** o sube un archivo, y pulsa **Simular**. Si dejas la cadena vacía se simulan todas las `simulation_strings` del YAML.

### 6. Análisis estático y formato con Ruff

```bash
uv run ruff check .
uv run ruff format --check .
```

## Instalación y ejecución sin `uv` (entorno virtual estándar)

Si prefieres usar `venv` y `pip` directamente con Python 3.14:

```bash
# 1. Crear el entorno virtual
python -m venv .venv

# 2. Activar el entorno virtual
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Linux / macOS:
source .venv/bin/activate

# 3. Instalar el paquete en modo editable junto con dependencias de desarrollo
python -m pip install -e ".[dev]"

# 4. Ejecutar el validador CLI
python -m tm_simulator tests/fixtures/yaml/valid_minimal.yaml

# 5. Ejecutar pruebas
pytest
```

## Explicación del pipeline de configuración

El módulo `tm_simulator.configuration` procesa las definiciones en cuatro etapas internas:

```text
Archivo o texto YAML
        ↓
step_01_load_yaml      → Carga segura con yaml.safe_load y codificación UTF-8
        ↓
step_02_normalize      → Normalización controlada del símbolo blanco a None
        ↓
step_03_validate       → Validación estructural y semántica con recolección de errores
        ↓
step_04_build_machine  → Construcción de MachineDefinition inmutable
```

## Árbol del proyecto

```text
.
├── .python-version
├── pyproject.toml
├── uv.lock
├── README.md
├── docs/
│   ├── Proyecto No 3.pdf
│   └── arquitectura_y_configuracion.md
├── src/
│   └── tm_simulator/
│       ├── __init__.py
│       ├── __main__.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── errors.py
│       ├── simulation.py
│       ├── api.py
│       └── configuration/
│           ├── __init__.py
│           ├── pipeline.py
│           ├── step_01_load_yaml.py
│           ├── step_02_normalize.py
│           ├── step_03_validate.py
│           └── step_04_build_machine.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── api/                  # tipos y cliente HTTP
│       ├── components/           # editor, cinta, controles, tabla de IDs, resultados
│       ├── examples.ts
│       ├── format.ts
│       └── usePlayer.ts          # reproducción paso a paso
└── tests/
    ├── fixtures/
    │   └── yaml/
    │       ├── invalid_empty.yaml
    │       ├── invalid_semantic.yaml
    │       ├── invalid_syntax.yaml
    │       ├── MTpersonalizado.yaml
    │       ├── alterer_complement_ab.yaml
    │       ├── recognizer_w_hash_w.yaml
    │       └── valid_minimal.yaml
    ├── test_cli.py
    ├── test_configuration_pipeline.py
    ├── test_machine_builder.py
    ├── test_normalizer.py
    ├── test_validator.py
    └── test_yaml_loader.py
```

## Formato YAML admitido y símbolo blanco

### Representación del símbolo blanco (`blank`)
Internamente el símbolo blanco se representa con `None`. Durante la normalización se reconocen como blanco únicamente en campos de símbolo de cinta o memoria (`tape_alphabet`, `mem_cache_value`, `tape_input`, `tape_output`):
- Un valor YAML vacío (ej. `-` en `tape_alphabet` o `mem_cache_value:` sin valor).
- `null`.
- `~`.
- El texto `None` (sin distinguir mayúsculas y minúsculas).

`tape_alphabet` debe incluir **exactamente una** representación del blanco, y `alphabet` (alfabeto de entrada) no puede contener el blanco.

### Nota sobre el carácter `#`
En YAML, un carácter `#` sin comillas inicia un comentario y es descartado por el parser. Para utilizar `#` como símbolo de entrada o de cinta, debe escribirse siempre entre comillas: `"#"`.

### Ejemplo mínimo válido

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
  - params:
      initial_state: "1"
      mem_cache_value: a
      tape_input: b
    output:
      final_state: "2"
      mem_cache_value:
      tape_output: X
      tape_displacement: S

simulation_strings:
  - ab
  - aab
```

## API pública

El paquete `tm_simulator.configuration` expone dos funciones públicas que devuelven una `MachineDefinition` inmutable:

- `load_machine_from_file(path: str | Path) -> MachineDefinition`
- `load_machine_from_text(content: str) -> MachineDefinition`

### Ejemplo de uso en Python

```python
from tm_simulator.configuration import load_machine_from_file

machine = load_machine_from_file("tests/fixtures/yaml/valid_minimal.yaml")
print(machine.states)  # frozenset({'0', '1', '2'})
print(machine.initial_state)  # '0'
print(machine.final_state)  # '2'
print(machine.simulation_strings)  # ('ab', 'aab')
```

