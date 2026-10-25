"use client";
import { useEffect, useRef, useState } from "react";

/** Private to this browser and session; never encoded in a companion URL. */
export function useViewerVisit(
  id: string,
  clock: number | undefined,
  enabled: boolean,
) {
  const [visit, setVisit] = useState<{
    id: string;
    from: number;
    returning: boolean;
  } | null>(null);
  const latest = useRef(clock);
  if (typeof document !== "undefined" && document.visibilityState === "visible")
    latest.current = clock;
  useEffect(() => {
    if (!enabled || clock === undefined) return;
    const key = `why-now-visit:${id}`;
    let previous: number | null = null;
    try {
      const saved = localStorage.getItem(key);
      const value = saved === null ? NaN : Number(saved);
      if (Number.isFinite(value) && value >= 0 && value <= clock)
        previous = value;
    } catch {
      /* Private browsing can disable storage. */
    }
    setVisit({ id, from: previous ?? clock, returning: previous !== null });
    const save = () => {
      if (latest.current === undefined) return;
      try {
        localStorage.setItem(key, String(latest.current));
      } catch {
        /* No account required. */
      }
    };
    const visibility = () => {
      if (document.visibilityState === "hidden") save();
    };
    window.addEventListener("pagehide", save);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      save();
      window.removeEventListener("pagehide", save);
      document.removeEventListener("visibilitychange", visibility);
    };
    // A visit starts at the first delivered snapshot, not every clock tick.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, enabled, clock === undefined]);
  return visit?.id === id ? visit : null;
}
