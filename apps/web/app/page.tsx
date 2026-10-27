"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Eye,
  ShieldCheck,
  ScanLine,
  SlidersHorizontal,
  Radio,
  Check,
} from "lucide-react";
import { api, MatchOption } from "@/lib/api";
import { Button, Tag } from "@/components/ui";
import { MomentPreview } from "@/components/moment-preview";
import { MatchSenseBrand } from "@/components/match-sense-brand";
export default function Home() {
  const router = useRouter();
  const [matches, setMatches] = useState<MatchOption[]>([]);
  const [key, setKey] = useState("");
  const [local, setLocal] = useState(false);
  const [accessNeeded, setAccessNeeded] = useState(false);
  const [runtime, setRuntime] = useState<{
    mode: string;
    workflow_ai_configured?: boolean;
    live_ai_configured?: boolean;
    model_identity?: { deployment?: string; version?: string };
  } | null>(null);
  const [experience, setExperience] = useState("live");
  const [execution, setExecution] = useState("template");
  const [fixture, setFixture] = useState("match-001");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const isLocal = ["localhost", "127.0.0.1"].includes(
      window.location.hostname,
    );
    setLocal(isLocal);
    setKey(
      sessionStorage.getItem("why-now-token") ||
        (isLocal ? "local-demo-producer" : ""),
    );
    api<{
      mode: string;
      workflow_ai_configured?: boolean;
      live_ai_configured?: boolean;
    }>("/health")
      .then((data) => {
        setRuntime(data);
        if (data.workflow_ai_configured) {
          setExperience("guided");
          setExecution("ai");
        }
      })
      .catch(() => {});
    api<{ matches: MatchOption[] }>("/matches")
      .then((data) => {
        const mixed = [
          "match-0c0a000000000009",
          "match-0c0a000000000005",
          "match-0c0a000000000003",
          "match-0c0a000000000001",
        ]
          .map((id) => data.matches.find((m) => m.match_id === id))
          .find(Boolean);
        setMatches(
          mixed
            ? [
                mixed,
                ...data.matches.filter((m) => m.match_id !== mixed.match_id),
              ]
            : data.matches,
        );
        setFixture(mixed?.match_id || data.matches[0]?.match_id || "match-001");
      })
      .catch(() =>
        setError(
          "Demo recordings are unavailable. Please refresh to try again.",
        ),
      );
  }, []);
  async function create() {
    setBusy(true);
    setError("");
    sessionStorage.setItem("why-now-token", key);
    try {
      const data = await api<{ session_id: string }>(
        "/replay-sessions",
        {
          method: "POST",
          body: JSON.stringify({
            match_id: fixture,
            mode: experience,
            execution,
          }),
        },
        true,
      );
      router.push(`/studio/${data.session_id}`);
    } catch (e) {
      const message = (e as Error).message;
      setAccessNeeded(message.includes("auth"));
      document.getElementById("demo-setup")?.scrollIntoView({ block: "start" });
      setError(
        message.includes("auth")
          ? "Enter your producer access key to open the demo."
          : message.includes("422") || message.includes("unknown_match")
            ? "This recording could not be opened. Choose another replay segment below and try again."
            : "The demo could not connect. Try again, or explore the prepared match example above.",
      );
    } finally {
      setBusy(false);
    }
  }
  const duration = matches.find((m) => m.match_id === fixture)?.duration_ms;
  const aiAvailableForSelection =
    runtime?.workflow_ai_configured &&
    (experience !== "live" || runtime.live_ai_configured);
  return (
    <main className="mx-auto min-h-dvh max-w-7xl px-5 pb-6 sm:px-8 lg:px-12">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:block focus:py-3"
      >
        Skip to content
      </a>
      <header className="flex min-h-24 items-center justify-between gap-4 border-b border-emerald-950/10">
        <a href="/" aria-label="MatchSense home" className="text-xl">
          <MatchSenseBrand />
        </a>
        <nav
          aria-label="Main navigation"
          className="flex items-center gap-3 text-sm"
        >
          <a
            href="#moment-preview"
            className="hidden min-h-11 items-center px-3 text-stone-600 hover:text-emerald-900 sm:inline-flex"
          >
            Explore a moment
          </a>
          <a
            href="#demo-setup"
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-stone-300 bg-white px-4 font-semibold"
          >
            Open producer desk <ArrowRight size={15} aria-hidden="true" />
          </a>
        </nav>
      </header>
      <div
        id="main-content"
        className="grid items-center gap-10 py-10 lg:grid-cols-[0.9fr_1.1fr] lg:gap-14 lg:py-14"
      >
        <section>
          <p className="mb-6 flex items-center gap-2 text-xs font-semibold text-emerald-800">
            <Radio size={15} aria-hidden="true" /> FOOTBALL, EXPLAINED
          </p>
          <h1 className="max-w-lg text-balance text-4xl font-bold leading-[1.06] sm:text-6xl">
            Explain the match.{" "}
            <span className="text-emerald-800">Let fans enjoy it.</span>
          </h1>
          <p className="mt-5 max-w-md text-pretty text-base leading-relaxed sm:text-lg text-stone-600">
            Turn a moment of play into a story fans can understand and check.
            Review the evidence, choose what goes on air, and let each fan
            explore it their way.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <a
              href="#demo-setup"
              className="inline-flex min-h-12 items-center gap-3 rounded-xl bg-emerald-800 px-5 text-sm font-semibold text-white shadow-sm hover:bg-emerald-900"
            >
              Try the producer demo <ArrowRight size={17} aria-hidden="true" />
            </a>
            <a
              href="#moment-preview"
              className="inline-flex min-h-12 items-center gap-2 rounded-xl border border-stone-300 bg-white px-5 text-sm font-semibold hover:bg-emerald-50"
            >
              <Eye size={17} aria-hidden="true" /> Explore the fan example
            </a>
          </div>
          <p className="mt-3 text-xs leading-relaxed text-stone-500">
            Explore the example now. No sign-in or AI connection needed.
          </p>
          <div className="mt-9 hidden border-t border-emerald-950/10 pt-6 lg:block">
            <p className="text-sm font-semibold">
              One story. Different ways to follow it.
            </p>
            <p className="mt-2 max-w-md text-sm leading-relaxed text-stone-600">
              Try English or Spanish and simple or detailed explanations in the
              example. The underlying facts stay the same.
            </p>
            <div className="mt-5 flex flex-wrap gap-x-5 gap-y-3 text-xs font-medium text-emerald-950">
              <span className="flex items-center gap-2">
                <ScanLine size={15} aria-hidden="true" /> Inspectable evidence
              </span>
              <span className="flex items-center gap-2">
                <ShieldCheck size={15} aria-hidden="true" /> Producer controls
                publication
              </span>
            </div>
          </div>
        </section>
        <MomentPreview />
      </div>
      <section
        className="grid gap-0 border-y border-emerald-950/15 py-7 md:grid-cols-3"
        aria-label="From the play to the fan"
      >
        {[
          [
            "01",
            "Find the story",
            "Suggested moments connect the play to measured facts.",
          ],
          [
            "02",
            "Make the call",
            "A producer checks the evidence and approves the exact story.",
          ],
          [
            "03",
            "Follow it your way",
            "Fans choose language, detail and player or team focus.",
          ],
        ].map(([n, title, copy]) => (
          <div key={n} className="flex gap-4 px-0 py-4 md:px-5 first:md:pl-0">
            <span className="pt-1 font-mono text-xs tabular-nums text-emerald-700">
              {n}
            </span>
            <div>
              <h2 className="text-sm font-semibold">{title}</h2>
              <p className="mt-2 max-w-xs text-pretty text-sm leading-relaxed text-stone-600">
                {copy}
              </p>
            </div>
          </div>
        ))}
      </section>
      <section
        id="demo-setup"
        className="grid scroll-mt-6 gap-8 py-12 lg:grid-cols-[0.9fr_1.1fr] lg:gap-14"
      >
        <div>
          <p className="flex items-center gap-2 text-xs font-semibold text-emerald-800">
            <SlidersHorizontal size={15} aria-hidden="true" /> YOUR NEXT STEP
          </p>
          <h2 className="mt-4 text-balance text-3xl font-semibold">
            Go behind the explanation.
          </h2>
          <div className="mt-6 space-y-6">
            <div>
              <h3 className="flex items-center gap-2 font-semibold">
                <ScanLine size={17} aria-hidden="true" /> For producers
              </h3>
              <p className="mt-2 max-w-sm text-sm leading-relaxed text-stone-600">
                Open a replay, inspect a suggestion, and approve the exact
                explanation for viewers.
              </p>
            </div>
            <div>
              <h3 className="flex items-center gap-2 font-semibold">
                <Eye size={17} aria-hidden="true" /> For fans
              </h3>
              <p className="mt-2 max-w-sm text-sm leading-relaxed text-stone-600">
                Explore the example above, or open the viewer companion from a
                producer session to follow approved stories and catch up.
              </p>
            </div>
          </div>
        </div>
        <div className="min-w-0 rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-7">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-xl font-semibold">Your producer demo</h3>
            <Tag>
              {execution === "template"
                ? "Prepared wording · no AI calls"
                : "AI · Director + Reviewer"}
            </Tag>
          </div>
          <p className="mt-3 text-pretty text-sm leading-relaxed text-stone-600">
            {execution === "template"
              ? "Start with a replay and rule-based explanations. You review and approve what fans receive."
              : "The Director proposes a supported story and the Reviewer checks it. You decide whether to publish."}
          </p>
          <div
            role="status"
            className="mt-4 rounded-lg bg-stone-50 p-3 text-sm leading-relaxed text-stone-600"
          >
            {runtime ? (
              runtime.workflow_ai_configured ? (
                <>
                  <Check
                    size={14}
                    className="mr-2 inline text-emerald-800"
                    aria-hidden="true"
                  />
                  {execution === "ai" && experience === "live" && !runtime.live_ai_configured
                    ? "AI is ready for the guided replay. Continuous live-mode AI needs additional event-model configuration."
                    : execution === "ai"
                      ? "AI is ready. The Director proposes, the Reviewer checks, and you decide what viewers receive."
                      : "AI is configured for this replay. Choose AI in Demo options to see the Director and Reviewer handoff."}
                </>
              ) : (
                <>
                  AI is not configured for this demo. The prepared example and
                  template preview remain available.
                </>
              )
            ) : (
              "Checking the demo connection…"
            )}
            {execution === "ai" && runtime && !runtime.workflow_ai_configured && (
              <button
                onClick={() => setExecution("template")}
                className="mt-2 block min-h-11 font-semibold text-emerald-800 underline underline-offset-4"
              >
                Use template preview instead
              </button>
            )}
            {execution === "ai" &&
              runtime?.workflow_ai_configured &&
              experience === "live" &&
              !runtime.live_ai_configured && (
                <button
                  onClick={() => setExperience("guided")}
                  className="mt-2 block min-h-11 font-semibold text-emerald-800 underline underline-offset-4"
                >
                  Use the guided AI walkthrough
                </button>
              )}
          </div>
          {(!local || accessNeeded) && (
            <div className="mt-4">
              <label
                htmlFor="access"
                className="mb-2 block text-sm font-medium"
              >
                Producer access key
              </label>
              <input
                id="access"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                type="password"
                autoComplete="off"
                className="min-h-12 w-full rounded-lg border border-stone-300 px-3"
              />
              <p className="mt-2 text-xs text-stone-500">
                Ask your host for access. The example above is open to everyone.
              </p>
            </div>
          )}
          {error && (
            <p
              role="alert"
              className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm leading-relaxed text-red-800"
            >
              {error}
            </p>
          )}
          <Button
            tone="primary"
            disabled={
              busy ||
              !matches.length ||
              !key ||
              (execution === "ai" && !aiAvailableForSelection)
            }
            onClick={create}
            className="mt-5 w-full py-3"
          >
            {busy
              ? "Opening your desk…"
              : experience === "live"
                ? "Start live simulation"
                : "Start the guided demo"}
            <ArrowRight size={17} aria-hidden="true" />
          </Button>
          <p className="mt-3 text-center text-xs text-stone-500">
            {duration
              ? `${Math.round(duration / 6000) / 10}-minute replay`
              : "Connecting to recordings…"}{" "}
            ·{" "}
            {experience === "live"
              ? "Continuous 1× playback"
              : "You control playback"}
          </p>
          <details className="mt-5 border-t border-stone-200 pt-2">
            <summary className="flex min-h-11 items-center text-sm font-medium">
              Demo options
            </summary>
            <div className="grid gap-4 py-3 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="experience"
                  className="mb-2 block text-sm font-medium"
                >
                  Experience
                </label>
                <select
                  id="experience"
                  value={experience}
                  onChange={(e) => setExperience(e.target.value)}
                  className="min-h-12 w-full rounded-lg border border-stone-300 bg-white px-3 text-sm"
                >
                  <option value="live">
                    Live simulation · continuous match
                  </option>
                  <option value="guided">
                    Guided walkthrough · pause and learn
                  </option>
                </select>
              </div>
              <div>
                <label
                  htmlFor="execution"
                  className="mb-2 block text-sm font-medium"
                >
                  Explanations
                </label>
                <select
                  id="execution"
                  value={execution}
                  onChange={(e) => setExecution(e.target.value)}
                  className="min-h-12 w-full rounded-lg border border-stone-300 bg-white px-3 text-sm"
                >
                  <option value="ai">AI · Director and Reviewer</option>
                  <option value="template">
                    Template preview · no AI calls
                  </option>
                </select>
              </div>
            </div>
            <details className="pb-3">
              <summary className="min-h-11 py-3 text-sm">
                More demo scenarios
              </summary>
              <label
                htmlFor="fixture"
                className="mb-2 block text-sm font-medium"
              >
                Replay segment
              </label>
              <select
                id="fixture"
                value={fixture}
                onChange={(e) => setFixture(e.target.value)}
                className="min-h-12 w-full min-w-0 rounded-lg border border-stone-300 bg-white px-3 text-sm"
              >
                {matches.map((item) => (
                  <option key={item.match_id} value={item.match_id}>
                    {item.label} · {Math.round(item.duration_ms / 6000) / 10}{" "}
                    min
                  </option>
                ))}
              </select>
              <p className="mt-2 text-xs leading-relaxed text-stone-500">
                Recordings are match excerpts. The catalogue also includes
                engineering test cases.
              </p>
            </details>
          </details>
          <details className="border-t border-stone-200 pt-2 text-xs text-stone-500">
            <summary className="min-h-11 py-3">
              Demo details &amp; access help
            </summary>
            <p className="pb-3 leading-relaxed">
              Execution: {runtime?.mode || "Service not connected"}. Templates
              use prepared rules and wording without AI calls. AI execution and
              any fallback are identified in the desk. Each replay has its own
              clock and approvals. The homepage example is a separate prepared
              illustration, not a live publication.
            </p>
          </details>
        </div>
      </section>
      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-emerald-950/10 py-5 text-xs leading-relaxed text-stone-500">
        <span>
          MatchSense · Football explanations for broadcasters and fans
        </span>
        <span>Demo with fictional teams and simulated match data.</span>
      </footer>
    </main>
  );
}
