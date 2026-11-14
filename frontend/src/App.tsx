import { useState } from "react";
import { runSimulations, SimulationApiError } from "./api/client";
import type { ApiError, SimulationResult } from "./api/types";
import { ErrorPanel } from "./components/ErrorPanel";
import { ResultTabs } from "./components/ResultTabs";
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
      <h1>Simulador de Máquinas de Turing</h1>
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
      {error && <ErrorPanel error={error} />}
      {results.length > 0 && <ResultTabs results={results} />}
    </main>
  );
}
