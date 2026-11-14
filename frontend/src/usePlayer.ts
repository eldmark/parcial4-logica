import { useCallback, useEffect, useState } from "react";

/** Controla el índice actual de una traza de `length` snapshots, con reproducción automática. */
export function usePlayer(length: number) {
  const last = Math.max(0, length - 1);
  const [index, setIndexRaw] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [delayMs, setDelayMs] = useState(500);

  const setIndex = useCallback(
    (i: number) => setIndexRaw(Math.min(last, Math.max(0, i))),
    [last],
  );

  useEffect(() => {
    if (!playing) return;
    if (index >= last) {
      setPlaying(false);
      return;
    }
    const id = setTimeout(() => setIndexRaw((i) => Math.min(last, i + 1)), delayMs);
    return () => clearTimeout(id);
  }, [playing, index, last, delayMs]);

  return {
    index,
    last,
    playing,
    delayMs,
    setDelayMs,
    setIndex,
    first: () => {
      setPlaying(false);
      setIndex(0);
    },
    prev: () => {
      setPlaying(false);
      setIndex(index - 1);
    },
    next: () => {
      setPlaying(false);
      setIndex(index + 1);
    },
    end: () => {
      setPlaying(false);
      setIndex(last);
    },
    toggle: () => {
      if (index >= last) setIndexRaw(0);
      setPlaying((p) => !p);
    },
  };
}

export type Player = ReturnType<typeof usePlayer>;
