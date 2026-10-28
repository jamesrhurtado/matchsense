"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Activity, ArrowRight, ChartNoAxesCombined, Eye } from "lucide-react";
import { api, MatchOption } from "@/lib/api";
import { Button, Tag } from "@/components/ui";
import { MomentPreview } from "@/components/moment-preview";
import { MatchSenseBrand } from "@/components/match-sense-brand";
import { ProductStory } from "@/components/product-story";
export default function Home() {
  const router = useRouter();
  const [matches, setMatches] = useState<MatchOption[]>([]);
  const [key, setKey] = useState("");
  const [local, setLocal] = useState(false);
  const [accessNeeded, setAccessNeeded] = useState(false);
  const [runtime, setRuntime] = useState<{
    workflow_ai_configured?: boolean;
    live_ai_configured?: boolean;
  } | null>(null);
  const [experience, setExperience] = useState("live");
  const [execution, setExecution] = useState("template");
  const [fixture, setFixture] = useState("");
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
        const curated = [
          "match-0c0a000000000009",
          "match-0c0a000000000005",
          "match-0c0a000000000003",
          "match-0c0a000000000001",
        ]
          .flatMap((id) => {
            const match = data.matches.find((item) => item.match_id === id);
            return match ? [match] : [];
          });
        const demoMatches = curated.length ? curated : data.matches.slice(0, 4);
        setMatches(demoMatches);
        setFixture(demoMatches[0]?.match_id || "");
        if (!demoMatches.length) {
          setError("No demo replays are available right now.");
        }
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
      <header className="flex min-h-20 items-center border-b border-emerald-950/10">
        <a href="/" aria-label="MatchSense home" className="text-xl">
          <MatchSenseBrand />
        </a>
      </header>
      <div
        id="main-content"
        className="grid items-start gap-8 py-6 lg:grid-cols-[1fr_1fr] lg:gap-8 lg:py-6"
      >
        <section>
          <h1 className="max-w-lg text-balance text-4xl font-bold leading-[1.06] sm:text-5xl">
            Explain the match.{" "}
            <span className="text-emerald-800">Let fans enjoy it.</span>
          </h1>
          <p className="mt-5 max-w-md text-pretty text-base leading-relaxed sm:text-lg text-stone-600">
            Turn a moment of play into a story fans can understand and check.
            Review the evidence, choose what goes on air, and let each fan
            explore it their way.
          </p>
          <div className="mt-7 flex max-w-xl flex-col items-start gap-3">
            <a
              href="#demo-setup"
              className="inline-flex min-h-12 items-center gap-3 rounded-xl bg-emerald-800 px-5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
            >
              Try the producer demo <ArrowRight size={17} aria-hidden="true" />
            </a>
            <nav aria-label="Explore MatchSense" className="flex flex-wrap items-center gap-x-6 gap-y-1">
              <a
                href="#moment-preview"
                className="inline-flex min-h-10 items-center gap-2 rounded-md text-sm font-semibold text-stone-700 transition-colors hover:text-emerald-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
              >
                <Eye size={16} aria-hidden="true" /> Explore the fan example
              </a>
              <a
                href="/insights"
                className="inline-flex min-h-10 items-center gap-2 rounded-md text-sm font-semibold text-stone-700 transition-colors hover:text-emerald-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
              >
                <ChartNoAxesCombined size={16} aria-hidden="true" /> Explore fan metrics
              </a>
              <a
                href="#core-features"
                className="inline-flex min-h-10 items-center gap-2 rounded-md text-sm font-semibold text-stone-700 transition-colors hover:text-emerald-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
              >
                <Activity size={16} aria-hidden="true" /> How it works
              </a>
            </nav>
          </div>
          <p className="mt-3 text-xs leading-relaxed text-stone-500">
            No sign-in required to explore the example.
          </p>
          <div className="mt-7 hidden max-w-xl border-t border-stone-200 pt-4 lg:block">
            <p className="text-xs font-semibold tracking-[0.12em] text-stone-500">
              FROM QUESTION TO BROADCAST
            </p>
            <ol className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-sm font-semibold text-stone-700">
              <li>Fan asks</li>
              <li aria-hidden="true" className="text-emerald-700">
                →
              </li>
              <li>Agents check evidence</li>
              <li aria-hidden="true" className="text-emerald-700">
                →
              </li>
              <li>Producer decides</li>
            </ol>
          </div>
        </section>
        <MomentPreview />
      </div>
      <div id="core-features" className="scroll-mt-8">
        <ProductStory />
      </div>
      <section
        aria-labelledby="homepage-preview-title"
        className="border-t border-stone-200 py-10 sm:py-14"
      >
        <div className="mx-auto max-w-5xl">
          <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase text-emerald-800">
                Product preview
              </p>
              <h2
                id="homepage-preview-title"
                className="mt-2 text-balance text-2xl font-semibold sm:text-3xl"
              >
                From a fan question to a clearer match
              </h2>
            </div>
            <p className="max-w-md text-pretty text-sm leading-relaxed text-stone-600 sm:text-right">
              A synthetic example of MatchSense connecting the play, its
              explanation, and the evidence behind it.
            </p>
          </div>
          <figure className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
            <Image
              src="/images/matchsense-homepage-preview.png"
              alt="MatchSense homepage preview showing a fan question about a pass, a plain-language explanation, and supporting match metrics."
              width={1251}
              height={739}
              sizes="(max-width: 1024px) 100vw, 1024px"
              className="h-auto w-full"
            />
            <figcaption className="border-t border-stone-200 px-4 py-2 text-xs text-stone-500 sm:px-5">
              Static product screenshot · synthetic match data
            </figcaption>
          </figure>
        </div>
      </section>
      <section
        id="demo-setup"
        className="scroll-mt-6 py-8 sm:py-10"
      >
        <div className="mx-auto min-w-0 max-w-3xl rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-7">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-xl font-semibold">Your producer demo</h3>
            <Tag>
              {execution === "template"
                ? "Prepared preview"
                : "AI · Director + Reviewer"}
            </Tag>
          </div>
          <p className="mt-3 text-pretty text-sm leading-relaxed text-stone-600">
            {execution === "template"
              ? "Review the evidence and approve the exact story viewers receive."
              : "The Director proposes a supported story and the Reviewer checks it. You decide whether to publish."}
          </p>
          {execution === "ai" && !runtime && (
            <p role="status" className="mt-3 text-sm text-stone-500">
              Checking AI availability…
            </p>
          )}
          {execution === "ai" && runtime && !runtime.workflow_ai_configured && (
            <div
              role="status"
              className="mt-3 flex flex-wrap items-center gap-2 text-sm text-amber-800"
            >
              <span>AI is unavailable here.</span>
              <button
                onClick={() => setExecution("template")}
                className="min-h-11 font-semibold text-emerald-800 underline underline-offset-4"
              >
                Use prepared preview
              </button>
            </div>
          )}
          {execution === "ai" &&
            runtime?.workflow_ai_configured &&
            experience === "live" &&
            !runtime.live_ai_configured && (
              <div role="status" className="mt-3 text-sm text-amber-800">
                AI is available in the guided walkthrough.
                <button
                  onClick={() => setExperience("guided")}
                  className="ml-2 min-h-11 font-semibold text-emerald-800 underline underline-offset-4"
                >
                  Switch to guided
                </button>
              </div>
            )}
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
            </details>
          </details>
        </div>
      </section>
      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-emerald-950/10 py-5 text-xs leading-relaxed text-stone-500">
        <span>MatchSense · Explain the moment. Follow the match.</span>
        <a
          href="https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/executive_challenge_details/5078/about"
          target="_blank"
          rel="noreferrer"
          className="inline-flex min-h-10 items-center gap-1 rounded-sm hover:text-emerald-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
        >
          Inside the Game challenge <ArrowRight size={13} aria-hidden="true" />
        </a>
      </footer>
    </main>
  );
}
