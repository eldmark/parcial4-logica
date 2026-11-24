import { useEffect, useState } from "react";
import { fetchDiagram, runSimulations, SimulationApiError } from "./api/client";
import type { ApiError, Diagram, SimulationResult } from "./api/types";
import { ErrorPanel } from "./components/ErrorPanel";
import { ResultTabs } from "./components/ResultTabs";
import { StateDiagram } from "./components/StateDiagram";
import { YamlEditor } from "./components/YamlEditor";
import { EXAMPLES } from "./examples";

export default function App() {
  const [yaml, setYaml] = useState(EXAMPLES[0].yaml);
  const [preset, setPreset] = useState<number | null>(0);
  const [input, setInput] = useState("");
  const [maxSteps, setMaxSteps] = useState(10_000);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [results, setResults] = useState<SimulationResult[]>([]);

  const [diagram, setDiagram] = useState<Diagram | null>(null);
  const [showDiagram, setShowDiagram] = useState(true);
  const [diagramError, setDiagramError] = useState<string | null>(null);

  // Diagrama depende del yaml
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        setDiagram(await fetchDiagram(yaml, controller.signal));
        setDiagramError(null);
      } catch (e) {
        if (controller.signal.aborted) return;
        setDiagram(null);
        setDiagramError(
          e instanceof SimulationApiError
            ? [e.info.title, ...e.info.messages].join(" — ")
            : "No se pudo generar el diagrama.",
        );
      }
    }, 400);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [yaml]);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      // Cadena vacía en el campo = ejecutar todas las simulation_strings del YAML.
      setResults(await runSimulations(yaml, input === "" ? null : input, maxSteps));
    } catch (e) {
      setResults([]);
      setError(
        e instanceof SimulationApiError
          ? e.info
          : { title: "Error inesperado", messages: [String(e)] },
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app">
      <header className="app-header">
        <h1>Simulador de Máquinas de Turing</h1>
        <p className="muted">
          Máquina determinista de una cinta con memoria caché. Elige un ejemplo o escribe tu YAML,
          simula y recorre la ejecución paso a paso.
        </p>
      </header>
      <div className="workspace">
      <YamlEditor
        yaml={yaml}
        input={input}
        maxSteps={maxSteps}
        loading={loading}
        preset={preset}
        onPreset={setPreset}
        onYaml={setYaml}
        onInput={setInput}
        onMaxSteps={setMaxSteps}
        onRun={run}
      />
      <section className="panel diagram-panel">
        <div className="panel-header">
          <h2>Diagrama de estados</h2>
          <button type="button" aria-expanded={showDiagram} onClick={() => setShowDiagram((v) => !v)}>
            {showDiagram ? "Ocultar diagrama" : "Mostrar diagrama"}
          </button>
        </div>
        {showDiagram && diagram && <StateDiagram diagram={diagram} highlight={null} />}
        {showDiagram && diagramError && (
          <p className="muted">No se puede dibujar el diagrama: {diagramError}</p>
        )}
        {showDiagram && diagram && (
          <p className="muted">
            Transiciones: <code>leído.caché → escrito,movimiento.caché</code> (␣ = blank). Doble
            círculo = estado final
          </p>
        )}
      </section>
      </div>
      {error && <ErrorPanel error={error} />}
      {results.length > 0 && <ResultTabs results={results} diagram={diagram} />}
    </main>
  );
}
