import { useState } from "react";
import { cn, Evidence, Variant, timecode } from "@/lib/api";
import Pitch from "./pitch";
import { PassComparison } from "./pass-comparison";

/** Clause bindings select recorded frames; the arrow measures displacement only. */
export function InlineEvidence({
  evidence,
  variant,
  language,
  focus,
}: {
  evidence: Evidence;
  variant: Variant | null;
  language: string;
  focus: string;
}) {
  const [selected, setSelected] = useState("c-forward");
  const m = evidence.story.metrics;
  const es = language === "es";
  const at =
    selected === "c-retain" || selected === "c-progress"
      ? m.retention_confirmed_at_ms
      : selected === "c-zone" || selected === "c-reception"
        ? m.reception_ms
        : m.release_ms;
  let frame = evidence.frames.filter((f) => f.time_ms <= (at ?? 0)).at(-1);
  if (selected === "c-pressure") {
    const candidates = evidence.frames.filter(
      (f) =>
        m.pressure_window_ms &&
        f.time_ms >= m.pressure_window_ms[0] &&
        f.time_ms <= m.pressure_window_ms[1],
    );
    const count = (f: typeof frame) => {
      const passer = f?.payload.players.find(
        (p) => p.player_id === m.passer_id,
      );
      if (!passer) return -1;
      return f!.payload.players.filter(
        (p) =>
          p.team_id !== passer.team_id &&
          Math.hypot(p.x_m - passer.x_m, p.y_m - passer.y_m) <=
            m.pressure_radius_m,
      ).length;
    };
    frame =
      candidates.reduce<typeof frame>(
        (best, next) => (count(next) > count(best) ? next : best),
        undefined,
      ) ?? frame;
  }
  const interval =
    selected === "c-retain" || selected === "c-progress"
      ? [m.reception_ms, m.retention_confirmed_at_ms]
      : selected === "c-pressure"
        ? m.pressure_window_ms
        : [m.release_ms, m.reception_ms];

  return (
    <div
      className="mt-4 overflow-hidden rounded-xl border border-stone-200"
      data-testid="inline-evidence"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 bg-stone-50 px-3 py-2 text-xs text-stone-600">
        <span>
          {es ? "Evidencia seleccionada" : "Selected evidence"} ·{" "}
          {timecode(frame?.time_ms ?? 0)}
        </span>
        <span>
          {es ? "Reloj independiente del directo" : "Separate from live clock"}
        </span>
      </div>
      <div className="bg-emerald-950">
        <div className="mx-auto max-w-xs">
          <Pitch
            frame={frame?.payload ?? null}
            metrics={m}
            focus={focus}
            compact
            language={language}
            highlight={selected}
          />
        </div>
      </div>
      <p className="border-t border-stone-200 px-3 py-2 text-xs tabular-nums text-stone-600">
        {es ? "Intervalo observado" : "Observed interval"}:{" "}
        {timecode(interval?.[0] ?? 0)}–{timecode(interval?.[1] ?? 0)}
        {selected === "c-retain"
          ? es
            ? " · posesión del equipo"
            : " · team possession"
          : ""}
      </p>
      <details className="p-3">
        <summary className="min-h-11 cursor-pointer py-3 text-sm font-medium">
          {es ? "Inspeccionar las afirmaciones" : "Inspect the facts"}
        </summary>
        <div
          className="space-y-2"
          role="group"
          aria-label={
            es
              ? "Elegir evidencia de una afirmación"
              : "Select a fact to inspect its evidence"
          }
        >
          {variant?.clauses
            ?.filter(
              (clause) =>
                clause.claim_ids.length > 0 && clause.id !== "qualification",
            )
            .map((clause) => (
              <button
                key={clause.id}
                type="button"
                aria-pressed={selected === clause.claim_ids[0]}
                onClick={() => setSelected(clause.claim_ids[0])}
                className={cn(
                  "block min-h-11 w-full rounded-lg border px-3 py-2 text-left text-xs leading-relaxed",
                  selected === clause.claim_ids[0]
                    ? "border-emerald-600 bg-emerald-50 text-emerald-950"
                    : "border-stone-200 text-stone-600",
                )}
              >
                {clause.text}
              </button>
            ))}
        </div>
      </details>
      {selected === "c-context" && m.context && (
        <PassComparison metrics={m} language={language} />
      )}
    </div>
  );
}
