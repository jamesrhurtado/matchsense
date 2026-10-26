"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Pause, Play, RotateCcw, Square, Volume2 } from "lucide-react";
import { cn } from "@/lib/api";

type PlaybackState = "idle" | "speaking" | "paused" | "finished" | "stopped" | "error";

/** Opt-in, transcript-backed reading of approved text; never generates new match claims. */
export function ListenButton({
  text,
  evidenceText,
  language,
  dark = false,
  heading,
}: {
  text: string;
  evidenceText?: string;
  language: string;
  dark?: boolean;
  heading?: string;
}) {
  const id = useId();
  const es = language === "es";
  const evidenceAvailable = Boolean(
    evidenceText?.trim() && evidenceText.trim() !== text.trim(),
  );
  const [evidenceSelected, setEvidenceSelected] = useState(false);
  const [available, setAvailable] = useState(false);
  const [state, setState] = useState<PlaybackState>("idle");
  const [error, setError] = useState(false);
  const sequence = useRef(0);
  const activeText = evidenceSelected && evidenceAvailable ? evidenceText! : text;
  const activeLabel = evidenceSelected && evidenceAvailable
    ? es ? "evidencia y límites" : "evidence and limitations"
    : es ? "explicación aprobada" : "approved explanation";
  const buttonClass = dark
    ? "border border-white/20 text-emerald-50 hover:bg-white/10 focus-visible:outline-emerald-200"
    : "border border-emerald-200 text-emerald-950 hover:bg-emerald-50 focus-visible:outline-emerald-700";

  useEffect(() => {
    setAvailable(
      "speechSynthesis" in window && "SpeechSynthesisUtterance" in window,
    );
    return () => {
      sequence.current += 1;
      window.speechSynthesis?.cancel();
    };
  }, []);

  useEffect(() => {
    sequence.current += 1;
    window.speechSynthesis?.cancel();
    setState("idle");
    setError(false);
    return () => {
      sequence.current += 1;
      window.speechSynthesis?.cancel();
    };
  }, [activeText, language]);

  function start() {
    if (!available || !activeText.trim()) return;
    const request = ++sequence.current;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(activeText);
    utterance.lang = es ? "es-ES" : "en-GB";
    utterance.rate = 0.95;
    utterance.onstart = () => {
      if (sequence.current === request) setState("speaking");
    };
    utterance.onend = () => {
      if (sequence.current === request) setState("finished");
    };
    utterance.onerror = (event) => {
      if (sequence.current !== request) return;
      setState("error");
      setError(!["canceled", "interrupted"].includes(event.error));
    };
    setError(false);
    setState("speaking");
    window.speechSynthesis.speak(utterance);
  }

  function togglePlayback() {
    if (state === "speaking") {
      window.speechSynthesis.pause();
      setState("paused");
    } else if (state === "paused") {
      window.speechSynthesis.resume();
      setState("speaking");
    } else {
      start();
    }
  }

  function stop() {
    sequence.current += 1;
    window.speechSynthesis?.cancel();
    setError(false);
    setState("stopped");
  }

  const status = !available
    ? es
      ? "La voz del navegador no está disponible; el texto sigue disponible."
      : "Speech is unavailable in this browser; the text remains available."
    : error
      ? es
        ? "No se pudo reproducir el audio. El texto sigue disponible."
        : "Audio could not be played. The text remains available."
      : state === "speaking"
        ? es
          ? `Reproduciendo ${activeLabel}.`
          : `Playing ${activeLabel}.`
        : state === "paused"
          ? es ? "Audio en pausa." : "Audio paused."
          : state === "finished"
            ? es ? "Audio terminado." : "Audio finished."
            : state === "stopped"
              ? es ? "Audio detenido." : "Audio stopped."
              : es
                ? "El audio solo comienza cuando lo pides."
                : "Audio starts only when you ask for it.";

  return (
    <section
      className={cn(
        "rounded-xl border p-3",
        dark ? "border-white/15 bg-white/5" : "border-emerald-200 bg-emerald-50/70",
      )}
      aria-label={heading || (es ? "Narración de audio" : "Audio narration")}
      data-testid="audio-narration"
    >
      {heading && (
        <h3 className={cn("text-sm font-semibold", dark ? "text-white" : "text-emerald-950")}>
          {heading}
        </h3>
      )}
      {evidenceAvailable && (
        <div
          role="group"
          aria-label={es ? "Contenido de audio" : "Audio content"}
          className="mt-2 flex flex-wrap gap-2"
        >
          <button
            type="button"
            aria-pressed={!evidenceSelected}
            onClick={() => setEvidenceSelected(false)}
            className={cn(
              "min-h-11 rounded-lg border px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2",
              buttonClass,
              !evidenceSelected && (dark ? "bg-white/15" : "bg-white"),
            )}
          >
            {es ? "Explicación" : "Explanation"}
          </button>
          <button
            type="button"
            aria-pressed={evidenceSelected}
            onClick={() => setEvidenceSelected(true)}
            className={cn(
              "min-h-11 rounded-lg border px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2",
              buttonClass,
              evidenceSelected && (dark ? "bg-white/15" : "bg-white"),
            )}
          >
            {es ? "Evidencia y límites" : "Evidence and limits"}
          </button>
        </div>
      )}
      <div className="mt-2 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={togglePlayback}
          disabled={!available || !activeText.trim()}
          aria-label={
            state === "speaking"
              ? es ? "Pausar audio" : "Pause audio"
              : state === "paused"
                ? es ? "Reanudar audio" : "Resume audio"
                : es ? `Escuchar ${activeLabel}` : `Listen to ${activeLabel}`
          }
          className={cn(
            "inline-flex min-h-11 items-center gap-2 rounded-lg px-3 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            buttonClass,
            dark ? "bg-emerald-900/50" : "bg-white",
          )}
        >
          {state === "speaking" ? (
            <Pause size={16} aria-hidden="true" />
          ) : state === "idle" || state === "finished" || state === "stopped" || state === "error" ? (
            <Volume2 size={17} aria-hidden="true" />
          ) : (
            <Play size={16} aria-hidden="true" />
          )}
          {state === "speaking"
            ? es ? "Pausar" : "Pause"
            : state === "paused"
              ? es ? "Reanudar" : "Resume"
              : es ? "Escuchar" : "Listen"}
        </button>
        <button
          type="button"
          onClick={start}
          disabled={!available || !activeText.trim()}
          aria-label={es ? "Repetir desde el principio" : "Repeat from the beginning"}
          className={cn(
            "inline-flex min-h-11 items-center gap-2 rounded-lg px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            buttonClass,
          )}
        >
          <RotateCcw size={15} aria-hidden="true" />
          {es ? "Repetir" : "Repeat"}
        </button>
        <button
          type="button"
          onClick={stop}
          disabled={!available || !["speaking", "paused"].includes(state)}
          aria-label={es ? "Detener audio" : "Stop audio"}
          className={cn(
            "inline-flex min-h-11 items-center gap-2 rounded-lg px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            buttonClass,
          )}
        >
          <Square size={14} aria-hidden="true" />
          {es ? "Detener" : "Stop"}
        </button>
      </div>
      <p
        role="status"
        aria-live="polite"
        className={cn("mt-2 text-xs leading-relaxed", dark ? "text-white/75" : "text-stone-700")}
      >
        {status}
      </p>
      <details className="mt-1">
        <summary
          className={cn(
            "min-h-11 cursor-pointer py-2 text-sm font-medium",
            dark ? "text-emerald-100" : "text-emerald-900",
          )}
        >
          {es ? "Leer transcripción" : "Read transcript"}
        </summary>
        <p lang={language} className={cn("pb-2 text-sm leading-relaxed", dark ? "text-white/80" : "text-stone-700")}>
          {activeText}
        </p>
      </details>
    </section>
  );
}
