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
import { api, cn, Evidence, Match, timecode, token, Variant } from "@/lib/api";
import { Button, Card, Tag } from "./ui";
import { MatchStage } from "./match-stage";
import { AudiencePanel, StoryPicker, relevantStories } from "./audience-panel";
import { useMatch } from "@/hooks/use-match";
import { useRenderAck } from "@/hooks/use-render-ack";
import { EvidenceReplay } from "./evidence-replay";
import { AudiencePreview } from "./audience-preview";
import { CatchUpPanel } from "./catch-up-panel";
import { useViewerVisit } from "@/hooks/use-viewer-visit";
import { ReviewCard } from "./review-card";
import { DecisionSummary } from "./decision-summary";
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
  const [guidedPauses, setGuidedPauses] = useState(true);
  const [guidedNotice, setGuidedNotice] = useState("");
  const guidedFamilies = useRef(new Set<string>());
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);
  const evidencePanel = useRef<HTMLDivElement>(null);
  const [diagnostics, setDiagnostics] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [diagnosticsLoading, setDiagnosticsLoading] = useState(false);
  const diagnosticsHeading = useRef<HTMLHeadingElement>(null);
  const { language, setLanguage, detail, setDetail, focus, setFocus } =
    useAudiencePreferences();
  const [recapOpen, setRecapOpen] = useState(false);
  const [viewerDisplay, setViewerDisplay] = useState("match");
  const recapPanel = useRef<HTMLDivElement>(null);
  const visit = useViewerVisit(id, match?.clock_ms, !isProducer);
  const quietViewer =
    !isProducer && match?.session_mode === "live" && viewerDisplay === "match";
  useEffect(() => {
    if (recapOpen) recapPanel.current?.scrollIntoView({ block: "start" });
  }, [recapOpen]);
  useEffect(() => {
    if (diagnostics) {
      diagnosticsHeading.current?.scrollIntoView({ block: "start" });
      diagnosticsHeading.current?.focus({ preventScroll: true });
    }
  }, [diagnostics]);
  const [access, setAccess] = useState("");
  const story =
    selectedStoryId && match?.story?.id !== selectedStoryId
      ? null
      : match?.story;
  const stories = match?.stories || (match?.story ? [match.story] : []);
  const focusedStories = relevantStories(stories, focus);
  const storyMatchesFocus =
    !focus ||
    relevantStories(story ? [story] : [], focus).some(
      (item) => item.id === story?.id,
    );
  const audienceStory = storyMatchesFocus ? story : null;
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
      !storyMatchesFocus &&
      focusedStories.length
    )
      setSelectedStoryId(focusedStories.at(-1)!.id);
  }, [
    isProducer,
    focus,
    story?.id,
    focusedStories.map((item) => item.id).join(","),
    storyMatchesFocus,
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
  useEffect(() => {
    if (showEvidence && visibleEvidence) {
      evidencePanel.current?.scrollIntoView({ block: "start" });
      evidencePanel.current?.focus({ preventScroll: true });
    }
  }, [
    showEvidence,
    visibleEvidence?.story.id,
    visibleEvidence?.story.revision,
  ]);
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
      !match.stories.some(
        (s) =>
          s.id === selectedStoryId ||
          s.related_stories?.some((related) => related.id === selectedStoryId),
      ) &&
      match.story?.id !== selectedStoryId
    )
      setSelectedStoryId("");
  }, [selectedStoryId, match?.stories, match?.story?.id]);
  // Pin the first available producer story; arriving candidates never replace
  // the evidence being read. Explicit selection and revision guards still apply.
  useEffect(() => {
    if (isProducer && !selectedStoryId && match?.story?.id)
      setSelectedStoryId(match.story.id);
  }, [isProducer, selectedStoryId, match?.story?.id]);
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
  const recapContext = `${id}:${language}:${focus}:${stories.map((item) => `${item.id}:${item.revision}:${item.status}`).join(",")}`;
  const correctionContext = (match?.corrections || [])
    .map((n) => n.notice_id)
    .join(",");
  const path = `/replay-sessions/${id}`;
  const visibleVariant = useStoryVariant(
    path,
    quietViewer ? null : story,
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
    !isProducer && !quietViewer && mode === "watch" && !!storyApproved,
  );
  const loadEvidence = useCallback(async () => {
    if (!story) return;
    setActionError("");
    setSelectedStoryId(story.id);
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
    if (isProducer || quietViewer || !audienceStory) return;
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
  }, [
    isProducer,
    quietViewer,
    path,
    audienceStory?.id,
    audienceStory?.revision,
  ]);
  async function control(action: string, speed?: number, clock_ms?: number) {
    setActionError("");
    if (action === "start") setGuidedNotice("");
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
  useEffect(() => {
    if (!isProducer || !match?.guided_demo || !guidedPauses || !match.running)
      return;
    const next = stories.find(
      (item) =>
        !item.approved &&
        item.status === "ready" &&
        item.eligible_from_ms <= match.clock_ms &&
        item.expires_at_ms > match.clock_ms &&
        !guidedFamilies.current.has(item.family || "pass") &&
        (item.family !== "pressure" || item.notable) &&
        (!match.flagship_demo ||
          item.family !== "recovery" ||
          match.clock_ms >=
            (item.occurrence_ms ?? item.eligible_from_ms) + 3000) &&
        (item.family !== "possession" || item.eligible_from_ms >= 60000),
    );
    if (!next) return;
    const family = next.family || "pass";
    guidedFamilies.current.add(family);
    setSelectedStoryId(next.id);
    setGuidedNotice(
      `Paused for review: ${family === "recovery" ? "change of control" : family}. Inspect the evidence, approve or skip, then press Play to continue.`,
    );
    void control("pause");
  }, [
    isProducer,
    match?.guided_demo,
    match?.running,
    match?.clock_ms,
    stories,
    guidedPauses,
  ]);

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
  function catchUp() {
    setRecapOpen(true);
  }
  async function inspectDiagnostics() {
    const requestStory = activeStory.current;
    setDiagnosticsLoading(true);
    try {
      const data = await api<Record<string, unknown>>(
        `${path}/diagnostics${story ? `?story_id=${encodeURIComponent(story.id)}` : ""}`,
        {},
        true,
      );
      if (activeStory.current === requestStory) setDiagnostics(data);
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setDiagnosticsLoading(false);
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
                {language === "es"
                  ? `Demo de ${duration / 60000} minutos`
                  : `${duration / 60000}-minute ${match?.session_mode === "live" ? "live simulation" : "demo replay"}`}
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
        {isProducer && (
          <div
            role="status"
            aria-live="polite"
            data-testid="review-status"
            className="mb-5 flex h-16 items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 text-sm text-emerald-900"
          >
            <ShieldCheck size={18} className="shrink-0" />
            <p>
              <strong className="block">
                {workflowPending
                  ? "AI review in progress"
                  : "Producer review desk"}
              </strong>
              <span className="text-xs">
                {workflowPending
                  ? "Checking a new explanation. Keep reviewing your selected insight."
                  : "New insights arrive in the queue. Your selected insight stays in view."}
              </span>
            </p>
          </div>
        )}
        <div
          className={cn(
            "grid items-start gap-6",
            isProducer
              ? "lg:grid-cols-3"
              : quietViewer
                ? "grid-cols-1"
                : "lg:grid-cols-2",
          )}
        >
          <div
            id="live"
            tabIndex={-1}
            aria-label={
              language === "es" ? "Repetición en directo" : "Live replay"
            }
            className={cn("min-w-0", isProducer && "lg:col-span-2")}
          >
            {isProducer && match?.session_mode !== "live" && (
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-stone-200 bg-white p-3">
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
                <details className="text-sm text-stone-600">
                  <summary className="flex min-h-11 cursor-pointer items-center">
                    Replay navigation
                  </summary>
                  <div className="flex flex-wrap items-center gap-2 py-2">
                    <label
                      htmlFor="jump-seconds"
                      className="text-xs text-stone-500"
                    >
                      Skip to time (seconds)
                    </label>
                    <input
                      id="jump-seconds"
                      type="number"
                      min={Math.ceil((match?.clock_ms || 0) / 1000)}
                      max={duration / 1000}
                      step="1"
                      placeholder="e.g. 90"
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
                      Skip forward
                    </Button>
                  </div>
                  <p className="max-w-sm pb-2 text-xs leading-relaxed">
                    Enter seconds from the start: 90 means 01:30. Skipping
                    pauses the replay at that time.
                  </p>
                </details>
                <details className="text-xs text-stone-500">
                  <summary className="flex min-h-11 items-center">
                    Replay data details
                  </summary>
                  <p className="max-w-sm pb-2 leading-relaxed">
                    Session reference: {id}.<br />
                    {match?.score && (
                      <>
                        {language === "es"
                          ? "El marcador refleja eventos confirmados del partido."
                          : "The score reflects confirmed match events."}
                        <br />
                      </>
                    )}
                    <span className="tabular-nums">
                      {match?.delivered_count || 0} observations delivered.
                    </span>{" "}
                    These are position samples and source records, not a count
                    of football incidents. Suggested insights appear in the
                    review queue.
                  </p>
                </details>
              </div>
            )}

            {match?.session_mode === "live" && (
              <div className="mb-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
                <p className="font-semibold">
                  {["complete", "stopped"].includes(match.live_status || "")
                    ? language === "es"
                      ? "Simulación finalizada"
                      : "Simulation ended"
                    : match.live_status === "ai_unavailable"
                      ? language === "es"
                        ? "Conexión de IA no disponible"
                        : "AI connection unavailable"
                      : language === "es"
                        ? "Partido simulado en directo · continuo a 1×"
                        : "Simulated live match · continuous 1×"}
                </p>
                <p className={isProducer ? "mt-2" : "mt-1 text-xs"}>
                  {match.execution === "ai"
                    ? match.mode.includes("fallback")
                      ? language === "es"
                        ? "Alternativa factual tras fallar la IA"
                        : "AI unavailable · factual fallback"
                      : language === "es"
                        ? "Explicaciones asistidas por IA"
                        : "AI-assisted explanations"
                    : language === "es"
                      ? "Vista previa con plantillas · sin llamadas de IA"
                      : "Template preview · no AI calls"}
                  .{" "}
                  {isProducer &&
                    (["complete", "stopped"].includes(match.live_status || "")
                      ? "Review approved insights and catch up on this segment."
                      : "The match continues during evidence review. Only producer-approved explanations reach fans.")}
                </p>
                {isProducer && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button onClick={() => void control("reset")}>
                      New simulation
                    </Button>
                    {match.running && (
                      <Button onClick={() => void control("stop")}>
                        End simulation
                      </Button>
                    )}
                    {["complete", "stopped"].includes(
                      match.live_status || "",
                    ) && (
                      <Button onClick={() => void catchUp()}>
                        Open segment recap
                      </Button>
                    )}
                  </div>
                )}
                {isProducer && (
                  <details className="mt-3">
                    <summary className="cursor-pointer">
                      Session details
                    </summary>
                    <p className="mt-2 break-all">
                      Session reference: {id}. Model:{" "}
                      {match.model_identity?.deployment || "none"}
                      {match.model_identity?.version
                        ? ` · ${match.model_identity.version}`
                        : ""}
                      .
                    </p>
                  </details>
                )}
              </div>
            )}
            {isProducer && match?.session_mode !== "live" && (
              <p role="status" className="mb-3 text-sm text-stone-600">
                {(match?.clock_ms || 0) >= duration
                  ? "Replay complete. Review the remaining insights, open the recap, or choose New replay to start again."
                  : "This replay ends at " +
                    timecode(duration) +
                    ". With guided pauses off, playback continues while suggested insights arrive. It will stop at the end."}
              </p>
            )}
            {isProducer && match?.guided_demo && (
              <div className="mb-3 rounded-xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-950">
                <label className="flex min-h-11 items-center gap-3 font-semibold">
                  <input
                    type="checkbox"
                    checked={guidedPauses}
                    onChange={(e) => setGuidedPauses(e.target.checked)}
                    className="size-4"
                  />
                  Pause at new event types
                </label>
                <p className="mt-1 text-xs leading-relaxed">
                  Play the segment → inspect a moment’s evidence → approve it
                  for viewers. Guided pauses stop at the first example of each
                  event type; turn them off for continuous playback.
                </p>
                {guidedNotice && (
                  <div className="mt-3">
                    <p role="status" className="font-medium">
                      {guidedNotice}
                    </p>
                    <Button
                      className="mt-3"
                      onClick={() => {
                        document
                          .getElementById("story-queue")
                          ?.scrollIntoView({ block: "start" });
                        document
                          .getElementById("story-queue")
                          ?.focus({ preventScroll: true });
                      }}
                    >
                      Review paused moment
                    </Button>
                  </div>
                )}
              </div>
            )}
            {!isProducer && match?.session_mode === "live" && (
              <div
                className="mb-4 flex flex-wrap items-center justify-between gap-3"
                aria-label={
                  language === "es" ? "Vista del partido" : "Match viewing mode"
                }
              >
                <div className="flex flex-wrap gap-2">
                  <Button
                    aria-pressed={quietViewer}
                    tone={quietViewer ? "primary" : "secondary"}
                    onClick={() => {
                      setViewerDisplay("match");
                      setShowEvidence(false);
                    }}
                  >
                    {language === "es" ? "Solo el partido" : "Match first"}
                  </Button>
                  <Button
                    aria-pressed={!quietViewer}
                    tone={!quietViewer ? "primary" : "secondary"}
                    onClick={() => setViewerDisplay("insights")}
                  >
                    {language === "es"
                      ? "Explorar explicaciones"
                      : "Explore explanations"}
                  </Button>
                </div>
                {quietViewer && (
                  <Button onClick={catchUp}>
                    {language === "es" ? "Ponerme al día" : "Catch me up"}
                  </Button>
                )}
                {quietViewer && (
                  <p className="w-full text-sm text-stone-600">
                    {language === "es"
                      ? "Sigue el juego. Abre las explicaciones o el resumen cuando quieras."
                      : "Enjoy the play. Open explanations or catch up whenever you choose."}
                  </p>
                )}
              </div>
            )}
            <MatchStage
              showExplanation={!quietViewer}
              match={match}
              language={language}
              expired={Boolean(story && match?.story_status === "expired")}
            />
            {!!match?.corrections?.length && (
              <details
                className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-4 text-sm"
                key={match.corrections[0].notice_id}
              >
                <summary className="min-h-11 cursor-pointer py-3 font-medium">
                  {language === "es"
                    ? "Actualización: se retiró una explicación aprobada"
                    : "Update: an approved explanation was withdrawn"}
                </summary>
                {match.corrections.map((notice) => (
                  <p key={notice.notice_id} className="mb-3 leading-relaxed">
                    {timecode(notice.at_ms)} ·{" "}
                    {language === "es"
                      ? notice.kind === "source_changed"
                        ? "Cambió la fuente; se retiró la explicación afectada."
                        : "El productor retiró la explicación."
                      : notice.text}
                  </p>
                ))}
              </details>
            )}
            {showEvidence && visibleEvidence && (
              <div
                ref={evidencePanel}
                tabIndex={-1}
                aria-label={
                  language === "es"
                    ? "Evidencia del momento seleccionado"
                    : "Evidence for the selected moment"
                }
                className="scroll-mt-4"
              >
                <p className="sticky top-0 z-10 mb-2 rounded-lg bg-white px-4 py-3 text-sm tabular-nums shadow-sm">
                  {language === "es" ? "Reloj del partido" : "Match clock"} ·{" "}
                  {timecode(match?.clock_ms || 0)} ·{" "}
                  {language === "es"
                    ? "La evidencia tiene su propio reloj"
                    : "Evidence uses its own clock"}
                </p>
                <EvidenceReplay
                  data={visibleEvidence}
                  language={language}
                  onClose={() => setShowEvidence(false)}
                  focus={focus}
                />
              </div>
            )}
            {match?.approved_possession && !quietViewer && (
              <Card className="mt-5 p-4">
                <h2 className="font-semibold">
                  {language === "es"
                    ? "Posesión aprobada"
                    : "Approved possession window"}
                </h2>
                <p className="mt-2 text-sm">
                  {timecode(match.approved_possession.interval[0])}–
                  {timecode(match.approved_possession.interval[1])}
                </p>
                <Button
                  className="mt-2"
                  onClick={() =>
                    setSelectedStoryId(match.approved_possession!.story_id)
                  }
                >
                  {language === "es" ? "Abrir intervalo" : "Open window"}
                </Button>
                <p className="mt-2 text-xs text-stone-500">
                  {language === "es"
                    ? "Intervalo fijo aprobado; no es una estadística de todo el partido."
                    : "Fixed approved interval; not a full-match statistic."}
                </p>
              </Card>
            )}
            {recapOpen && (
              <div ref={recapPanel} className="scroll-mt-4">
                <CatchUpPanel
                  path={path}
                  language={language}
                  focus={focus}
                  context={`${recapContext}:${correctionContext}:${match?.score?.blue}:${match?.score?.amber}`}
                  clock={match?.clock_ms || 0}
                  visit={visit}
                  stories={stories}
                  onClose={() => setRecapOpen(false)}
                  onSelect={(storyId) => {
                    setViewerDisplay("insights");
                    setSelectedStoryId(storyId);
                    setRecapOpen(false);
                  }}
                />
              </div>
            )}
          </div>
          {!isProducer && !quietViewer && (
            <aside className="order-first min-w-0 lg:order-last">
              <AudiencePanel
                flagship={match?.flagship_demo}
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
            <aside
              id="story-queue"
              tabIndex={-1}
              aria-label="Producer story queue"
              className="order-last min-w-0 space-y-5"
            >
              <Card className="overflow-hidden">
                <div className="flex items-center justify-between border-b border-stone-100 p-5">
                  <h2 className="flex items-center gap-2 font-semibold">
                    <Layers3 size={16} />
                    Suggested insights
                  </h2>
                  <Tag>
                    {stories.length
                      ? `${stories.length} ${stories.length === 1 ? "insight" : "insights"}`
                      : "Watching"}
                  </Tag>
                </div>
                <p className="px-5 pt-4 text-sm leading-relaxed text-stone-500">
                  Suggested explanations of observed incidents and possession
                  windows. Review the evidence before approving for viewers;
                  these are not necessarily match highlights.
                </p>
                {match?.session_mode === "live" && (
                  <details className="mx-5 my-3 max-h-48 overflow-y-auto overscroll-contain text-sm">
                    <summary className="cursor-pointer">
                      AI review and delivery history
                    </summary>
                    <p className="my-2 text-xs text-stone-500">
                      Technology: {match.mode}
                    </p>
                    {(match.workflow_notices || []).map((notice, i) => (
                      <p
                        key={i}
                        className="my-2 rounded-lg bg-amber-50 p-3 text-xs text-amber-950"
                      >
                        {(
                          {
                            capacity_deferred:
                              "Model capacity was busy; the insight waited in the queue.",
                            attempt_or_session_budget_limit:
                              "An insight reached its attempt or session call limit.",
                            ai_unavailable:
                              "The AI connection was unavailable; no AI explanation was substituted.",
                            expired_unscheduled:
                              "An insight's live window ended before it could be reviewed.",
                          } as Record<string, string>
                        )[notice.state] || notice.state}{" "}
                        {notice.at_ms !== undefined
                          ? `At ${timecode(notice.at_ms)}.`
                          : ""}
                      </p>
                    ))}
                    {(match.workflow_attempts || []).length ? (
                      (match.workflow_attempts || []).map((attempt, i) => (
                        <div
                          key={i}
                          className="my-2 rounded-lg bg-stone-50 p-3"
                        >
                          <p>
                            {attempt.story_id} · {attempt.state}
                          </p>
                          <p className="text-xs text-stone-500">
                            {attempt.mode} · {attempt.usage.calls ?? "unknown"}{" "}
                            calls{attempt.reason ? ` · ${attempt.reason}` : ""}
                          </p>
                        </div>
                      ))
                    ) : (
                      <p className="mt-2 text-stone-500">
                        Watching for supported events. No explanation attempt
                        yet.
                      </p>
                    )}
                  </details>
                )}
                <div
                  data-testid="producer-insight-list"
                  className="h-80 overflow-y-auto overscroll-contain [scrollbar-gutter:stable]"
                  tabIndex={0}
                  aria-label="Incoming insights"
                >
                  {stories.length ? (
                    <StoryPicker
                      stories={stories}
                      selected={story?.id || ""}
                      onSelect={setSelectedStoryId}
                      producer
                    />
                  ) : (
                    <p className="p-5 text-sm text-stone-500">
                      Watching for supported moments.
                    </p>
                  )}
                </div>
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
                        : story.status === "ready"
                          ? language === "es"
                            ? "Lista para revisión"
                            : "Ready for review"
                          : match?.story_status}
                      {storyApproved && ` · revision ${story.revision}`}
                    </Tag>
                    <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-emerald-800">
                      {language === "es" ? "Qué cambió" : "What changed"}
                    </p>
                    <h3 className="mt-2 text-balance text-2xl font-semibold leading-tight">
                      {story.family === "pressure"
                        ? language === "es"
                          ? "Cambio de presión cercana"
                          : "Nearby pressure change"
                        : story.title}
                    </h3>
                    <p className="mt-3 text-pretty text-sm leading-relaxed text-stone-500">
                      {visibleVariant?.text ||
                        "Loading the supported explanation…"}
                    </p>
                    {match?.flagship_demo &&
                      story.why_now &&
                      (story.family !== "pressure" ||
                        /previous three|tres pases anteriores/i.test(
                          story.why_now[language] || "",
                        )) && (
                      <section
                        aria-label="Why this moment"
                        className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4"
                      >
                        <h4 className="text-sm font-semibold text-emerald-950">
                          {language === "es"
                            ? "¿Por qué este momento?"
                            : "Why this moment?"}
                        </h4>
                        <p className="mt-2 text-pretty text-sm leading-relaxed text-emerald-950">
                          {story.why_now[language]}
                        </p>
                      </section>
                    )}
                    <AudiencePreview
                      key={`${story.id}:${story.revision}`}
                      path={path}
                      story={story}
                      onInspect={() => setSelectedStoryId(story.id)}
                    />
                    {story.editorial_decision && (
                      <details className="mt-2 text-sm">
                        <summary className="min-h-11 cursor-pointer py-3 font-medium">
                          Selection and review
                        </summary>
                        <p className="mt-2 text-stone-600">
                          {story.editorial_decision.claim_ids.length} supported
                          fact
                          {story.editorial_decision.claim_ids.length === 1
                            ? " block"
                            : " blocks"}
                          . Producer approval controls whether it is shared.
                        </p>
                        {story.editorial_decision.fallback && (
                          <p className="mt-2 text-amber-900">
                            AI did not complete this explanation. A factual
                            fallback still needs producer approval.
                          </p>
                        )}
                      </details>
                    )}
                    <Button
                      onClick={() => void loadEvidence()}
                      className="mt-5 w-full"
                    >
                      <ScanLine size={15} />
                      {match?.flagship_demo ? "Check the evidence" : "Show why"}
                      <ArrowRight size={15} />
                    </Button>
                    <p className="mt-2 text-xs leading-relaxed text-stone-500">
                      Opens the recorded facts supporting this explanation. It
                      does not infer a tactical cause.
                    </p>
                    <div className="my-5 border-t border-stone-100" />
                    <div className="flex items-start gap-2 text-xs leading-relaxed text-stone-500">
                      <FileCheck2
                        size={15}
                        className="mt-0.5 shrink-0 text-emerald-700"
                      />
                      {match?.mode?.includes("local")
                        ? "Local factual template reviewed."
                        : match?.mode?.includes("fallback")
                          ? "AI attempt used a factual template fallback."
                          : "Evidence review completed."}{" "}
                      Inspect the evidence before approving.
                    </div>
                    {match?.session_mode === "live" && (
                      <p className="mt-3 text-sm font-medium">
                        {story.status === "ready"
                          ? `${Math.max(0, Math.ceil((story.expires_at_ms - match.clock_ms) / 1000))} s left for live approval`
                          : story.status === "expired"
                            ? "Live window ended · history review only"
                            : `Review status: ${story.status}`}
                      </p>
                    )}
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
                    {match?.story_status === "expired" && !storyApproved && (
                      <Button
                        className="mt-3 w-full"
                        disabled={busy}
                        onClick={() => void review("approve_archive")}
                      >
                        Approve for history only
                      </Button>
                    )}
                    {storyApproved && match?.story_status === "approved" && (
                      <Button
                        className="mt-3 w-full"
                        onClick={async () => {
                          try {
                            await api(
                              `${path}/selection`,
                              {
                                method: "POST",
                                body: JSON.stringify({
                                  story_id: story.id,
                                  expected_revision: story.revision,
                                  package_hash: story.package_hash,
                                }),
                              },
                              true,
                            );
                            await refresh();
                          } catch (e) {
                            setActionError((e as Error).message);
                          }
                        }}
                      >
                        Select shared overlay
                      </Button>
                    )}
                    {story.selection_reason && (
                      <p className="mt-3 text-xs text-stone-500">
                        {story.selection_reason}
                      </p>
                    )}
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
                      Candidates use observed goals, resolved shots, possession
                      windows, control changes and supported passes. Review
                      source facts before approval.
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
              {visibleEvidence &&
                story &&
                (!story.family || story.family === "pass") && (
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
                  Approved match insights. Choose how you follow the game.
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
                aria-expanded={Boolean(diagnostics)}
                aria-busy={diagnosticsLoading}
                disabled={diagnosticsLoading}
                className="flex w-full items-center justify-between px-2 py-2 text-xs text-stone-500"
              >
                <span className="flex items-center gap-2">
                  <Activity size={14} />
                  {diagnosticsLoading
                    ? "Opening review trace…"
                    : "Processing & review trace"}
                </span>
                <ChevronRight size={14} />
              </button>
            </aside>
          )}
        </div>
        {diagnostics && (
          <Card className="mt-6 p-6">
            <div className="flex items-center justify-between">
              <h2
                ref={diagnosticsHeading}
                tabIndex={-1}
                className="text-lg font-semibold outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"
              >
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
            {(!story?.family || story.family === "pass") && (
              <DecisionSummary
                summary={
                  diagnostics.decision_summary as Parameters<
                    typeof DecisionSummary
                  >[0]["summary"]
                }
              />
            )}
            {story?.family && story.family !== "pass" && (
              <section
                className="mt-4 rounded-xl border border-stone-200 p-4"
                aria-label="AI role decisions"
              >
                <h3 className="text-sm font-semibold">AI review steps</h3>
                <p className="mt-1 text-sm text-stone-600">
                  The Director selects a supported moment; the Reviewer checks
                  its facts and wording. Neither role approves publication.
                </p>
                <div className="mt-3 space-y-2">
                  {(
                    (diagnostics.trace ?? []) as {
                      role: string;
                      action: string;
                      status: string;
                      duration_ms?: number;
                    }[]
                  )
                    .filter((entry) => entry.action === "model_decision")
                    .map((entry, i) => {
                      const result =
                        entry.status === "propose"
                          ? "Selected this explanation"
                          : entry.status === "supported"
                            ? "Supported the facts and wording"
                            : entry.status === "abstain"
                              ? "Suggested no explanation"
                              : entry.status === "reject"
                                ? "Could not support the explanation"
                                : entry.status === "revise"
                                  ? "Requested a wording change"
                                  : entry.status.replaceAll("_", " ");
                      return (
                        <div
                          key={`${entry.role}-${i}`}
                          className="flex flex-wrap items-center justify-between gap-2 border-t border-stone-100 pt-2 text-sm"
                        >
                          <span className="font-medium">{entry.role}</span>
                          <span className="text-stone-600">{result}</span>
                          {entry.duration_ms != null && (
                            <Tag>{(entry.duration_ms / 1000).toFixed(1)} s</Tag>
                          )}
                        </div>
                      );
                    })}
                </div>
              </section>
            )}
            <details className="mt-5">
              <summary className="text-sm font-medium">
                Technical calls, timing and usage
              </summary>
              <div className="my-5 grid gap-3 text-sm sm:grid-cols-2">
                <div className="rounded-xl bg-stone-50 p-4">
                  <p className="text-xs text-stone-500">Total workflow time</p>
                  <p className="mt-2 font-mono tabular-nums">
                    {diagnostics.workflow_ms == null
                      ? "—"
                      : `${(Number(diagnostics.workflow_ms) / 1000).toFixed(2)} s`}
                  </p>
                </div>
                <div className="rounded-xl bg-stone-50 p-4">
                  <p className="text-xs text-stone-500">Model usage</p>
                  <p className="mt-2">
                    {String(
                      diagnostics.model_calls ?? modelUsage?.calls ?? "—",
                    )}{" "}
                    calls
                    {(diagnostics.model_tokens ?? modelUsage?.total_tokens) !=
                    null
                      ? ` · ${Number(diagnostics.model_tokens ?? modelUsage?.total_tokens).toLocaleString()} tokens`
                      : ""}
                  </p>
                </div>
                <div className="rounded-xl bg-stone-50 p-4 sm:col-span-2">
                  <p className="text-xs text-stone-500">AI setup</p>
                  <p className="mt-2">
                    {String(diagnostics.mode ?? "Unknown")}
                  </p>
                </div>
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
              : "Fictional identities · Original synthetic data"}
          </span>
        </footer>
      </div>
    </div>
  );
}
