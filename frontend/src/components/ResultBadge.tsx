import type { SimulationResult } from "../api/types";

const LABELS: Record<SimulationResult["status"], string> = {
  accepted: "Aceptada",
  rejected: "Rechazada",
  indeterminate: "Indeterminada",
};

const REASONS: Record<SimulationResult["halt_reason"], string> = {
  accepted: "se alcanzó el estado final",
  no_transition: "no existe transición aplicable",
  step_limit: "se alcanzó el límite de pasos",
  loop: "bucle infinito: una configuración se repitió",
};

export function ResultBadge({ result }: { result: SimulationResult }) {
  return (
    <div className="result-line">
      <span className={`badge ${result.status}`}>{LABELS[result.status]}</span>
      <span className="muted">
        {REASONS[result.halt_reason]} · {result.steps} paso(s)
      </span>
    </div>
  );
}
