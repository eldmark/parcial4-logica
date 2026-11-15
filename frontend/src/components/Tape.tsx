import type { Snapshot } from "../api/types";
import { BLANK, sym } from "../format";

/** Cinta con cabezal; añade una celda en blanco de margen a cada lado. */
export function Tape({ snapshot }: { snapshot: Snapshot }) {
  const { start, cells, head } = snapshot.tape;
  const padded = [null, ...cells, null];
  const first = start - 1;

  return (
    <div className="tape-view">
      <div className="tape-status">
        <span>
          Estado: <strong>{snapshot.state}</strong>
        </span>
        <span>
          Memoria: <strong>{sym(snapshot.memory)}</strong>
        </span>
        <span>
          Paso: <strong>{snapshot.step}</strong>
        </span>
      </div>
      <div className="tape" role="list" aria-label="Cinta">
        {padded.map((cell, i) => {
          const pos = first + i;
          const isHead = pos === head;
          return (
            <div
              key={pos}
              role="listitem"
              className={`cell${isHead ? " head" : ""}${cell === null ? " blank" : ""}`}
              aria-current={isHead ? "true" : undefined}
              title={`posición ${pos}`}
            >
              <span className="pointer">{isHead ? "▼" : ""}</span>
              <span className="symbol">{cell === null ? BLANK : cell}</span>
              <span className="pos">{pos}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
