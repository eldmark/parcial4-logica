// Tipos espejo de los schemas de src/tm_simulator/api.py.
export type Movement = "L" | "R" | "S";
export type Status = "accepted" | "rejected" | "indeterminate";
export type HaltReason = "accepted" | "no_transition" | "step_limit";

export interface Tape {
  start: number;
  cells: (string | null)[]; // null = blanco; índice real de cells[i] = start + i
  head: number;
}

export interface Snapshot {
  step: number;
  state: string;
  memory: string | null;
  tape: Tape;
}

export interface AppliedTransition {
  step: number;
  key: { state: string; memory_value: string | null; read_symbol: string | null };
  effect: {
    next_state: string;
    next_memory_value: string | null;
    write_symbol: string | null;
    movement: Movement;
  };
}

export interface SimulationResult {
  input: string;
  status: Status;
  halt_reason: HaltReason;
  steps: number;
  final_tape: Tape;
  snapshots: Snapshot[];
  transitions: AppliedTransition[];
}

export interface ValidationIssue {
  code: string;
  path: string;
  message: string;
}

export interface ApiError {
  title: string;
  messages: string[];
}
