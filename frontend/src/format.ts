import type { AppliedTransition } from "./api/types";

export const BLANK = "␣";

export const sym = (s: string | null): string => (s === null ? BLANK : s);

export function describeTransition(t: AppliedTransition): string {
  const { key, effect } = t;
  return (
    `δ([${key.state}, ${sym(key.memory_value)}], ${sym(key.read_symbol)}) = ` +
    `([${effect.next_state}, ${sym(effect.next_memory_value)}], ` +
    `${sym(effect.write_symbol)}, ${effect.movement})`
  );
}
