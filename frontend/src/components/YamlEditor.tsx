import { useRef } from "react";
import { EXAMPLES } from "../examples";
// Plantilla que se escribe en el editor al elegir «Personalizado» (MT funcional de ejemplo).
import FORMAT_TEMPLATE from "../../../tests/fixtures/yaml/MTpersonalizado.yaml?raw";

interface Props {
  yaml: string;
  input: string;
  maxSteps: number;
  loading: boolean;
  /** Índice del ejemplo predefinido seleccionado; null = YAML personalizado (editable). */
  preset: number | null;
  onPreset: (i: number | null) => void;
  onYaml: (v: string) => void;
  onInput: (v: string) => void;
  onMaxSteps: (v: number) => void;
  onRun: () => void;
}

export function YamlEditor(p: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  const onFile = async (file: File | undefined) => {
    if (file) {
      p.onYaml(await file.text());
      p.onPreset(null);
    }
    if (fileRef.current) fileRef.current.value = "";
  };

  const readOnly = p.preset !== null;

  return (
    <section className="panel editor">
      <h2>Definición de la máquina (YAML)</h2>
      <div className="row presets">
        {EXAMPLES.map((e, i) => (
          <button
            key={e.label}
            type="button"
            aria-pressed={p.preset === i}
            className={p.preset === i ? "selected" : undefined}
            onClick={() => {
              p.onYaml(e.yaml);
              p.onPreset(i);
            }}
          >
            {e.label}
          </button>
        ))}
        <button
          type="button"
          aria-pressed={!readOnly}
          className={!readOnly ? "selected" : undefined}
          disabled={!readOnly}
          onClick={() => {
            p.onYaml(FORMAT_TEMPLATE);
            p.onPreset(null);
          }}
        >
          Personalizado
        </button>
        <button type="button" onClick={() => fileRef.current?.click()}>
          Subir archivo…
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".yaml,.yml,text/yaml"
          hidden
          onChange={(e) => onFile(e.target.files?.[0])}
        />
      </div>
      <textarea
        value={p.yaml}
        onChange={(e) => p.onYaml(e.target.value)}
        readOnly={readOnly}
        spellCheck={false}
        aria-label="Definición YAML"
      />
      <div className="row run-row">
        <label className="grow">
          Cadena (vacío = todas las del YAML)
          <input
            value={p.input}
            placeholder="Escribir cadena"
            onChange={(e) => p.onInput(e.target.value)}
          />
        </label>
        <label>
          max_steps
          <input
            type="number"
            min={1}
            max={10000}
            value={p.maxSteps}
            onChange={(e) => p.onMaxSteps(Number(e.target.value))}
          />
        </label>
        <button
          type="button"
          className="primary"
          disabled={p.loading || !p.yaml.trim()}
          onClick={p.onRun}
        >
          {p.loading ? "Simulando…" : "Simular"}
        </button>
      </div>
    </section>
  );
}
