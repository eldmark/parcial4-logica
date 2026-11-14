import type { ApiError } from "../api/types";

export function ErrorPanel({ error }: { error: ApiError }) {
  return (
    <div className="error-panel" role="alert">
      <strong>{error.title}</strong>
      <ul>
        {error.messages.map((m, i) => (
          <li key={i}>{m}</li>
        ))}
      </ul>
    </div>
  );
}
