"use client";

import { useCallback, useEffect, useState } from "react";
import { api, Match, Story, timecode, Variant } from "@/lib/api";
import { Button, Card, Tag } from "./ui";

type AudienceGroup = {
  id: string;
  question: string;
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
      <Card className="overflow-hidden">
        <div className="border-b border-stone-200 bg-stone-50/80 p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">
              {es ? "Audiencia de YouTube" : "YouTube audience"}
            </h2>
            <Tag>
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
          </div>
          <p className="mt-2 text-sm leading-relaxed text-stone-600">
            {es
              ? "Preguntas agrupadas para revisión. La audiencia no aprueba ni publica historias."
              : "Grouped questions for review. Audience messages cannot approve or publish stories."}
          </p>
        </div>
        <div className="space-y-4 p-5">
          <div className="flex flex-wrap items-center gap-3">
            <Button
              disabled={!!busy || !!audience?.youtube_authorized}
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
                : audience?.youtube_authorized
                  ? es ? "Cuenta de YouTube conectada" : "YouTube account connected"
                  : es ? "Autorizar YouTube Live" : "Authorize YouTube Live"}
            </Button>
            <span className="text-xs text-stone-500">
              {es
                ? "La cuenta se autoriza en Google; las credenciales permanecen en el servidor."
                : "Authorize through Google; credentials stay on the server."}
            </span>
          </div>
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
          <details className="rounded-lg border border-stone-200 p-3">
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
            {!!pending.length && <p className="text-xs leading-relaxed text-stone-500">{es ? `Preguntas observadas en una ventana de ${audience?.window_seconds ?? 90} segundos; los conteos no representan a toda la audiencia.` : `Questions observed in a ${audience?.window_seconds ?? 90}-second window; counts do not represent the entire audience.`}{audience?.sample_limited && (es ? ` Análisis limitado a los 50 mensajes más recientes de ${audience.available_message_count} disponibles.` : ` Analysis limited to the latest 50 of ${audience.available_message_count} available messages.`)}</p>}
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
                    <Tag>{modeLabel(group.mode, es)}</Tag>
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
                  <h3 className="mt-3 text-sm font-semibold leading-relaxed">
                    {group.question}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-stone-600">
                    {group.reason}
                  </p>
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
      </Card>
      <Card className="p-5">
        <h2 className="font-semibold">
          {es ? "Productor de emisión" : "Broadcast producer"}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-stone-600">
          {es
            ? "Pide una recomendación para la emisión actual. Tú decides qué revisar o mostrar."
            : "Request a recommendation for the current broadcast. You decide what to review or show."}
        </p>
        <Button
          className="mt-3"
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
            className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3"
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
    </section>
  );
}
