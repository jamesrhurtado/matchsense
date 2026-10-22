import { useEffect, useState } from "react";
import { Pause, Play, ScanLine, X } from "lucide-react";
import { Evidence, timecode } from "@/lib/api";
import { Button, Card } from "./ui";
import Pitch from "./pitch";

export function EvidenceReplay({
  data,
  onClose,
  focus,
}: {
  data: Evidence;
  onClose: () => void;
  focus: string;
}) {
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
      label: "Before release",
      at: release == null ? undefined : release - 100,
    },
    { label: "Pass", at: release },
    { label: "Reception / continuation", at: reception },
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
      ? "Verified passer"
      : focus === m.receiver_id
        ? "Verified receiver"
        : null;
  return (
    <Card className="mt-6 overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 p-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-800">
            <ScanLine size={14} />
            EVIDENCE REPLAY
          </div>
          <h2 className="mt-2 text-balance text-xl font-semibold">
            Replay the sequence.
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-stone-400">
            Independent of live replay
          </span>
          <button aria-label="Close evidence" onClick={onClose} className="p-2">
            <X size={18} />
          </button>
        </div>
      </div>
      <div className="grid items-center gap-0 md:grid-cols-3">
        <div className="md:col-span-2">
          <div
            className="flex flex-wrap gap-2 bg-stone-50 px-3 py-2"
            role="group"
            aria-label="Evidence stages"
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
          />
          {focus && (
            <p className="bg-stone-50 px-3 py-2 text-xs text-stone-600">
              {role || "No verified passer or receiver role for this focus."}
              {trails.some((points) => points.length > 1)
                ? " Trail: observed positions only; missing frames are not joined."
                : ""}
            </p>
          )}
          <div className="flex items-center gap-3 bg-stone-50 p-3">
            <Button
              aria-label={
                playing ? "Pause evidence replay" : "Play evidence replay"
              }
              onClick={() => setPlaying(!playing)}
              className="px-3"
            >
              {playing ? <Pause size={14} /> : <Play size={14} />}
            </Button>
            <label htmlFor="evidence-time" className="sr-only">
              Evidence replay time
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
            label="opponents close before release"
            note={`Within ${m.pressure_radius_m} m · 2 s trailing window`}
          />
          <Metric
            value={String(m.bypassed_count)}
            label="longitudinal positions passed"
            note="Longitudinal positions at release"
          />
          <Metric
            value={`${m.progression_m.toFixed(1)} m`}
            label="team ball movement after reception"
            note={`Possession held for ${m.retention_window_ms / 1000} s after reception`}
          />
        </div>
      </div>
      <details className="border-t border-stone-100 p-5">
        <summary className="text-sm font-medium text-stone-600">
          Definitions, source observations & limits
        </summary>
        <div className="mt-4 space-y-3 text-sm leading-relaxed text-stone-500">
          <p>
            Coverage: {Math.round(m.coverage * 100)}% of the pressure window ·{" "}
            {m.pressure_samples} frames. Source positions are 10 Hz; playback
            adds no evidence.
          </p>
          {m.limitations.map((l) => (
            <p key={l}>{l}</p>
          ))}
          <p className="break-all font-mono text-xs">
            Evidence {data.story.evidence_revision}
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
