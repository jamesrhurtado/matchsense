"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  MessageCircle,
  Radio,
} from "lucide-react";
import { api, Match, Story, timecode, Variant } from "@/lib/api";
import { Button, Card, Tag } from "./ui";

type AudienceGroup = {
  id: string;
  question: string;
  interpretation: string | null;
  message_count: number;
  participant_count: number;
  first_at: string;
  last_at: string;
  story_id: string | null;
  story_revision: number | null;
  story_status: string | null;
  association_confirmed: boolean;
  reason: string;
  mode: "ai" | "template" | "fallback";
  state: "pending" | "dismissed";
};
type AudienceStatus = {
  source: "rehearsal" | "youtube" | null;
  status: "idle" | "connected" | "error";
  video_id: string | null;
  error: string | null;
  groups: AudienceGroup[];
  window_seconds: number;
  available_message_count: number;
  sample_limited: boolean;
  youtube_authorized: boolean;
};
type DirectorDecision = {
  action: "show" | "hold" | "wait";
  story_id: string | null;
  revision: number | null;
  package_hash: string | null;
  status: "ready" | "approved" | null;
  reason: string;
  mode: "ai" | "template" | "fallback";
  eligible_until_ms: number | null;
};

function modeLabel(mode: AudienceGroup["mode"], es: boolean) {
  if (mode === "ai") return es ? "IA" : "AI";
  if (mode === "fallback") return es ? "Alternativa sin IA" : "Non-AI fallback";
  return es ? "Reglas sin IA" : "Non-AI rules";
}

function audienceModeLabel(mode: AudienceGroup["mode"], es: boolean) {
  if (mode === "ai") return es ? "Analizado por IA" : "AI analyzed";
  if (mode === "fallback") return es ? "Respaldo sin IA" : "Rule fallback";
  return es ? "Agrupación por reglas" : "Rule grouping";
}

function youtubeVideoId(value: string) {
  const input = value.trim();
  if (/^[A-Za-z0-9_-]{11}$/.test(input)) return input;
  try {
    const url = new URL(input);
    if (!["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"].includes(url.hostname)) return "";
    const id = url.hostname.includes("youtu.be")
      ? url.pathname.split("/").filter(Boolean)[0]
      : url.searchParams.get("v") || url.pathname.match(/^\/(?:live|shorts|embed)\/([^/?]+)/)?.[1] || "";
    return /^[A-Za-z0-9_-]{11}$/.test(id) ? id : "";
  } catch {
    return "";
  }
}

function Draft({
  path,
  group,
  story,
  language,
}: {
  path: string;
  group: AudienceGroup;
  story: Story;
  language: string;
}) {
  const [draft, setDraft] = useState<Variant | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    setDraft(null);
    setFailed(false);
    void api<Variant>(
      `${path}/stories/${encodeURIComponent(story.id)}/variants?language=${language === "es" ? "es" : "en"}&detail=simple`,
      {},
      true,
    )
      .then((value) => {
        if (
          active &&
          value.revision === story.revision &&
          value.revision === group.story_revision
        )
          setDraft(value);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
    };
  }, [path, story.id, story.revision, group.story_revision, language]);
  if (failed)
    return (
      <p className="mt-2 text-xs text-amber-900">
        {language === "es"
          ? "No se pudo cargar la explicación; vuelve a seleccionar la historia."
          : "Could not load the explanation; select the story to retry."}
      </p>
    );
  return (
    <p className="mt-2 text-sm leading-relaxed text-stone-700">
      {draft?.text ||
        (language === "es"
          ? "Cargando explicación disponible…"
          : "Loading available explanation…")}
    </p>
  );
}

export function BroadcastAgents({
  id,
  match,
  stories,
  language,
  onSelect,
  onRefresh,
}: {
  id: string;
  match: Match | null;
  stories: Story[];
  language: string;
  onSelect: (id: string) => void;
  onRefresh: () => Promise<void>;
}) {
  const es = language === "es";
  const path = `/replay-sessions/${encodeURIComponent(id)}`;
  const audiencePath = `${path}/audience`;
  const [audience, setAudience] = useState<AudienceStatus | null>(null);
  const [videoId, setVideoId] = useState("");
  const [rehearsal, setRehearsal] = useState("");
  const [decision, setDecision] = useState<DirectorDecision | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [chosenStories, setChosenStories] = useState<Record<string, string>>(
    {},
  );

  const load = useCallback(async () => {
    const data = await api<AudienceStatus>(audiencePath, {}, true);
    setAudience(data);
    return data;
  }, [audiencePath]);
  useEffect(() => {
    let active = true;
    const oauthResult = new URLSearchParams(window.location.search).get("youtube_oauth");
    if (oauthResult) {
      if (oauthResult === "connected")
        setNotice(es ? "Cuenta de YouTube conectada." : "YouTube account connected.");
      else if (oauthResult !== "denied")
        setError(es ? "No se pudo conectar la cuenta de YouTube. Revisa la configuración OAuth." : "Could not connect the YouTube account. Check its OAuth configuration.");
      window.history.replaceState({}, "", window.location.pathname);
    }
    void api<AudienceStatus>(audiencePath, {}, true)
      .then((data) => {
        if (active) setAudience(data);
      })
      .catch((e: Error) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [audiencePath, es]);
  useEffect(() => {
    if (audience?.source !== "youtube" || audience.status !== "connected")
      return;
    let active = true;
    const timer = window.setInterval(() => {
      // Do not overlap a manual operation. The server performs quota and cursor handling.
      if (busy || document.visibilityState !== "visible") return;
      void api<AudienceStatus>(
        `${audiencePath}/refresh`,
        { method: "POST" },
        true,
      )
        .then((data) => {
          if (active) setAudience(data);
        })
        .catch((e: Error) => {
          if (active) setError(e.message);
        });
    }, 20000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [audience?.source, audience?.status, audiencePath, busy]);

  async function operation(name: string, action: () => Promise<void>) {
    setBusy(name);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  const storyFor = (group: AudienceGroup) =>
    stories
      .flatMap((s) => [s, ...(s.related_stories || [])])
      .find(
        (s) => s.id === group.story_id && s.revision === group.story_revision,
      );
  const pending =
    audience?.groups.filter((group) => group.state === "pending") || [];
  const availableStories = stories
    .flatMap((item) => [item, ...(item.related_stories || [])])
    .filter(
      (item) =>
        !!item.package_hash &&
        ["ready", "approved"].includes(item.status) &&
        !!match &&
        item.eligible_from_ms <= match.clock_ms &&
        item.expires_at_ms > match.clock_ms,
    );
  const selectedDecision =
    decision?.story_id &&
    stories
      .flatMap((s) => [s, ...(s.related_stories || [])])
      .find(
        (s) =>
          s.id === decision.story_id &&
          s.revision === decision.revision &&
          s.package_hash === decision.package_hash,
      );

  return (
    <section
      aria-label={es ? "Equipo de emisión" : "Broadcast team"}
      className="space-y-4"
    >
      <Card className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-3 border-emerald-100 p-3 max-[440px]:grid-cols-1">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-800">
            <Radio size={16} aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-stone-900">
              {es ? "Productor de emisión" : "Broadcast producer"}
            </h2>
            <p className="mt-0.5 text-xs leading-snug text-stone-600">
              {es ? "Tú decides qué sale al aire." : "You decide what goes on air."}
            </p>
          </div>
        </div>
        <Button
          className="h-9 min-h-9 shrink-0 gap-2 rounded-lg border-emerald-200 bg-emerald-50 px-3 py-0 text-xs text-emerald-950 shadow-none hover:bg-emerald-100 max-[440px]:justify-self-start"
          disabled={!!busy}
          onClick={() =>
            void operation("director", async () => {
              const result = await api<DirectorDecision>(
                `${path}/broadcast/director`,
                { method: "POST" },
                true,
              );
              setDecision(result);
            })
          }
        >
          <ArrowRight size={16} aria-hidden="true" />
          {busy === "director"
            ? es
              ? "Evaluando…"
              : "Evaluating…"
            : es
              ? "Recomendar siguiente acción"
              : "Recommend next action"}
        </Button>
        {decision && (
          <div
            role="status"
            className="col-span-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 max-[440px]:col-span-1"
          >
            <div className="flex flex-wrap gap-2">
              <Tag>{modeLabel(decision.mode, es)}</Tag>
              <Tag>
                {decision.action === "show"
                  ? es
                    ? "Mostrar"
                    : "Show"
                  : decision.action === "hold"
                    ? es
                      ? "Mantener"
                      : "Hold"
                    : es
                      ? "Esperar"
                      : "Wait"}
              </Tag>
            </div>
            <p className="mt-2 text-sm text-emerald-950">{decision.reason}</p>
            {decision.eligible_until_ms !== null && (
              <p className="mt-2 text-xs text-emerald-800">
                {es ? "Ventana hasta" : "Window until"}{" "}
                {timecode(decision.eligible_until_ms)}
              </p>
            )}
            {selectedDecision && (
              <Button
                className="mt-3"
                onClick={() => onSelect(selectedDecision.id)}
              >
                {es ? "Revisar recomendación" : "Review recommendation"}
              </Button>
            )}
            {decision.story_id && !selectedDecision && (
              <p className="mt-2 text-xs text-amber-900">
                {es
                  ? "Esta recomendación ya no coincide con la versión actual. Solicita otra."
                  : "This recommendation no longer matches the current revision. Request another."}
              </p>
            )}
          </div>
        )}
      </Card>
      <details
        id="audience-agent-panel"
        className="overflow-hidden rounded-2xl border border-stone-200 bg-white"
      >
        <summary className="grid cursor-pointer list-none grid-cols-[2.5rem_minmax(0,1fr)] items-center gap-3 bg-white p-4 marker:content-none [&::-webkit-details-marker]:hidden">
          <span className="flex size-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-800">
            <MessageCircle size={18} aria-hidden="true" />
          </span>
          <span className="min-w-0">
            <span className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
              <span className="whitespace-nowrap text-sm font-semibold text-stone-900">
                Audience Agent
              </span>
              <span className="flex flex-wrap items-center justify-end gap-1.5">
                {audience?.youtube_authorized && (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-950">
                    <CheckCircle2 size={14} aria-hidden="true" />
                    {es ? "YouTube autorizado" : "YouTube account connected"}
                  </span>
                )}
                <Tag
                  className={`px-2.5 py-1 text-xs ${
                    audience?.source === "youtube" && audience.status === "connected"
                      ? "border-emerald-200 bg-emerald-50 text-emerald-900"
                      : "border-stone-200 bg-stone-50 text-stone-700"
                  }`}
                >
                  {audience?.source === "youtube" && audience.status === "connected"
                    ? es
                      ? "Chat conectado"
                      : "Chat connected"
                    : audience?.source === "rehearsal"
                      ? es
                        ? "Ensayo"
                        : "Rehearsal"
                      : es
                        ? "Sin conectar"
                        : "Not connected"}
                </Tag>
                <ChevronDown size={15} className="text-stone-500" aria-hidden="true" />
              </span>
            </span>
            <span className="mt-1 block text-xs leading-snug text-stone-600">
              {es
                ? "Preguntas de YouTube Live o de ensayo."
                : "YouTube Live or rehearsal questions."}
            </span>
          </span>
        </summary>
        <div className="space-y-4 border-t border-stone-100 bg-stone-50/60 p-4">
          <details
            className="rounded-lg border border-stone-200 p-3"
          >
            <summary className="min-h-11 cursor-pointer text-sm font-medium">
              {es ? "Conectar el chat en vivo de YouTube" : "Connect YouTube Live chat"}
            </summary>
            <div className="mt-3 space-y-4">
              {audience?.youtube_authorized ? (
                <div
                  role="status"
                  className="flex items-start gap-3 rounded-xl border border-emerald-300 bg-emerald-50 p-4 text-emerald-950"
                >
                  <CheckCircle2
                    size={20}
                    className="mt-0.5 shrink-0 text-emerald-800"
                    aria-hidden="true"
                  />
                  <div>
                    <p className="text-sm font-semibold text-emerald-950">
                      {es ? "Cuenta de YouTube conectada" : "YouTube account connected"}
                    </p>
                    <p className="mt-1 text-sm leading-relaxed text-emerald-900">
                      {audience.source === "youtube" && audience.status === "connected"
                        ? es
                          ? "El chat en vivo está conectado a esta transmisión."
                          : "Live chat is connected to this broadcast."
                        : es
                          ? "Ahora pega el enlace de una transmisión activa para conectar su chat."
                          : "Now paste the link to an active broadcast to connect its chat."}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    disabled={!!busy}
                    onClick={() =>
                      void operation("youtube-auth", async () => {
                        const result = await api<{ authorization_url: string }>(
                          `${audiencePath}/oauth/start`,
                          { method: "POST" },
                          true,
                        );
                        window.location.assign(result.authorization_url);
                      })
                    }
                  >
                    {busy === "youtube-auth"
                      ? es ? "Abriendo YouTube…" : "Opening YouTube…"
                      : es ? "Autorizar YouTube Live" : "Authorize YouTube Live"}
                  </Button>
                  <span className="text-xs text-stone-600">
                    {es
                      ? "Autoriza tu cuenta para poder enlazar el chat de una transmisión."
                      : "Authorize your account to link a broadcast chat."}
                  </span>
                </div>
              )}
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  void operation("connect", async () => {
                    const result = await api<AudienceStatus>(
                      `${audiencePath}/connect`,
                      {
                        method: "POST",
                        body: JSON.stringify({ video_id: youtubeVideoId(videoId) }),
                      },
                      true,
                    );
                    setAudience(result);
                    setNotice(
                      es ? "Conexión solicitada." : "Connection requested.",
                    );
                  });
                }}
              >
                <label
                  htmlFor="audience-video-id"
                  className="block text-sm font-medium"
                >
                  {es ? "Enlace o ID del video en vivo de YouTube" : "YouTube live video link or ID"}
                </label>
                <div className="mt-2 flex gap-2">
                  <input
                    id="audience-video-id"
                    value={videoId}
                    onChange={(e) => setVideoId(e.target.value)}
                    placeholder="https://youtu.be/…"
                    className="min-w-0 flex-1 rounded-lg border border-stone-300 px-3 py-2 text-sm"
                    autoComplete="off"
                  />
                  <Button type="submit" disabled={!!busy || !youtubeVideoId(videoId) || !audience?.youtube_authorized}>
                    {busy === "connect"
                      ? es
                        ? "Conectando…"
                        : "Connecting…"
                      : es
                        ? "Conectar"
                        : "Connect"}
                  </Button>
                </div>
                {!audience?.youtube_authorized && <p className="mt-1 text-xs text-stone-500">
                  {es
                    ? "Autoriza tu canal primero para leer el chat en vivo."
                    : "Authorize your channel first to read its live chat."}
                </p>}
                {audience?.source === "youtube" && <p className="mt-1 text-xs text-stone-500">{es ? "El chat se actualiza mientras esta consola esté abierta y visible. Puedes actualizarlo manualmente." : "Chat refreshes while this console is open and visible. You can also refresh it manually."}</p>}
              </form>
            </div>
          </details>
          <details
            id="audience-agent-rehearsal"
            className="rounded-lg border border-stone-200 bg-white p-3"
          >
            <summary className="cursor-pointer text-sm font-medium">
              {es
                ? "Ensayar con preguntas simuladas"
                : "Rehearse with simulated questions"}
            </summary>
            <form
              className="mt-3"
              onSubmit={(event) => {
                event.preventDefault();
                void operation("rehearsal", async () => {
                  const messages = rehearsal
                    .split("\n")
                    .map((line) => line.trim())
                    .filter(Boolean)
                    .map((text, index) => ({
                      text,
                      author_id: `rehearsal-${index + 1}`,
                    }));
                  await api(
                    `${audiencePath}/rehearsal`,
                    { method: "POST", body: JSON.stringify({ messages }) },
                    true,
                  );
                  await load();
                  setRehearsal("");
                  setNotice(
                    es
                      ? "Preguntas de ensayo procesadas."
                      : "Rehearsal questions processed.",
                  );
                });
              }}
            >
              <label
                htmlFor="audience-rehearsal"
                className="block text-xs leading-relaxed text-stone-600"
              >
                {es
                  ? "Escribe una pregunta por línea. Cada línea simula una persona distinta."
                  : "One question per line. Each line simulates a different participant."}
              </label>
              <textarea
                id="audience-rehearsal"
                value={rehearsal}
                onChange={(e) => setRehearsal(e.target.value)}
                rows={3}
                maxLength={8000}
                placeholder={
                  es
                    ? "¿Qué cambió en ese pase?"
                    : "What changed with that pass?"
                }
                className="mt-2 w-full rounded-lg border border-stone-300 p-2 text-sm"
              />
              <Button
                type="submit"
                disabled={!!busy || !rehearsal.trim()}
                className="mt-2"
              >
                {busy === "rehearsal"
                  ? es
                    ? "Procesando…"
                    : "Processing…"
                  : es
                    ? "Analizar ensayo"
                    : "Analyze rehearsal"}
              </Button>
            </form>
          </details>
          {audience?.source === "youtube" && (
            <Button
              disabled={!!busy}
              onClick={() =>
                void operation("refresh", async () => {
                  const result = await api<AudienceStatus>(
                    `${audiencePath}/refresh`,
                    { method: "POST" },
                    true,
                  );
                  setAudience(result);
                })
              }
            >
              {busy === "refresh"
                ? es
                  ? "Actualizando…"
                  : "Refreshing…"
                : es
                  ? "Actualizar chat"
                  : "Refresh chat"}
            </Button>
          )}
          {(error || audience?.error) && (
            <p
              role="alert"
              className="rounded-lg bg-red-50 p-3 text-sm text-red-800"
            >
              {error || audience?.error}
            </p>
          )}
          {notice && (
            <p role="status" className="text-sm text-emerald-800">
              {notice}
            </p>
          )}
          <div aria-live="polite" className="space-y-3">
            {!!pending.length && (
              <p className="text-xs leading-relaxed text-stone-500">
                {es
                  ? `Muestra de chat: últimos ${audience?.window_seconds ?? 90} s; no representa a toda la audiencia.`
                  : `Recent chat sample (${audience?.window_seconds ?? 90}s), not the full audience.`}
                {audience?.sample_limited &&
                  (es
                    ? ` La IA analizó los últimos 50 de ${audience.available_message_count} mensajes.`
                    : ` AI analyzed the latest 50 of ${audience.available_message_count} messages.`)}
              </p>
            )}
            {!pending.length && (
              <p className="text-sm text-stone-500">
                {es
                  ? "No hay preguntas pendientes."
                  : "No questions awaiting review."}
              </p>
            )}
            {pending.map((group) => {
              const story = storyFor(group);
              const chosenId = chosenStories[group.id] ?? group.story_id ?? "";
              const chosenStory = availableStories.find(
                (item) => item.id === chosenId,
              );
              const confirmed =
                group.association_confirmed && chosenId === group.story_id;
              const current =
                !!story &&
                !!match &&
                story.eligible_from_ms <= match.clock_ms &&
                story.expires_at_ms > match.clock_ms;
              const approved = story?.approved || story?.status === "approved";
              return (
                <article
                  key={group.id}
                  className="rounded-xl border border-stone-200 bg-white p-4"
                >
                  <div className="flex flex-wrap items-center gap-2 text-xs text-stone-600">
                    <Tag>{audienceModeLabel(group.mode, es)}</Tag>
                    <span>
                      {group.message_count} {es ? "mensajes" : "messages"} ·{" "}
                      {group.participant_count}{" "}
                      {es ? "participantes" : "participants"}
                    </span>
                    <span>
                      {es ? "Último mensaje" : "Last message"}{" "}
                      {new Date(group.last_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                  <div className="mt-3">
                    <p className="text-[11px] font-semibold uppercase text-stone-500">
                      {es ? "Mensaje original" : "Original chat message"}
                    </p>
                    <h3 className="mt-1 text-sm font-semibold leading-relaxed text-stone-900">
                      {group.question}
                    </h3>
                  </div>
                  <div className="mt-3 rounded-lg border border-emerald-100 bg-emerald-50/70 p-3">
                    <p className="text-[11px] font-semibold uppercase text-emerald-900">
                      {group.mode === "ai"
                        ? es
                          ? "Interpretación de la IA"
                          : "AI interpretation"
                        : es
                          ? "Criterio de agrupación"
                          : "Grouping note"}
                    </p>
                    <p className="mt-1 text-sm leading-relaxed text-stone-700">
                      {group.mode === "ai"
                        ? group.interpretation || group.reason
                        : group.reason}
                    </p>
                  </div>
                  {story && (
                    <>
                      <p className="mt-3 text-xs font-medium text-stone-600">
                        {group.association_confirmed
                          ? es
                            ? "Jugada confirmada"
                            : "Confirmed moment"
                          : es
                            ? "Posible jugada"
                            : "Suggested moment"}{" "}
                        · {story.titles?.[language] || story.title} ·{" "}
                        {timecode(
                          story.occurrence_ms ?? story.eligible_from_ms,
                        )}
                      </p>
                      <Draft
                        path={path}
                        group={group}
                        story={story}
                        language={language}
                      />
                    </>
                  )}
                  {!story && (
                    <p className="mt-3 text-xs text-amber-900">
                      {es
                        ? "Selecciona una historia en la cola; no hay una coincidencia actual inequívoca."
                        : "Select an insight in the queue; there is no unambiguous current match."}
                    </p>
                  )}
                  <label
                    htmlFor={`audience-story-${group.id}`}
                    className="mt-3 block text-xs font-medium text-stone-700"
                  >
                    {es
                      ? "Confirma la jugada a la que se refiere la pregunta"
                      : "Confirm the moment this question refers to"}
                  </label>
                  <select
                    id={`audience-story-${group.id}`}
                    value={chosenId}
                    onChange={(event) =>
                      setChosenStories((current) => ({
                        ...current,
                        [group.id]: event.target.value,
                      }))
                    }
                    className="mt-2 w-full rounded-lg border border-stone-300 bg-white p-2 text-sm"
                  >
                    <option value="">
                      {es ? "Seleccionar una historia" : "Select an insight"}
                    </option>
                    {availableStories.map((item) => (
                      <option
                        key={`${item.id}:${item.revision}`}
                        value={item.id}
                      >
                        {timecode(item.occurrence_ms ?? item.eligible_from_ms)}{" "}
                        · {item.titles?.[language] || item.title}
                      </option>
                    ))}
                  </select>
                  <p className="mt-2 text-xs leading-relaxed text-stone-500">
                    {es
                      ? "Comprueba el momento: el video de YouTube puede estar retrasado frente al partido."
                      : "Check the moment: the YouTube video may be delayed relative to the match."}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {chosenStory && !confirmed && (
                      <Button
                        disabled={!!busy}
                        onClick={() =>
                          void operation(`associate-${group.id}`, async () => {
                            await api(
                              `${audiencePath}/groups/${encodeURIComponent(group.id)}/associate`,
                              {
                                method: "POST",
                                body: JSON.stringify({
                                  story_id: chosenStory.id,
                                  expected_revision: chosenStory.revision,
                                  package_hash: chosenStory.package_hash,
                                }),
                              },
                              true,
                            );
                            await load();
                            onSelect(chosenStory.id);
                          })
                        }
                      >
                        {busy === `associate-${group.id}`
                          ? es
                            ? "Confirmando…"
                            : "Confirming…"
                          : es
                            ? "Confirmar jugada y revisar"
                            : "Confirm moment and review"}
                      </Button>
                    )}
                    {story && (
                      <Button onClick={() => onSelect(story.id)}>
                        {es
                          ? "Revisar historia y evidencia"
                          : "Review story and evidence"}
                      </Button>
                    )}
                    {story &&
                      approved &&
                      current &&
                      story.package_hash &&
                      confirmed && (
                        <Button
                          tone="primary"
                          disabled={!!busy}
                          onClick={() =>
                            void operation(`show-${group.id}`, async () => {
                              await api(
                                `${path}/selection`,
                                {
                                  method: "POST",
                                  body: JSON.stringify({
                                    story_id: story.id,
                                    expected_revision: story.revision,
                                    package_hash: story.package_hash,
                                    audience_group_id: group.id,
                                  }),
                                },
                                true,
                              );
                              await onRefresh();
                              setNotice(
                                es
                                  ? "Pregunta e historia aprobada seleccionadas para el overlay."
                                  : "Question and approved story selected for the overlay.",
                              );
                            })
                          }
                        >
                          {busy === `show-${group.id}`
                            ? es
                              ? "Seleccionando…"
                              : "Selecting…"
                            : es
                              ? "Mostrar pregunta e historia aprobada"
                              : "Show question and approved insight"}
                        </Button>
                      )}
                    <Button
                      disabled={!!busy}
                      onClick={() =>
                        void operation(`dismiss-${group.id}`, async () => {
                          await api(
                            `${audiencePath}/groups/${encodeURIComponent(group.id)}/dismiss`,
                            { method: "POST" },
                            true,
                          );
                          await load();
                        })
                      }
                    >
                      {es ? "Descartar" : "Dismiss"}
                    </Button>
                  </div>
                  {story && !approved && (
                    <p className="mt-2 text-xs text-stone-500">
                      {es
                        ? "Aprueba la historia antes de seleccionarla para emisión."
                        : "Approve the story before selecting it for broadcast."}
                    </p>
                  )}
                  {story && approved && !current && (
                    <p className="mt-2 text-xs text-stone-500">
                      {es
                        ? "La ventana de emisión de esta historia está cerrada."
                        : "This story's live display window has closed."}
                    </p>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      </details>
    </section>
  );
}
