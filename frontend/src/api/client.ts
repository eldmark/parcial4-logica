import type { ApiError, SimulationResult, ValidationIssue } from "./types";

export class SimulationApiError extends Error {
  constructor(public readonly info: ApiError) {
    super(info.title);
  }
}

function parseDetail(status: number, detail: unknown): ApiError {
  const d = detail as Record<string, unknown> | undefined;
  switch (d?.code) {
    case "invalid_machine": {
      const issues = (d.issues as ValidationIssue[]) ?? [];
      return {
        title: `La máquina tiene ${issues.length} error(es) de validación`,
        messages: issues.map((i) => `[${i.code}] ${i.path}: ${i.message}`),
      };
    }
    case "invalid_yaml":
      return { title: "YAML inválido", messages: [String(d.message ?? "")] };
    case "invalid_input":
      return {
        title: "Cadena de entrada inválida",
        messages: [
          `Símbolos fuera del alfabeto de entrada (cadena #${Number(d.index) + 1}): ${(
            d.symbols as string[]
          ).join(", ")}`,
        ],
      };
    default:
      return { title: `Error ${status}`, messages: [JSON.stringify(detail)] };
  }
}

export async function runSimulations(
  yaml: string,
  input: string | null,
  maxSteps: number,
): Promise<SimulationResult[]> {
  let response: Response;
  try {
    response = await fetch("/api/v1/simulations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ yaml, input, max_steps: maxSteps }),
    });
  } catch {
    throw new SimulationApiError({
      title: "No se pudo conectar con la API",
      messages: ["Verifica que el backend esté corriendo en http://127.0.0.1:8000"],
    });
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    // Errores de validación de pydantic llegan como lista en `detail`.
    const detail = Array.isArray(body?.detail)
      ? { code: "request", message: JSON.stringify(body.detail) }
      : body?.detail;
    throw new SimulationApiError(parseDetail(response.status, detail));
  }
  return body.results as SimulationResult[];
}
