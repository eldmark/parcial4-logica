import type { Player } from "../usePlayer";

export function Controls({ player }: { player: Player }) {
  const atStart = player.index === 0;
  const atEnd = player.index === player.last;
  return (
    <div className="row controls">
      <button type="button" onClick={player.first} disabled={atStart} title="Primer paso">
        ⏮
      </button>
      <button type="button" onClick={player.prev} disabled={atStart} title="Paso anterior">
        ◀
      </button>
      <button type="button" className="play" onClick={player.toggle}>
        {player.playing ? "⏸ Pausa" : "▶ Reproducir"}
      </button>
      <button type="button" onClick={player.next} disabled={atEnd} title="Paso siguiente">
        ▶
      </button>
      <button type="button" onClick={player.end} disabled={atEnd} title="Último paso">
        ⏭
      </button>
      <label className="speed">
        Velocidad ({player.delayMs} ms/paso)
        <input
          type="range"
          min={50}
          max={1500}
          step={50}
          value={1550 - player.delayMs}
          onChange={(e) => player.setDelayMs(1550 - Number(e.target.value))}
        />
      </label>
      <span className="muted step-count">
        {player.index} / {player.last}
      </span>
    </div>
  );
}
