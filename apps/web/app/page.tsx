"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ShieldCheck, ScanLine } from "lucide-react";
import { api, MatchOption } from "@/lib/api";
import { Button, Tag } from "@/components/ui";
export default function Home() {
  const router = useRouter();
  const [matches, setMatches] = useState<MatchOption[]>([]);
  const [key, setKey] = useState("");
  const [local, setLocal] = useState(false);
  const [accessNeeded, setAccessNeeded] = useState(false);
  const [runtime, setRuntime] = useState<{
    mode: string;
    live_ai_configured?: boolean;
    model_identity?: { deployment?: string; version?: string };
  } | null>(null);
  const [experience, setExperience] = useState("live");
  const [execution, setExecution] = useState("ai");
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
    api<{ mode: string; live_ai_configured?: boolean }>("/health")
      .then(setRuntime)
      .catch(() => {});
    api<{ matches: MatchOption[] }>("/matches")
      .then((data) => {
        const mixed = [
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
      setAccessNeeded(true);
      setError(
        message.includes("auth")
          ? "Enter your producer access key to open the demo."
          : message,
      );
    } finally {
      setBusy(false);
    }
  }
  const duration = matches.find((m) => m.match_id === fixture)?.duration_ms;
  return (
    <main className="mx-auto flex min-h-dvh max-w-6xl flex-col px-6 py-8 md:px-12">
      <header className="flex items-center justify-between gap-4">
        <a href="/" className="text-xl font-black">
          WHY<span className="text-emerald-700">/</span>NOW
        </a>
        <Tag>Interactive product demo</Tag>
      </header>
      <div className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-2 lg:py-16">
        <section>
          <p className="mb-5 text-sm font-semibold text-emerald-800">
            FOOTBALL, EXPLAINED
          </p>
          <h1 className="max-w-xl text-balance text-4xl font-semibold leading-tight md:text-5xl">
            Explain the match. Let fans enjoy it.
          </h1>
          <p className="mt-6 max-w-lg text-pretty text-lg leading-relaxed text-stone-600">
            WHY/NOW is a live football explanation desk. AI suggests stories
            from observed play; a producer checks and approves them. Fans can
            enjoy the match, explore an explanation, or catch up when they
            choose.
          </p>
          <div className="mt-8 space-y-5">
            <div>
              <h2 className="font-semibold">For producers</h2>
              <p className="mt-1 text-sm leading-relaxed text-stone-600">
                Review suggested insights, check the evidence, and approve what
                viewers see.
              </p>
            </div>
            <div>
              <h2 className="font-semibold">For fans</h2>
              <p className="mt-1 text-sm leading-relaxed text-stone-600">
                Follow the match, choose your level of detail or player focus,
                and read the recap.
              </p>
            </div>
          </div>
          <div className="mt-8 flex flex-wrap gap-5 text-sm text-stone-600">
            <span className="flex items-center gap-2">
              <ScanLine size={17} />
              Inspectable evidence
            </span>
            <span className="flex items-center gap-2">
              <ShieldCheck size={17} />
              Producer approved
            </span>
          </div>
        </section>
        <section className="min-w-0 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm md:p-9">
          <Tag className="bg-emerald-50 text-emerald-800">
            Try the producer workflow
          </Tag>
          <h2 className="mt-4 text-2xl font-semibold">
            Your live match explanation desk.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-stone-600">
            A simulated live feed keeps playing while you review a suggested
            explanation. Check its evidence, approve it, then open the viewer
            companion.
          </p>
          <div className="mt-5 space-y-4">
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
                className="min-h-12 w-full rounded-lg border border-stone-200 px-3 text-sm"
              >
                <option value="live">Live simulation · continuous match</option>
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
                className="min-h-12 w-full rounded-lg border border-stone-200 px-3 text-sm"
              >
                <option value="ai">AI · Director and Reviewer</option>
                <option value="template">Template preview · no AI calls</option>
              </select>
            </div>
            <p role="status" className="text-sm leading-relaxed text-stone-600">
              {execution === "template"
                ? "Template preview uses prepared rules and wording. It does not test AI quality or response time."
                : runtime?.live_ai_configured
                  ? "AI workflow configured. Each attempt and any fallback are identified in the producer desk."
                  : "AI is unavailable on this server. Configure the model connection or explicitly choose Template preview."}
            </p>
          </div>
          <ol className="my-6 space-y-3 text-sm text-stone-700">
            <li>1. Review suggested insights</li>
            <li>2. Check the supporting evidence</li>
            <li>3. Approve and share with fans</li>
          </ol>
          <p className="mb-4 text-sm text-stone-600">
            {duration
              ? `${Math.round(duration / 60000)}-minute replay`
              : "Loading demo…"}{" "}
            ·{" "}
            {experience === "live"
              ? "Continuous 1× playback. Stops at the end."
              : "You control playback."}
          </p>
          <details className="mb-5 rounded-xl border border-stone-200 p-4">
            <summary className="cursor-pointer text-sm font-medium">
              More demo scenarios
            </summary>
            <p className="my-3 text-sm text-stone-600">
              Each scenario is a match excerpt, not a single highlight.
              Additional recordings include engineering test cases.
            </p>
            <label htmlFor="fixture" className="mb-2 block text-sm font-medium">
              Replay segment
            </label>
            <select
              id="fixture"
              value={fixture}
              onChange={(e) => setFixture(e.target.value)}
              className="min-h-12 w-full min-w-0 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm"
            >
              {matches.map((item, index) => (
                <option key={item.match_id} value={item.match_id}>
                  {index === 0 && item.match_id === "match-0c0a000000000005"
                    ? "Mixed-event match · recommended"
                    : item.label}{" "}
                  · {Math.round(item.duration_ms / 6000) / 10} min
                </option>
              ))}
            </select>
          </details>
          {(!local || accessNeeded) && (
            <div className="mb-5">
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
                className="min-h-12 w-full rounded-lg border border-stone-200 px-3"
              />
              <p className="mt-2 text-xs text-stone-500">
                Ask your host for access. Viewers do not need a key.
              </p>
            </div>
          )}
          {error && (
            <p role="alert" className="mb-4 text-sm text-red-700">
              {error}
            </p>
          )}
          <Button
            tone="primary"
            disabled={
              busy ||
              !matches.length ||
              !key ||
              (execution === "ai" && !runtime?.live_ai_configured)
            }
            onClick={create}
            className="w-full py-3"
          >
            {busy
              ? "Opening your desk…"
              : experience === "live"
                ? "Start live simulation"
                : "Start the guided demo"}
            <ArrowRight size={17} />
          </Button>
          <p className="mt-4 text-sm leading-relaxed text-stone-500">
            Here to watch? Open the viewer link shared by your producer.
          </p>
          <p className="mt-6 border-t border-stone-100 pt-5 text-xs leading-relaxed text-stone-500">
            Demo with fictional teams and simulated match data.
          </p>
          <details className="mt-3 text-xs text-stone-500">
            <summary className="cursor-pointer py-2">
              Demo details &amp; access help
            </summary>
            <p className="mt-2 leading-relaxed">
              Execution:{" "}
              {runtime?.mode || "Connecting to the processing service…"}. Local
              template mode uses prepared rules and templates without AI model
              calls. AI mode uses the configured model, with explicitly labeled
              fallback when necessary. Each replay has its own clock and
              approvals. For local demos, access is filled in automatically; if
              prompted, ask your host for the key.
            </p>
          </details>
        </section>
      </div>
      <footer className="flex flex-wrap justify-between gap-3 border-t border-stone-200 pt-5 text-xs text-stone-500">
        <span>WHY/NOW · Football explanations for broadcasters and fans</span>
        <span>Review insights → Check evidence → Share with fans</span>
      </footer>
    </main>
  );
}
