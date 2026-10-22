"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronRight,
  Clock3,
  Eye,
  FileCheck2,
  Globe2,
  Layers3,
  Pause,
  Play,
  Radio,
  RotateCcw,
  ScanLine,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  X,
} from "lucide-react";
import {
  api,
  cn,
  Evidence,
  Match,
  Recap,
  timecode,
  token,
  Variant,
} from "@/lib/api";
import { Button, Card, Tag } from "./ui";
import Pitch from "./pitch";
import { AudiencePanel, StoryPicker, relevantStories } from "./audience-panel";
import { useMatch } from "@/hooks/use-match";
import { useRenderAck } from "@/hooks/use-render-ack";
import { EvidenceReplay } from "./evidence-replay";
import { DecisionSummary } from "./decision-summary";
import { ReviewCard } from "./review-card";
import { AudienceControls } from "./audience-controls";
import { useAudiencePreferences } from "@/hooks/use-audience-preferences";
import { useStoryVariant } from "@/hooks/use-story-variant";

export default function MatchDesk({
  id,
  mode,
}: {
  id: string;
  mode: "studio" | "watch" | "overlay";
}) {
  const isProducer = mode === "studio";
  const [selectedStoryId, setSelectedStoryId] = useState("");
  const { match, error, connected, refresh } = useMatch(
    id,
    isProducer,
    selectedStoryId,
  );
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);
  const [diagnostics, setDiagnostics] = useState<Record<
    string,
    unknown
  > | null>(null);
  const { language, setLanguage, detail, setDetail, focus, setFocus } =
    useAudiencePreferences();
  const [recap, setRecap] = useState<Recap | null>(null);
  const [access, setAccess] = useState("");
  const story =
    selectedStoryId && match?.story?.id !== selectedStoryId
      ? null
      : match?.story;
  const stories = match?.stories || (match?.story ? [match.story] : []);
  const focusedStories = relevantStories(stories, focus);
  const audienceStory =
    focus && !focusedStories.some((item) => item.id === story?.id)
      ? null
      : story;
  const changeFocus = (next: string) => {
    setFocus(next);
    const relevant = relevantStories(stories, next);
    setSelectedStoryId(relevant.at(-1)?.id || "");
  };
  useEffect(() => {
    if (
      !isProducer &&
      focus &&
      story &&
      !focusedStories.some((item) => item.id === story.id) &&
      focusedStories.length
    )
      setSelectedStoryId(focusedStories.at(-1)!.id);
  }, [
    isProducer,
    focus,
    story?.id,
    focusedStories.map((item) => item.id).join(","),
  ]);
  const storyApproved = story?.approved ?? story?.status === "approved";
  const duration = match?.duration_ms || 60000;
  const liveApproved = stories
    .filter(
      (item) =>
        item.status === "approved" &&
        item.eligible_from_ms <= (match?.clock_ms || 0) &&
        item.expires_at_ms > (match?.clock_ms || 0),
    )
    .at(-1);
  const activeStory = useRef("");
  activeStory.current = story ? `${story.id}:${story.revision}` : "";
  const visibleEvidence =
    evidence &&
    story &&
    evidence.story.id === story.id &&
    evidence.story.revision === story.revision
      ? evidence
      : null;
  const [seekSeconds, setSeekSeconds] = useState("");
  useEffect(() => {
    setEvidence(null);
    setShowEvidence(false);
    setDiagnostics(null);
    setActionError("");
  }, [story?.id, story?.revision]);
  useEffect(() => {
    if (
      selectedStoryId &&
      match?.stories &&
      !match.stories.some((s) => s.id === selectedStoryId) &&
      match.story?.id !== selectedStoryId
    )
      setSelectedStoryId("");
  }, [selectedStoryId, match?.stories, match?.story?.id]);
  const workflowPending = match?.workflow_pending === true;
  const modelUsage = diagnostics?.model_usage as
    | {
        calls?: number;
        input_tokens?: number;
        output_tokens?: number;
        total_tokens?: number;
        usage_complete?: boolean;
      }
    | undefined;
  useEffect(
    () => setRecap(null),
    [story?.id, story?.revision, match?.story_status],
  );
  const recapContext = `${id}:${language}:${focus}:${stories.map((item) => `${item.id}:${item.revision}:${item.status}`).join(",")}`;
  const currentRecapContext = useRef(recapContext);
  currentRecapContext.current = recapContext;
  useEffect(() => setRecap(null), [recapContext]);
  const path = `/replay-sessions/${id}`;
  const visibleVariant = useStoryVariant(
    path,
    story,
    match?.story_status,
    language,
    detail,
    focus,
    isProducer,
  );
  useRenderAck(
    path,
    audienceStory,
    visibleVariant,
    !isProducer && mode === "watch" && !!storyApproved,
  );
  const loadEvidence = useCallback(async () => {
    if (!story) return;
    setActionError("");
    try {
      const requestStory = `${story.id}:${story.revision}`;
      const data = await api<Evidence>(
        `${path}/stories/${story.id}/evidence`,
        {},
        isProducer,
      );
      if (activeStory.current !== requestStory) return;
      setEvidence(data);
      setShowEvidence(true);
    } catch (e) {
      setActionError((e as Error).message);
    }
  }, [story?.id, story?.revision, path, isProducer]);
  useEffect(() => {
    if (isProducer || !audienceStory) return;
    let ignore = false;
    api<Evidence>(`${path}/stories/${audienceStory.id}/evidence`)
      .then((data) => {
        if (!ignore) setEvidence(data);
      })
      .catch(() => {
        if (!ignore) setEvidence(null);
      });
    return () => {
      ignore = true;
    };
  }, [isProducer, path, audienceStory?.id, audienceStory?.revision]);
  async function control(action: string, speed?: number, clock_ms?: number) {
    setActionError("");
    try {
      const data = await api<{ session_id: string }>(
        `${path}/control`,
        {
          method: "POST",
          body: JSON.stringify({
            action,
            ...(speed === undefined ? {} : { speed }),
            ...(clock_ms === undefined ? {} : { clock_ms }),
          }),
        },
        true,
      );
      if (action === "reset")
        window.location.href = `/studio/${data.session_id}`;
      else await refresh();
    } catch (e) {
      setActionError((e as Error).message);
    }
  }
  async function review(action: string, text?: string, angle?: string) {
    if (!story) return;
    setBusy(true);
    setActionError("");
    try {
      if (!story.package_hash)
        throw new Error("Refresh the story before reviewing");
      await api(
        `${path}/stories/${story.id}/review`,
        {
          method: "POST",
          body: JSON.stringify({
            action,
            expected_revision: story.revision,
            package_hash: story.package_hash,
            idempotency_key: crypto.randomUUID(),
            ...(text ? { text } : {}),
            ...(angle ? { angle } : {}),
          }),
        },
        true,
      );
      await refresh();
      const updated = await api<Evidence>(
        `${path}/stories/${story.id}/evidence`,
        {},
        true,
      );
      if (activeStory.current.split(":")[0] === story.id) setEvidence(updated);
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function catchUp() {
    const requestedContext = recapContext;
    setActionError("");
    try {
      const data = await api<Recap>(`${path}/recaps`, {
        method: "POST",
        body: JSON.stringify({ language, focus: focus || null }),
      });
      if (currentRecapContext.current === requestedContext) setRecap(data);
    } catch (e) {
      setActionError((e as Error).message);
    }
  }
  async function inspectDiagnostics() {
    const requestStory = activeStory.current;
    try {
      const data = await api<Record<string, unknown>>(
        `${path}/diagnostics${story ? `?story_id=${encodeURIComponent(story.id)}` : ""}`,
        {},
        true,
      );
      if (activeStory.current === requestStory) setDiagnostics(data);
    } catch (e) {
      setActionError((e as Error).message);
    }
  }
  if (mode === "overlay")
    return (
      <main className="flex min-h-dvh items-end bg-stone-950 p-8">
        <div className="max-w-3xl rounded-xl border-l-4 border-emerald-500 bg-white p-6">
          <p className="mb-2 text-xs font-semibold text-emerald-800">
            WHY/NOW · SYNTHETIC REPLAY ·{" "}
            {match ? timecode(match.clock_ms) : "CONNECTING"}
          </p>
          <p className="text-pretty text-2xl font-medium">
            {match?.overlay || "Waiting for an approved live story"}
          </p>
          <p className="mt-2 text-xs text-stone-500">
            {connected ? "Shared broadcast preview" : "Reconnecting…"}
          </p>
        </div>
      </main>
    );
  return (
    <div className="min-h-dvh lg:flex">
      {isProducer && (
        <aside className="hidden w-20 shrink-0 flex-col items-center gap-8 border-r border-stone-200 bg-white py-7 lg:flex">
          <Link
            href="/"
            aria-label="WHY/NOW home"
            className="flex size-10 items-center justify-center rounded-xl bg-stone-900 text-xl font-black text-white"
          >
            W<span className="text-emerald-400">/</span>
          </Link>
          <a
            href="#live"
            aria-label="Live match"
            className="rounded-xl bg-emerald-50 p-3 text-emerald-800"
          >
            <Radio size={20} />
          </a>
          <button
            onClick={() => void loadEvidence()}
            aria-label="Inspect evidence"
            className="p-3 text-stone-400 hover:text-stone-800"
          >
            <ScanLine size={20} />
          </button>
          <button
            onClick={inspectDiagnostics}
            aria-label="Open diagnostics"
            className="p-3 text-stone-400 hover:text-stone-800"
          >
            <Activity size={20} />
          </button>
          <Link
            href={`/watch/${id}`}
            target="_blank"
            aria-label="Open viewer companion"
            className="mt-auto p-3 text-stone-400 hover:text-stone-800"
          >
            <Eye size={20} />
          </Link>
        </aside>
      )}
      <div
        className={cn(
          "mx-auto w-full px-4 pb-12 md:px-8",
          isProducer ? "max-w-screen-2xl" : "max-w-7xl",
        )}
      >
        <header className="flex min-h-24 flex-wrap items-center justify-between gap-4 border-b border-stone-200 py-5">
          <div className="flex items-center gap-4">
            {!isProducer && (
              <Link href="/" className="text-xl font-black">
                WHY<span className="text-emerald-700">/</span>NOW
              </Link>
            )}
            <div
              className={cn(!isProducer && "border-l border-stone-300 pl-4")}
            >
              <p className="text-sm font-semibold">
                {isProducer
                  ? "Producer console"
                  : language === "es"
                    ? "Vista del espectador"
                    : "Viewer companion"}
              </p>
              <p className="mt-1 text-xs text-stone-400">
                {isProducer
                  ? "Live stories. Evidence in view."
                  : language === "es"
                    ? "Tu perspectiva del momento."
                    : "Your view of the moment."}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Tag
              className={
                connected
                  ? "bg-emerald-50 text-emerald-800"
                  : "bg-amber-50 text-amber-900"
              }
            >
              <span
                className={cn(
                  "size-1.5 rounded-full",
                  connected ? "bg-emerald-600" : "bg-amber-600",
                )}
              />
              {connected
                ? language === "es"
                  ? "Conectado"
                  : "Connected"
                : language === "es"
                  ? "Reconectando"
                  : "Reconnecting"}
            </Tag>
            {isProducer && (
              <Link
                href={`/watch/${id}`}
                target="_blank"
                className="inline-flex items-center gap-2 rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm"
              >
                Viewer companion
                <ArrowUpRight size={15} />
              </Link>
            )}
          </div>
        </header>
        {error && (
          <Card className="my-5 p-5">
            <p role="alert" className="text-sm text-red-700">
              {error}
            </p>
            {isProducer && error.includes("auth") && (
              <div className="mt-3 flex flex-wrap gap-2">
                <label className="sr-only" htmlFor="producer-key">
                  Producer access key
                </label>
                <input
                  id="producer-key"
                  type="password"
                  value={access}
                  onChange={(e) => setAccess(e.target.value)}
                  placeholder="Producer access key"
                  className="rounded-lg border border-stone-200 p-2"
                />
                <Button
                  onClick={() => {
                    sessionStorage.setItem("why-now-token", access);
                    void refresh();
                  }}
                >
                  Connect
                </Button>
              </div>
            )}
          </Card>
        )}
        <div className="flex flex-wrap items-end justify-between gap-3 py-4">
          <div>
            <div className="mb-2 flex items-center gap-2 text-xs text-stone-500">
              <span>
                {language === "es" ? "SESIÓN" : "SESSION"}{" "}
                {id.slice(0, 8).toUpperCase()}
              </span>
              <ChevronRight size={12} />
              <span>
                {language === "es"
                  ? `Segmento de ${duration / 1000} segundos`
                  : `${duration / 1000}-second segment`}
              </span>
            </div>
            <h1 className="text-balance text-2xl font-semibold md:text-3xl">
              Harbor City <span className="font-normal text-stone-400">vs</span>{" "}
              Alder Rovers
            </h1>
          </div>
          <Tag className="bg-stone-200/70">
            <Layers3 size={12} />
            {language === "es" ? "Datos sintéticos" : "Synthetic data"}
          </Tag>
        </div>
        {actionError && (
          <p
            role="alert"
            className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
          >
            {actionError}
          </p>
        )}
        {workflowPending && (
          <div
            role="status"
            aria-live="polite"
            className="mb-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4"
          >
            <p className="flex items-center gap-2 text-sm font-semibold text-emerald-900">
              <ShieldCheck size={16} />
              AI review in progress
            </p>
            <p className="mt-2 text-pretty text-sm text-emerald-900">
              A supported sequence is being reviewed before an explanation is
              offered for producer approval. The replay can continue.
            </p>
            <p className="mt-2 text-xs text-emerald-800">{match?.mode}</p>
          </div>
        )}
        <div
          className={cn(
            "grid items-start gap-6",
            isProducer ? "xl:grid-cols-3" : "lg:grid-cols-2",
          )}
        >
          <div
            id="live"
            tabIndex={-1}
            aria-label={
              language === "es" ? "Repetición en directo" : "Live replay"
            }
            className={cn("min-w-0", isProducer && "xl:col-span-2")}
          >
            <section className="overflow-hidden rounded-2xl border border-emerald-950 bg-emerald-950 text-white">
              <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                <div className="flex items-center gap-3 text-sm font-semibold">
                  <span className="size-2 rounded-full bg-blue-400" />
                  HBC
                  <span className="rounded-md bg-white/10 px-3 py-1 tabular-nums">
                    0 : 0
                  </span>
                  ALD
                  <span className="size-2 rounded-full bg-amber-400" />
                </div>
                <span className="flex items-center gap-2 text-xs text-emerald-200">
                  <span className="rounded bg-white/10 px-2 py-1 font-mono tabular-nums">
                    {timecode(match?.clock_ms || 0)}
                  </span>
                  {match?.running
                    ? language === "es"
                      ? "REPETICIÓN EN CURSO"
                      : "REPLAY RUNNING"
                    : (match?.clock_ms || 0) >= duration
                      ? language === "es"
                        ? "SEGMENTO COMPLETO"
                        : "SEGMENT COMPLETE"
                      : language === "es"
                        ? "REPETICIÓN PAUSADA"
                        : "REPLAY PAUSED"}
                  {match?.speed !== 1 && <span>{match?.speed}×</span>}
                </span>
              </div>
              <Pitch frame={match?.frame || null} language={language} />
              <div className="border-t border-white/10 px-5 py-4">
                <div className="mb-2 flex items-center gap-2 text-xs font-medium text-emerald-200">
                  <Radio size={12} />
                  {language === "es"
                    ? "TEXTO COMPARTIDO DE LA TRANSMISIÓN"
                    : "SHARED BROADCAST OVERLAY"}
                </div>
                {match?.overlay ? (
                  <p className="max-w-xl text-pretty text-base leading-relaxed">
                    {match.overlay}
                  </p>
                ) : (
                  <p className="text-sm text-emerald-200/70">
                    {story && match?.story_status === "expired"
                      ? language === "es"
                        ? "Terminó el intervalo en pantalla. El momento aprobado sigue disponible en el historial."
                        : "Display interval ended. The approved moment remains available in the companion."
                      : language === "es"
                        ? "Las historias aprobadas aparecen aquí durante su intervalo de repetición."
                        : "Approved stories appear here at their eligible replay time."}
                  </p>
                )}
              </div>
            </section>
            {isProducer && (
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-stone-200 bg-white p-3">
                <div className="flex items-center gap-2">
                  <Button
                    disabled={!match || match.clock_ms >= duration}
                    onClick={() =>
                      void control(match?.running ? "pause" : "start")
                    }
                    className="px-3"
                  >
                    {match?.running ? <Pause size={15} /> : <Play size={15} />}{" "}
                    {match?.running ? "Pause" : "Play"}
                  </Button>
                  <label htmlFor="speed" className="sr-only">
                    Replay speed
                  </label>
                  <select
                    id="speed"
                    value={match?.speed || 1}
                    onChange={(e) =>
                      void control("speed", Number(e.target.value))
                    }
                    className="min-h-10 rounded-lg border border-stone-200 px-2 text-sm"
                  >
                    <option value="0.5">0.5×</option>
                    <option value="1">1×</option>
                    <option value="2">2×</option>
                    <option value="4">4×</option>
                    <option value="8">8×</option>
                  </select>
                  <Button
                    onClick={() => void control("reset")}
                    className="border-transparent px-3"
                  >
                    <RotateCcw size={14} />
                    New replay
                  </Button>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <label
                    htmlFor="jump-seconds"
                    className="text-xs text-stone-500"
                  >
                    Jump to second
                  </label>
                  <input
                    id="jump-seconds"
                    type="number"
                    min={Math.ceil((match?.clock_ms || 0) / 1000)}
                    max={duration / 1000}
                    step="1"
                    value={seekSeconds}
                    onChange={(e) => setSeekSeconds(e.target.value)}
                    className="min-h-10 w-20 rounded-lg border border-stone-200 px-2 text-sm"
                  />
                  <Button
                    disabled={
                      !seekSeconds ||
                      Number(seekSeconds) * 1000 < (match?.clock_ms || 0) ||
                      Number(seekSeconds) * 1000 > duration
                    }
                    onClick={() =>
                      void control(
                        "seek",
                        undefined,
                        Math.round(Number(seekSeconds) * 1000),
                      )
                    }
                  >
                    Jump forward
                  </Button>
                </div>
                <span className="pr-2 text-xs tabular-nums text-stone-400">
                  {match?.delivered_count || 0} observations delivered
                </span>
              </div>
            )}

            {showEvidence && visibleEvidence && (
              <EvidenceReplay
                data={visibleEvidence}
                language={language}
                onClose={() => setShowEvidence(false)}
                focus={focus}
              />
            )}
            {recap && (
              <Card className="mt-6 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <Tag>
                      <Clock3 size={12} />
                      Through {timecode(recap.through_ms)}
                    </Tag>
                    <h2 className="mt-3 text-xl font-semibold">
                      {recap.title}
                    </h2>
                  </div>
                  <button
                    aria-label="Close recap"
                    onClick={() => setRecap(null)}
                    className="p-2"
                  >
                    <X size={18} />
                  </button>
                </div>
                {recap.moments.length ? (
                  recap.moments.map((m) => (
                    <article
                      lang={language}
                      key={`${m.story_id}-${m.revision}`}
                      className="mt-4 border-l-2 border-emerald-600 pl-4"
                    >
                      <p className="text-xs tabular-nums text-stone-500">
                        {timecode(m.at_ms)} ·{" "}
                        {m.archived
                          ? language === "es"
                            ? "Aprobado · archivo"
                            : "Approved · archived"
                          : language === "es"
                            ? "Aprobado"
                            : "Approved"}
                      </p>
                      <h3 className="mt-1 font-semibold">{m.title}</h3>
                      <p className="mt-2 text-pretty leading-relaxed text-stone-600">
                        {m.text}
                      </p>
                      <Button
                        className="mt-2"
                        onClick={() => {
                          setSelectedStoryId(m.story_id);
                          setRecap(null);
                        }}
                      >
                        {language === "es" ? "Abrir momento" : "Open moment"}
                      </Button>
                      {m.similar_moments.length > 1 && (
                        <details className="mt-2 text-sm">
                          <summary>
                            {m.similar_moments.length}{" "}
                            {language === "es"
                              ? "momentos aprobados similares"
                              : "similar approved moments"}
                          </summary>
                          <p className="mt-2 text-xs text-stone-500">
                            {language === "es"
                              ? "La similitud no demuestra una tendencia."
                              : "Similarity does not establish a trend."}
                          </p>
                          {m.similar_moments.map((member) => (
                            <Button
                              key={member.story_id}
                              className="mr-2 mt-2"
                              onClick={() => {
                                setSelectedStoryId(member.story_id);
                                setRecap(null);
                              }}
                            >
                              {timecode(member.at_ms)} · {member.story_id}
                            </Button>
                          ))}
                        </details>
                      )}
                    </article>
                  ))
                ) : (
                  <p className="mt-4 text-sm text-stone-500">
                    {language === "es"
                      ? "No hay momentos aprobados para este enfoque."
                      : "No approved moments are available for this focus."}
                  </p>
                )}
                <p className="mt-4 text-xs text-stone-400">
                  {language === "es"
                    ? "Solo revisiones aprobadas · todos los momentos en el historial"
                    : "Approved revisions only · all moments remain in history"}
                </p>
                <Button className="mt-3" onClick={catchUp}>
                  {language === "es" ? "Actualizar resumen" : "Refresh recap"}
                </Button>
              </Card>
            )}
          </div>
          {!isProducer && (
            <aside className="order-first min-w-0 lg:order-last">
              <AudiencePanel
                story={audienceStory}
                stories={focusedStories}
                variant={audienceStory ? visibleVariant : null}
                evidence={audienceStory ? visibleEvidence : null}
                language={language}
                detail={detail}
                focus={focus}
                workflowPending={workflowPending}
                overlayId={match?.overlay_story_id || liveApproved?.id}
                onSelect={setSelectedStoryId}
                onEvidence={() => void loadEvidence()}
                onRecap={() => void catchUp()}
                onWholePlay={() => changeFocus("")}
                viewingEarlier={
                  !!selectedStoryId &&
                  !!audienceStory &&
                  audienceStory.id !==
                    (match?.overlay_story_id || liveApproved?.id)
                }
                onReturnLive={() => {
                  setFocus("");
                  setSelectedStoryId("");
                  setShowEvidence(false);
                  document
                    .getElementById("live")
                    ?.scrollIntoView({ block: "start" });
                  document
                    .getElementById("live")
                    ?.focus({ preventScroll: true });
                }}
                controls={
                  <AudienceControls
                    language={language}
                    detail={detail}
                    focus={focus}
                    players={match?.players || []}
                    setLanguage={setLanguage}
                    setDetail={setDetail}
                    setFocus={changeFocus}
                  />
                }
              />
            </aside>
          )}
          {isProducer && (
            <aside className="order-first space-y-5 xl:order-last">
              <Card className="overflow-hidden">
                <div className="flex items-center justify-between border-b border-stone-100 p-5">
                  <h2 className="flex items-center gap-2 font-semibold">
                    <Layers3 size={16} />
                    Story queue
                  </h2>
                  <Tag>
                    {stories.length
                      ? `${stories.length} ${stories.length === 1 ? "moment" : "moments"}`
                      : "Watching"}
                  </Tag>
                </div>
                {stories.length > 0 && (
                  <StoryPicker
                    stories={stories}
                    selected={story?.id || ""}
                    onSelect={setSelectedStoryId}
                    producer
                  />
                )}
                {story ? (
                  <div className="p-5">
                    <Tag
                      className={
                        match?.story_status === "approved"
                          ? "bg-emerald-50 text-emerald-800"
                          : ""
                      }
                    >
                      <ShieldCheck size={12} />
                      {storyApproved
                        ? match?.overlay &&
                          (match?.overlay_story_id || liveApproved?.id) ===
                            story.id
                          ? "On air"
                          : match?.story_status === "expired"
                            ? "Approved · archived"
                            : "Approved"
                        : match?.story_status}{" "}
                      · revision {story.revision}
                    </Tag>
                    <h3 className="mt-4 text-balance text-2xl font-semibold leading-tight">
                      {story.title}
                    </h3>
                    <p className="mt-3 text-pretty text-sm leading-relaxed text-stone-500">
                      {visibleVariant?.text ||
                        "Loading the supported explanation…"}
                    </p>
                    <Button
                      onClick={() => void loadEvidence()}
                      className="mt-5 w-full"
                    >
                      <ScanLine size={15} />
                      Show why
                      <ArrowRight size={15} />
                    </Button>
                    <div className="my-5 border-t border-stone-100" />
                    <div className="flex items-start gap-2 text-xs leading-relaxed text-stone-500">
                      <FileCheck2
                        size={15}
                        className="mt-0.5 shrink-0 text-emerald-700"
                      />
                      {match?.mode?.includes("local")
                        ? "Local factual template reviewed."
                        : "Evidence review completed."}{" "}
                      Inspect the evidence before approving.
                    </div>
                    <div className="mt-5 flex gap-2">
                      <Button
                        tone="primary"
                        className="flex-1"
                        disabled={
                          busy ||
                          ["expired", "approved"].includes(
                            match?.story_status || "",
                          )
                        }
                        onClick={() => void review("approve")}
                      >
                        <Check size={15} />
                        Approve
                      </Button>
                      <Button
                        disabled={
                          busy ||
                          (match?.story_status === "expired" && !storyApproved)
                        }
                        onClick={() =>
                          void review(storyApproved ? "retract" : "suppress")
                        }
                      >
                        {storyApproved ? "Retract" : "Suppress"}
                      </Button>
                    </div>
                    <p className="mt-3 text-xs tabular-nums text-stone-400">
                      Display ends at {timecode(story.expires_at_ms)} · replay
                      time
                    </p>
                  </div>
                ) : (
                  <div className="p-6">
                    <div className="my-6 flex size-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-800">
                      <ScanLine size={24} />
                    </div>
                    <h3 className="text-balance text-xl font-semibold">
                      {workflowPending
                        ? "AI review in progress"
                        : "Let the play tell its story."}
                    </h3>
                    <p className="mt-3 text-pretty text-sm leading-relaxed text-stone-500">
                      A candidate appears only when pressure, a pass beyond
                      opponents, and retained progression are supported by
                      delivered evidence.
                    </p>
                    <div className="mt-6 space-y-4 text-xs text-stone-500">
                      {[
                        "Count nearby opponents before release",
                        "Inspect the pass and longitudinal positions",
                        "Confirm possession and progression",
                      ].map((text, i) => (
                        <div className="flex items-center gap-3" key={text}>
                          <span className="flex size-5 items-center justify-center rounded-full bg-stone-100 tabular-nums">
                            {i + 1}
                          </span>
                          {text}
                        </div>
                      ))}
                    </div>
                    <p className="mt-6 border-t border-stone-100 pt-4 text-xs text-stone-400">
                      {workflowPending
                        ? "Evidence is ready. The AI workflow is checking the explanation; approval becomes available after review."
                        : match?.running
                          ? "Processing the replay. Some sequences correctly stay quiet."
                          : "Press Play to begin the synthetic segment."}
                    </p>
                  </div>
                )}
              </Card>
              {visibleEvidence && story && (
                <ReviewCard
                  key={story.id}
                  data={visibleEvidence}
                  busy={busy}
                  onEdit={(text, angle) => void review("edit", text, angle)}
                />
              )}
              <Card className="p-5">
                <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
                  <Eye size={16} />
                  Audience package
                </div>
                <p className="text-pretty text-sm leading-relaxed text-stone-500">
                  Approved moments. Different ways to understand them.
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Tag>Simple</Tag>
                  <Tag>Detailed</Tag>
                  <Tag>English / Español</Tag>
                  <Tag>Player focus</Tag>
                </div>
                <Link
                  href={`/watch/${id}`}
                  target="_blank"
                  className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-emerald-800"
                >
                  Open companion
                  <ArrowUpRight size={14} />
                </Link>
              </Card>
              <button
                onClick={inspectDiagnostics}
                className="flex w-full items-center justify-between px-2 py-2 text-xs text-stone-500"
              >
                <span className="flex items-center gap-2">
                  <Activity size={14} />
                  Processing & review trace
                </span>
                <ChevronRight size={14} />
              </button>
            </aside>
          )}
        </div>
        {diagnostics && (
          <Card className="mt-6 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                Processing & review trace
              </h2>
              <button
                aria-label="Close diagnostics"
                onClick={() => setDiagnostics(null)}
                className="p-2"
              >
                <X size={18} />
              </button>
            </div>
            <DecisionSummary
              summary={
                diagnostics.decision_summary as Parameters<
                  typeof DecisionSummary
                >[0]["summary"]
              }
            />
            <details className="mt-5">
              <summary className="text-sm font-medium">
                Technical calls, timing and usage
              </summary>
              <div className="my-5 grid gap-3 text-sm sm:grid-cols-3">
                <div className="rounded-xl bg-stone-50 p-4">
                  <p className="text-xs text-stone-500">Workflow processing</p>
                  <p className="mt-2 font-mono tabular-nums">
                    {String(diagnostics.workflow_ms ?? "—")} ms
                  </p>
                </div>
                <div className="rounded-xl bg-stone-50 p-4">
                  <p className="text-xs text-stone-500">
                    Delivered observations
                  </p>
                  <p className="mt-2 font-mono tabular-nums">
                    {String(diagnostics.observations_delivered)}
                  </p>
                </div>
                <div className="rounded-xl bg-stone-50 p-4">
                  <p className="text-xs text-stone-500">Execution mode</p>
                  <p className="mt-2">
                    {String(diagnostics.mode ?? "Unknown")} ·{" "}
                    {String(
                      diagnostics.model_calls ?? modelUsage?.calls ?? "—",
                    )}{" "}
                    model calls
                    {(diagnostics.model_tokens ?? modelUsage?.total_tokens) !=
                    null
                      ? ` · ${String(diagnostics.model_tokens ?? modelUsage?.total_tokens)} tokens`
                      : ""}
                  </p>
                </div>
              </div>
              <div className="space-y-3">
                {(
                  (diagnostics.trace ?? []) as {
                    role: string;
                    action: string;
                    status: string;
                    elapsed_ms: number;
                  }[]
                ).map((t, i) => (
                  <div
                    key={i}
                    className="flex flex-wrap justify-between gap-2 border-t border-stone-100 pt-3 text-sm"
                  >
                    <span className="font-medium">{t.role}</span>
                    <span className="text-stone-500">
                      {t.action.replaceAll("_", " ")}
                    </span>
                    <Tag>
                      {t.status} · {t.elapsed_ms} ms
                    </Tag>
                  </div>
                ))}
              </div>
              <p className="mt-5 text-xs text-stone-400">
                Workflow timing excludes replay waiting and human approval.{" "}
                {diagnostics.azure_deployed
                  ? "Running on Azure."
                  : "Running locally."}{" "}
                Usage includes attempted model calls.
                {modelUsage?.usage_complete === false
                  ? " Token totals are incomplete because the provider did not return usage for every attempt."
                  : ""}
                {modelUsage?.input_tokens != null
                  ? ` Input: ${modelUsage.input_tokens} tokens. Output: ${modelUsage.output_tokens ?? "unavailable"} tokens.`
                  : ""}
              </p>
            </details>
          </Card>
        )}
        <footer className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-stone-200 pt-5 text-xs text-stone-400">
          <span>
            {language === "es"
              ? "WHY/NOW · Mira la jugada. Entiende el momento."
              : "WHY/NOW · See the play. Understand the moment."}
          </span>
          <span>
            {language === "es"
              ? "Identidades ficticias · Datos sintéticos originales"
              : "Fictional identities · Original synthetic data"}{" "}
            · {match?.mode || "Connecting"}
          </span>
        </footer>
      </div>
    </div>
  );
}
