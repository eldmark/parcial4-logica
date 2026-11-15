import { useEffect, useRef } from "react";
import type { SimulationResult, Snapshot } from "../api/types";
import { describeTransition, sym } from "../format";

/** ID clásica: contenido de la cinta con el estado insertado justo antes del símbolo bajo el cabezal. */
function InstantaneousDescription({ snapshot }: { snapshot: Snapshot }) {
  const { start, cells, head } = snapshot.tape;
  const split = head - start;
  return (
    <code className="id">
      {cells.slice(0, split).map(sym).join("")}
      <b className="id-state">[{snapshot.state}]</b>
      {cells.slice(split).map(sym).join("")}
    </code>
  );
}

interface Props {
  result: SimulationResult;
  current: number;
  onSelect: (step: number) => void;
}

export function IdTable({ result, current, onSelect }: Props) {
  const currentRef = useRef<HTMLTableRowElement>(null);

  useEffect(() => {
    currentRef.current?.scrollIntoView({ block: "nearest" });
  }, [current]);

  return (
    <div className="table-wrap">
      <table className="id-table">
        <thead>
          <tr>
            <th>Paso</th>
            <th>Descripción instantánea</th>
            <th>Memoria</th>
            <th>Transición aplicada</th>
          </tr>
        </thead>
        <tbody>
          {result.snapshots.map((s, i) => (
            <tr
              key={s.step}
              ref={i === current ? currentRef : undefined}
              className={i === current ? "current" : undefined}
              onClick={() => onSelect(i)}
            >
              <td>{s.step}</td>
              <td>
                <InstantaneousDescription snapshot={s} />
              </td>
              <td>{sym(s.memory)}</td>
              <td className="muted">
                {i === 0
                  ? "— configuración inicial —"
                  : describeTransition(result.transitions[i - 1])}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
