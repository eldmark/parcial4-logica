import type { Diagram, DiagramEdge, Highlight } from "../api/types";
import { sym } from "../format";

const NODE_R = 24;
const LINE_H = 13;

interface Point {
  x: number;
  y: number;
}

interface Group {
  source: string;
  target: string;
  edges: DiagramEdge[];
}

const add = (a: Point, b: Point): Point => ({ x: a.x + b.x, y: a.y + b.y });
const scale = (a: Point, k: number): Point => ({ x: a.x * k, y: a.y * k });
const unit = (a: Point): Point => {
  const len = Math.hypot(a.x, a.y) || 1;
  return { x: a.x / len, y: a.y / len };
};
const rotate = (a: Point, deg: number): Point => {
  const r = (deg * Math.PI) / 180;
  return { x: a.x * Math.cos(r) - a.y * Math.sin(r), y: a.x * Math.sin(r) + a.y * Math.cos(r) };
};

/** Etiqueta compacta: leído → escrito,mov. «·x» indica valor de la memoria caché. */
function edgeLabel(e: DiagramEdge): string {
  const mem = (v: string | null) => (v === null ? "" : `·${v}`);
  const { key, effect } = e;
  return `${sym(key.read_symbol)}${mem(key.memory_value)} → ${sym(effect.write_symbol)},${effect.movement}${mem(effect.next_memory_value)}`;
}

function groupEdges(edges: DiagramEdge[]): Group[] {
  const map = new Map<string, Group>();
  for (const e of edges) {
    const id = `${e.source}\u0000${e.target}`;
    const g = map.get(id) ?? { source: e.source, target: e.target, edges: [] };
    g.edges.push(e);
    map.set(id, g);
  }
  return [...map.values()];
}

function isApplied(e: DiagramEdge, h: Highlight | null): boolean {
  const t = h?.transition;
  return (
    !!t &&
    t.key.state === e.key.state &&
    t.key.memory_value === e.key.memory_value &&
    t.key.read_symbol === e.key.read_symbol
  );
}

function Label({ at, lines }: { at: Point; lines: { text: string; active: boolean }[] }) {
  const top = at.y - ((lines.length - 1) * LINE_H) / 2;
  return (
    <text className="sd-label" x={at.x} y={top} textAnchor="middle" dominantBaseline="middle">
      {lines.map((l, i) => (
        <tspan key={i} x={at.x} dy={i === 0 ? 0 : LINE_H} className={l.active ? "active" : undefined}>
          {l.text}
        </tspan>
      ))}
    </text>
  );
}

export function StateDiagram({ diagram, highlight }: { diagram: Diagram; highlight: Highlight | null }) {
  const n = diagram.states.length;
  // Estado inicial arriba, el resto en sentido horario.
  const ordered = [
    diagram.initial_state,
    ...diagram.states.filter((s) => s !== diagram.initial_state),
  ];
  const ring = n === 1 ? 0 : Math.max(130, n * 38);
  const margin = 150;
  const size = 2 * (ring + margin);
  const center: Point = { x: size / 2, y: size / 2 };
  const pos = new Map<string, Point>(
    ordered.map((s, i) => {
      const angle = (-90 + (360 * i) / n) * (Math.PI / 180);
      return [s, { x: center.x + ring * Math.cos(angle), y: center.y + ring * Math.sin(angle) }];
    }),
  );

  const groups = groupEdges(diagram.edges);
  const activeState = highlight?.state ?? null;

  return (
    <svg
      className="state-diagram"
      viewBox={`0 0 ${size} ${size}`}
      role="img"
      aria-label="Diagrama de estados de la máquina de Turing"
    >
      <defs>
        <marker id="sd-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" className="sd-arrow" />
        </marker>
        <marker id="sd-arrow-active" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" className="sd-arrow active" />
        </marker>
      </defs>

      {groups.map((g) => {
        const a = pos.get(g.source)!;
        const b = pos.get(g.target)!;
        const lines = g.edges.map((e) => ({ text: edgeLabel(e), active: isApplied(e, highlight) }));
        const active = lines.some((l) => l.active);
        const cls = `sd-edge${active ? " active" : ""}`;
        const marker = `url(#${active ? "sd-arrow-active" : "sd-arrow"})`;
        const key = `${g.source}->${g.target}`;

        if (g.source === g.target) {
          const dir = n === 1 ? { x: 0, y: -1 } : unit({ x: a.x - center.x, y: a.y - center.y });
          const p1 = add(a, scale(rotate(dir, -35), NODE_R));
          const p2 = add(a, scale(rotate(dir, 35), NODE_R + 3));
          const c1 = add(a, scale(rotate(dir, -40), NODE_R + 62));
          const c2 = add(a, scale(rotate(dir, 40), NODE_R + 62));
          const labelAt = add(a, scale(dir, NODE_R + 52 + (lines.length * LINE_H) / 2));
          return (
            <g key={key}>
              <path className={cls} d={`M${p1.x},${p1.y} C${c1.x},${c1.y} ${c2.x},${c2.y} ${p2.x},${p2.y}`} markerEnd={marker} />
              <Label at={labelAt} lines={lines} />
            </g>
          );
        }

        // Curva hacia la derecha del sentido a→b: separa las aristas a→b y b→a.
        const mid = scale(add(a, b), 0.5);
        const d = unit({ x: b.x - a.x, y: b.y - a.y });
        const dist = Math.hypot(b.x - a.x, b.y - a.y);
        const ctrl = add(mid, scale({ x: -d.y, y: d.x }, Math.min(55, dist * 0.3)));
        const start = add(a, scale(unit({ x: ctrl.x - a.x, y: ctrl.y - a.y }), NODE_R));
        const end = add(b, scale(unit({ x: ctrl.x - b.x, y: ctrl.y - b.y }), NODE_R + 3));
        const labelAt = add(
          add(scale(a, 0.25), add(scale(ctrl, 0.5), scale(b, 0.25))),
          scale({ x: -d.y, y: d.x }, 8 + (lines.length * LINE_H) / 2),
        );
        return (
          <g key={key}>
            <path className={cls} d={`M${start.x},${start.y} Q${ctrl.x},${ctrl.y} ${end.x},${end.y}`} markerEnd={marker} />
            <Label at={labelAt} lines={lines} />
          </g>
        );
      })}

      {ordered.map((s) => {
        const p = pos.get(s)!;
        const isFinal = s === diagram.final_state;
        return (
          <g key={s} className={`sd-node${s === activeState ? " active" : ""}`}>
            {s === diagram.initial_state && (
              <path
                className="sd-edge"
                d={`M${p.x - NODE_R - 34},${p.y} L${p.x - NODE_R - 1},${p.y}`}
                markerEnd="url(#sd-arrow)"
              />
            )}
            <circle cx={p.x} cy={p.y} r={NODE_R} />
            {isFinal && <circle cx={p.x} cy={p.y} r={NODE_R - 5} />}
            <text x={p.x} y={p.y} textAnchor="middle" dominantBaseline="central">
              {s}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
