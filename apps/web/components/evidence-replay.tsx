import { EventEvidence } from "./event-evidence";
import { useEffect, useState } from "react";
import { Pause, Play, ScanLine, X } from "lucide-react";
import { Evidence, timecode } from "@/lib/api";
import { Button, Card } from "./ui";
import Pitch from "./pitch";
import { displayMetres } from "./pass-comparison";

export function EvidenceReplay(props: {
  data: Evidence;
  onClose: () => void;
  focus: string;
  language?: string;
}) {
  if (props.data.story.metrics.family)
    return (
      <Card className="mt-6 p-4">
        <Button onClick={props.onClose}>
          {props.language === "es" ? "Cerrar evidencia" : "Close evidence"}
        </Button>
        <EventEvidence data={props.data} language={props.language} />
      </Card>
    );
  return <PassEvidenceReplay {...props} />;
}
function PassEvidenceReplay({
  data,
  onClose,
  focus,
  language = "en",
}: {
  data: Evidence;
  onClose: () => void;
  focus: string;
  language?: string;
}) {
  const es = language === "es";
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const frames = data.frames.filter((frame) => frame.time_ms <= data.cutoff_ms);
  const m = data.story.metrics;
  useEffect(() => {
    setIndex(0);
    setPlaying(false);
  }, [data.story.id, data.story.revision]);
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(
      () =>
        setIndex((i) => {
          if (i + 1 >= frames.length) {
            setPlaying(false);
            return 0;
          }
          return i + 1;
        }),
      100,
    );
    return () => clearInterval(timer);
  }, [playing, frames.length]);
  const f = frames[Math.min(index, frames.length - 1)];
  const release = m.pressure_window_ms?.[1];
  const reception =
    m.retention_confirmed_at_ms == null
      ? undefined
      : m.retention_confirmed_at_ms - m.retention_window_ms;
  const stages = [
    {
      label: es ? "Antes del pase" : "Before release",
      at: release == null ? undefined : release - 100,
    },
    { label: es ? "Pase" : "Pass", at: release },
    {
      label: es ? "Recepción / continuación" : "Reception / continuation",
      at: reception,
    },
  ];
  const seekStage = (at: number) => {
    let selected = 0;
    frames.forEach((frame, i) => {
      if (frame.time_ms <= at) selected = i;
    });
    setIndex(selected);
    setPlaying(false);
  };
  const trails: { x_m: number; y_m: number }[][] = [];
  let previousTime: number | undefined;
  if (focus && !["blue", "amber"].includes(focus))
    frames.slice(0, index + 1).forEach((frame) => {
      const player = frame.payload.players.find(
        (player) => player.player_id === focus,
      );
      if (!player) {
        previousTime = undefined;
        return;
      }
      if (previousTime == null || frame.time_ms - previousTime > 150)
        trails.push([]);
      trails.at(-1)!.push(player);
      previousTime = frame.time_ms;
    });
  const role =
    focus === m.passer_id
      ? es
        ? "Pasador verificado"
        : "Verified passer"
      : focus === m.receiver_id
        ? es
          ? "Receptor verificado"
          : "Verified receiver"
        : null;
  return (
    <Card className="mt-6 overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 p-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-800">
            <ScanLine size={14} />
            {es ? "REPETICIÓN DE LA EVIDENCIA" : "EVIDENCE REPLAY"}
          </div>
          <h2 className="mt-2 text-balance text-xl font-semibold">
            {es ? "Repite la secuencia." : "Replay the sequence."}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-stone-400">
            {es ? "Independiente del directo" : "Independent of live replay"}
          </span>
          <button
            aria-label={es ? "Cerrar evidencia" : "Close evidence"}
            onClick={onClose}
            className="p-2"
          >
            <X size={18} />
          </button>
        </div>
      </div>
      <div className="grid items-center gap-0 md:grid-cols-3">
        <div className="md:col-span-2">
          <div
            className="flex flex-wrap gap-2 bg-stone-50 px-3 py-2"
            role="group"
            aria-label={es ? "Etapas de la evidencia" : "Evidence stages"}
          >
            {stages.map((stage) => (
              <Button
                key={stage.label}
                disabled={stage.at == null}
                onClick={() => seekStage(stage.at!)}
              >
                {stage.label}
              </Button>
            ))}
          </div>
          <Pitch
            frame={f?.payload || null}
            metrics={m}
            focus={focus}
            trails={trails}
            compact
            language={language}
          />
          {focus && (
            <p className="bg-stone-50 px-3 py-2 text-xs text-stone-600">
              {role ||
                (es
                  ? "Sin rol verificado de pasador o receptor para este enfoque."
                  : "No verified passer or receiver role for this focus.")}
              {trails.some((points) => points.length > 1)
                ? es
                  ? " Trayectoria: solo posiciones observadas; los intervalos sin datos no se unen."
                  : " Trail: observed positions only; missing frames are not joined."
                : ""}
            </p>
          )}
          <div className="flex items-center gap-3 bg-stone-50 p-3">
            <Button
              aria-label={
                playing
                  ? es
                    ? "Pausar evidencia"
                    : "Pause evidence replay"
                  : es
                    ? "Reproducir evidencia"
                    : "Play evidence replay"
              }
              onClick={() => setPlaying(!playing)}
              className="px-3"
            >
              {playing ? <Pause size={14} /> : <Play size={14} />}
            </Button>
            <label htmlFor="evidence-time" className="sr-only">
              {es ? "Tiempo de la evidencia" : "Evidence replay time"}
            </label>
            <input
              id="evidence-time"
              className="min-w-0 flex-1 accent-emerald-700"
              type="range"
              min="0"
              max={Math.max(0, frames.length - 1)}
              value={index}
              onChange={(e) => {
                setIndex(Number(e.target.value));
                setPlaying(false);
              }}
            />
            <span className="font-mono text-xs tabular-nums text-stone-500">
              {timecode(f?.time_ms || 0)}
            </span>
          </div>
        </div>
        <div className="space-y-5 p-5">
          <Metric
            value={String(m.pressure_opponents_max)}
            label={
              es
                ? "oponentes cercanos antes del pase"
                : "opponents close before release"
            }
            note={
              es
                ? `Dentro de ${displayMetres(m.pressure_radius_m)} m · 2 s anteriores`
                : `Within ${displayMetres(m.pressure_radius_m)} m · 2 s trailing window`
            }
          />
          <Metric
            value={String(m.bypassed_count)}
            label={
              es
                ? "posiciones longitudinales superadas"
                : "longitudinal positions passed"
            }
            note={
              es
                ? "Posiciones longitudinales al pasar"
                : "Longitudinal positions at release"
            }
          />
          <Metric
            value={`${displayMetres(m.progression_m)} m`}
            label={
              es
                ? "movimiento del balón del equipo tras la recepción"
                : "team ball movement after reception"
            }
            note={
              es
                ? `Posesión mantenida durante ${m.retention_window_ms / 1000} s tras la recepción`
                : `Possession held for ${m.retention_window_ms / 1000} s after reception`
            }
          />
        </div>
      </div>
      <details className="border-t border-stone-100 p-5">
        <summary className="text-sm font-medium text-stone-600">
          {es
            ? "Definiciones, observaciones y límites"
            : "Definitions, source observations & limits"}
        </summary>
        <div className="mt-4 space-y-3 text-sm leading-relaxed text-stone-500">
          <p>
            {es
              ? `Cobertura: ${Math.round(m.coverage * 100)}% del intervalo de proximidad · ${m.pressure_samples} fotogramas. Las posiciones se registran a 10 Hz; reproducirlas no añade evidencia.`
              : `Coverage: ${Math.round(m.coverage * 100)}% of the pressure window · ${m.pressure_samples} frames. Source positions are 10 Hz; playback adds no evidence.`}
          </p>
          {m.limitations.map((l) => (
            <p key={l} lang={es && SPANISH_LIMITATIONS[l] ? "es" : "en"}>
              {es ? SPANISH_LIMITATIONS[l] || l : l}
            </p>
          ))}
          <p className="break-all font-mono text-xs">
            {es ? "Evidencia" : "Evidence"} {data.story.evidence_revision}
            <br />
            {m.source_message_ids.join(", ")}
          </p>
        </div>
      </details>
    </Card>
  );
}
function Metric({
  value,
  label,
  note,
}: {
  value: string;
  label: string;
  note: string;
}) {
  return (
    <div>
      <p className="text-3xl font-semibold tabular-nums text-stone-800">
        {value}
      </p>
      <p className="mt-1 text-sm font-medium">{label}</p>
      <p className="mt-1 text-xs leading-relaxed text-stone-400">{note}</p>
    </div>
  );
}

const SPANISH_LIMITATIONS: Record<string, string> = {
  "Pressure is opponent proximity, not a calibrated probability.":
    "La presión mide la proximidad de los oponentes, no una probabilidad calibrada.",
  "Bypassed counts longitudinal positions at release; it does not prove a defensive line was broken.":
    "El recuento considera posiciones longitudinales al pasar; no demuestra que se haya superado una línea defensiva.",
  "This sequence does not establish intent or sustained match control.":
    "Esta secuencia no demuestra intención ni control sostenido del partido.",
};
