import { useState } from "react";
import type { Diagram, Highlight, SimulationResult } from "../api/types";
import { usePlayer } from "../usePlayer";
import { Controls } from "./Controls";
import { IdTable } from "./IdTable";
import { ResultBadge } from "./ResultBadge";
import { StateDiagram } from "./StateDiagram";
import { Tape } from "./Tape";

function ResultView({ result, diagram }: { result: SimulationResult; diagram: Diagram | null }) {
  const player = usePlayer(result.snapshots.length);
  // El paso i llega al estado snapshots[i] aplicando transitions[i - 1].
  const highlight: Highlight = {
    state: result.snapshots[player.index].state,
    transition: player.index > 0 ? result.transitions[player.index - 1] : null,
  };
  return (
    <div className="result-layout">
      <div className="result-view">
        <ResultBadge result={result} />
        <Tape snapshot={result.snapshots[player.index]} />
        <Controls player={player} />
        <IdTable result={result} current={player.index} onSelect={player.setIndex} />
      </div>
      {diagram && (
        <aside className="result-diagram">
          <StateDiagram diagram={diagram} highlight={highlight} />
        </aside>
      )}
    </div>
  );
}

export function ResultTabs({
  results,
  diagram,
}: {
  results: SimulationResult[];
  diagram: Diagram | null;
}) {
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
      <ResultView
        key={`${active}:${results[active].input}`}
        result={results[active]}
        diagram={diagram}
      />
    </section>
  );
}
