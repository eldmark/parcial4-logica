import { useState } from "react";
import type { SimulationResult } from "../api/types";
import { usePlayer } from "../usePlayer";
import { Controls } from "./Controls";
import { IdTable } from "./IdTable";
import { ResultBadge } from "./ResultBadge";
import { Tape } from "./Tape";

function ResultView({ result }: { result: SimulationResult }) {
  const player = usePlayer(result.snapshots.length);
  return (
    <div className="result-view">
      <ResultBadge result={result} />
      <Tape snapshot={result.snapshots[player.index]} />
      <Controls player={player} />
      <IdTable result={result} current={player.index} onSelect={player.setIndex} />
    </div>
  );
}

export function ResultTabs({ results }: { results: SimulationResult[] }) {
  const [selected, setSelected] = useState(0);
  const active = Math.min(selected, results.length - 1);

  return (
    <section className="panel">
      <h2>Resultados</h2>
      <div className="tabs" role="tablist">
        {results.map((r, i) => (
          <button
            key={i}
            type="button"
            role="tab"
            aria-selected={i === active}
            className={`tab ${r.status}${i === active ? " active" : ""}`}
            onClick={() => setSelected(i)}
          >
            {r.input === "" ? "ε (vacía)" : r.input}
          </button>
        ))}
      </div>
      {/* key: reinicia el reproductor al cambiar de cadena o de ejecución */}
      <ResultView key={`${active}:${results[active].input}`} result={results[active]} />
    </section>
  );
}
