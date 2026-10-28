import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Languages,
  MessageCircleQuestion,
  RadioTower,
  ScanSearch,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

const features: {
  number: string;
  title: string;
  description: string;
  icon: LucideIcon;
  note?: string;
  href?: string;
}[] = [
  {
    number: "01",
    title: "Find the moment behind the question",
    description:
      "The Audience Agent can group questions from a connected YouTube Live chat or a labeled rehearsal. A producer links the group to the relevant moment.",
    icon: MessageCircleQuestion,
    note: "The producer confirms each moment",
  },
  {
    number: "02",
    title: "Read more than the score",
    description:
      "Explore passes, pressure changes, shots, possession and player contributions with the match context alongside them.",
    icon: BarChart3,
    note: "Synthetic Match Lab",
    href: "/insights",
  },
  {
    number: "03",
    title: "Trace every explanation to evidence",
    description:
      "Inspect the measurements, time windows, source observations and coverage behind a proposed story.",
    icon: ScanSearch,
    note: "Incomplete evidence stays visible",
  },
  {
    number: "04",
    title: "Give AI clear roles and boundaries",
    description:
      "The Story Director selects supported facts. The Claim Reviewer checks the rendered wording and can request a bounded revision.",
    icon: BrainCircuit,
    note: "The producer makes the final call",
  },
  {
    number: "05",
    title: "Put an approved story on screen",
    description:
      "The producer approves an exact revision before it appears as a timed browser overlay that can be composed in OBS.",
    icon: RadioTower,
    note: "Producer approval before broadcast",
  },
  {
    number: "06",
    title: "Let every fan choose how to follow",
    description:
      "Viewers can switch English or Spanish, choose a concise or detailed view, focus on a player or team, and catch up on approved moments.",
    icon: Languages,
    note: "One approved story, several viewer lenses",
  },
];

const stages = [
  {
    number: "01",
    name: "Ingest",
    description: "Release synthetic match events as the replay clock advances.",
  },
  {
    number: "02",
    name: "Interpret",
    description: "Calculate what the available match evidence supports.",
  },
  {
    number: "03",
    name: "Explain",
    description: "Build a clear story from checked facts and context.",
  },
  {
    number: "04",
    name: "Render",
    description: "Let a producer approve the story for the broadcast overlay.",
  },
  {
    number: "05",
    name: "Personalize",
    description: "Give fans their choice of language, detail and focus.",
  },
];

const stack = [
  {
    label: "AI workflow",
    items: "Microsoft Foundry · Azure OpenAI · Microsoft Agent Framework",
  },
  {
    label: "Product",
    items: "Next.js · React · TypeScript · Python · FastAPI",
  },
  {
    label: "Azure services",
    items: "Container Apps · Event Hubs · Cosmos DB · managed identity",
  },
  {
    label: "Match and broadcast",
    items: "Synthetic event replay · OBS browser overlay · YouTube Live chat",
  },
];

export function ProductStory() {
  return (
    <div className="space-y-16 py-12 sm:space-y-20 sm:py-16 lg:space-y-24 lg:py-20">
      <section
        aria-labelledby="problem-heading"
        className="space-y-6 border-y border-emerald-950/10 py-9 sm:py-12"
      >
        <div className="grid gap-7 lg:grid-cols-[0.9fr_1.1fr] lg:items-end lg:gap-16">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-800">
              What fans are telling us
            </p>
            <h2
              id="problem-heading"
              className="mt-4 max-w-2xl text-balance text-3xl font-semibold leading-tight tracking-tight sm:text-4xl"
            >
              The ball is easy to follow. The story around it can be harder to see.
            </h2>
          </div>
          <div className="max-w-2xl lg:justify-self-end">
            <p className="text-pretty text-base leading-relaxed text-stone-600">
              In public fan discussions, new viewers describe seeing a chain of
              passes without knowing what to look for. Others say player roles
              and movement away from the ball are hard to follow while play
              unfolds. They can see the action, but the reason it matters can
              pass them by.
            </p>
            <p className="mt-3 text-sm leading-relaxed text-stone-600">
              We saw this in discussions from{" "}
              <a
                href="https://www.reddit.com/r/SoccerNoobs/comments/1glgt9u/how_to_understand_the_game/"
                target="_blank"
                rel="noreferrer"
                className="font-medium text-emerald-900 underline decoration-emerald-900/30 underline-offset-2 hover:decoration-emerald-900"
              >
                first-time viewers
              </a>{" "}
              and fans trying to understand{" "}
              <a
                href="https://www.reddit.com/r/footballtactics/comments/1tmj2dg/im_trying_to_understand_soccer_tactics_better_as/"
                target="_blank"
                rel="noreferrer"
                className="font-medium text-emerald-900 underline decoration-emerald-900/30 underline-offset-2 hover:decoration-emerald-900"
              >
                player roles and team movement
              </a>
              .
            </p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <article className="rounded-2xl border border-emerald-950/10 bg-white/75 p-5 sm:p-6">
            <p className="text-4xl font-semibold tracking-tight text-emerald-900 sm:text-5xl">
              53%
            </p>
            <p className="mt-2 max-w-sm text-sm leading-relaxed text-stone-700">
              of surveyed sports fans say too much technology has reduced the
              fun of watching live.
            </p>
            <a
              href="https://www.capgemini.com/wp-content/uploads/2025/07/Final-Web-Version-Report-Tech-In-Sports_V3.pdf#page=35"
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-flex min-h-8 items-center text-xs font-medium text-emerald-900 underline decoration-emerald-900/30 underline-offset-2 hover:decoration-emerald-900"
            >
              Capgemini · 12,017 fans surveyed
            </a>
          </article>
          <article className="rounded-2xl border border-emerald-950/10 bg-white/75 p-5 sm:p-6">
            <p className="text-4xl font-semibold tracking-tight text-emerald-900 sm:text-5xl">
              67%
            </p>
            <p className="mt-2 max-w-sm text-sm leading-relaxed text-stone-700">
              say faster recaps would improve their digital sports experience.
            </p>
            <a
              href="https://newsroom.ibm.com/2025-08-18-ibm-study-sports-fans-demand-more-dynamic-digital-content,-powered-by-ai"
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-flex min-h-8 items-center text-xs font-medium text-emerald-900 underline decoration-emerald-900/30 underline-offset-2 hover:decoration-emerald-900"
            >
              IBM · 20,864 fans across 12 countries
            </a>
          </article>
        </div>

        <div className="flex flex-col gap-2 border-t border-emerald-950/10 pt-4 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
          <p className="flex items-center gap-2 text-sm font-semibold text-emerald-950">
            <Activity size={17} className="shrink-0 text-emerald-700" aria-hidden="true" />
            MatchSense adds one concise explanation checked against match
            evidence, with more detail available when a fan wants it.
          </p>
        </div>
      </section>

      <section aria-labelledby="features-heading" className="scroll-mt-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-800">
              From live event to fan insight
            </p>
            <h2
              id="features-heading"
              className="mt-3 text-balance text-3xl font-semibold tracking-tight sm:text-4xl"
            >
              Core features
            </h2>
          </div>
          <p className="max-w-md text-pretty text-sm leading-relaxed text-stone-600 sm:text-right">
            A connected workflow for the people making the broadcast and the
            fans following it.
          </p>
        </div>

        <div className="mt-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <article
                key={feature.number}
                className="group flex min-h-56 flex-col rounded-2xl border border-emerald-950/10 bg-white/75 p-5 shadow-sm transition-colors hover:border-emerald-900/25 hover:bg-white sm:p-6"
              >
                <div className="flex items-center justify-between">
                  <span className="flex size-10 items-center justify-center rounded-xl bg-emerald-950 text-emerald-100">
                    <Icon size={19} strokeWidth={1.8} aria-hidden="true" />
                  </span>
                  <span className="font-mono text-xs tabular-nums text-stone-400">
                    {feature.number}
                  </span>
                </div>
                <h3 className="mt-5 text-lg font-semibold leading-snug tracking-tight">
                  {feature.title}
                </h3>
                <p className="mt-2 flex-1 text-pretty text-sm leading-relaxed text-stone-600">
                  {feature.description}
                </p>
                <div className="mt-4 flex min-h-5 items-center justify-between gap-2 border-t border-stone-200 pt-3 text-xs font-medium text-emerald-900">
                  <span>{feature.note}</span>
                  {feature.href && (
                    <a
                      href={feature.href}
                      className="inline-flex shrink-0 items-center gap-1 rounded-sm font-semibold hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
                    >
                      Explore <ArrowRight size={13} aria-hidden="true" />
                    </a>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section
        aria-labelledby="pipeline-heading"
        className="overflow-hidden rounded-3xl bg-[#132c24] text-white shadow-xl"
      >
        <div className="p-6 sm:p-9 lg:p-11">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">
                One connected pipeline
              </p>
              <h2
                id="pipeline-heading"
                className="mt-3 text-balance text-3xl font-semibold tracking-tight sm:text-4xl"
              >
                From match feed to a fan’s point of view.
              </h2>
            </div>
            <span className="flex items-center gap-2 text-sm font-medium text-emerald-100/75">
              <ShieldCheck size={17} aria-hidden="true" />
              Evidence in. Producer-approved stories out.
            </span>
          </div>
          <ol className="mt-9 grid gap-0 sm:grid-cols-2 lg:grid-cols-5">
            {stages.map((stage, index) => (
              <li
                key={stage.number}
                className={`relative border-t border-white/20 py-5 sm:px-4 first:sm:pl-0 lg:border-l lg:border-t-0 lg:py-0 lg:first:border-l-0 lg:first:pl-0 ${
                  index === stages.length - 1 ? "lg:pr-0" : "lg:pr-5"
                }`}
              >
                <span className="font-mono text-[11px] tabular-nums text-emerald-200">
                  {stage.number} <span aria-hidden="true">/</span> 05
                </span>
                <h3 className="mt-3 text-xl font-semibold">{stage.name}</h3>
                <p className="mt-2 max-w-52 text-pretty text-sm leading-relaxed text-white/70">
                  {stage.description}
                </p>
              </li>
            ))}
          </ol>
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-white/15 bg-white/[0.04] px-6 py-4 text-xs font-medium text-emerald-100/80 sm:px-9 lg:px-11">
          <span>Fan question</span>
          <span aria-hidden="true">→</span>
          <span>Match evidence</span>
          <span aria-hidden="true">→</span>
          <span>Agent review</span>
          <span aria-hidden="true">→</span>
          <span>Producer approval</span>
          <span aria-hidden="true">→</span>
          <span>Viewer companion</span>
        </div>
      </section>

      <section aria-labelledby="built-with-heading">
        <div className="grid gap-7 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-800">
              Built for the Inside the Game challenge
            </p>
            <h2
              id="built-with-heading"
              className="mt-3 text-balance text-3xl font-semibold tracking-tight sm:text-4xl"
            >
              Built to explain the game, end to end.
            </h2>
            <p className="mt-4 max-w-md text-pretty text-sm leading-relaxed text-stone-600">
              Deterministic match calculations keep every displayed number tied
              to its source. In the Azure AI workflow, two specialist agents
              prepare and review the explanation before the producer decides.
            </p>
          </div>
          <div className="divide-y divide-emerald-950/10 border-y border-emerald-950/10">
            {stack.map((item) => (
              <div
                key={item.label}
                className="grid gap-1 py-4 sm:grid-cols-[10.5rem_1fr] sm:gap-5"
              >
                <h3 className="text-sm font-semibold text-emerald-950">
                  {item.label}
                </h3>
                <p className="text-pretty text-sm leading-relaxed text-stone-600">
                  {item.items}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
