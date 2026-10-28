"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ChartNoAxesCombined, ShieldCheck } from "lucide-react";
import { api, cn } from "@/lib/api";
import { MatchSenseBrand } from "@/components/match-sense-brand";

type Shot = {
  id: string;
  team_id: string;
  team_name: string;
  player_id: string;
  player_name: string;
  x_m: number;
  y_m: number;
  body_part: string;
  play_type: string;
  defenders_nearby: number;
  keeper_out_of_position: boolean;
  xg: number;
  distance_m: number;
  angle_deg: number;
  goal: boolean;
};
type Episode = {
  id: string;
  time_s: number;
  pressing_team: string;
  pressured_team: string;
  nearby_defenders: number;
  distance_m: number;
  outcome: string;
  window_s: number;
};
type ShapeScenario = {
  id: string;
  label: string;
  description: string;
  trigger_time_s: number;
  trigger_x_m: number;
  trigger_zone: string;
  trigger_observed: boolean;
  team_length_m: number;
  team_width_m: number;
  line_heights_m: Record<string, number>;
  line_gaps_m: Record<string, number>;
  frame: {
    ball: { x_m: number; y_m: number };
    players: {
      player_id: string;
      team_id: string;
      role: string;
      x_m: number;
      y_m: number;
    }[];
  };
};
type PlayerContribution = {
  player_id: string;
  number: string;
  name: string;
  role: string;
  role_code: string;
  team_id: string;
  team_name: string;
  progressive_passes_completed: number;
  progressive_passes_attempted: number;
  recoveries: number;
  shots: number;
  xg: number;
};
type Demo = {
  source: string;
  teams: Record<string, { name: string; color: string }>;
  xg: {
    model_version: string;
    model_note: string;
    explanation: string;
    shots: Shot[];
    teams: {
      team_id: string;
      team_name: string;
      xg: number;
      goals: number;
      shots: number;
    }[];
  };
  pressure: {
    definition_version: string;
    definition: string;
    episodes: Episode[];
    summary: {
      total: number;
      known: number;
      incomplete: number;
      regains: number;
      regain_rate: number;
      outcomes: Record<string, number>;
    };
  };
  tactics: { definition_version: string; scenarios: ShapeScenario[] };
  players: PlayerContribution[];
  limits: string[];
};

const copy = {
  en: {
    back: "Back to MatchSense",
    eyebrow: "SYNTHETIC MATCH LAB",
    title: "Make the numbers make sense.",
    intro:
      "Explore the questions fans ask through an interactive synthetic match.",
    shots: "Chance quality · xG",
    pressure: "Pressure · next outcome",
    shape: "Team shape · press location",
    players: "Player contributions",
    simulated: "Synthetic example",
    shotsTitle: "How good was the chance?",
    shotHelp: "Select a shot to see what shaped its estimate.",
    xg: "Expected goals",
    goals: "Goals scored",
    totalShots: "shots",
    model: "Demo model",
    xgNote:
      "xG estimates the chance that a shot becomes a goal. A 0.20 estimate means about 2 in 10 similar chances score over many attempts; this shot can still score or miss.",
    selectedShot: "Selected shot",
    distance: "Distance",
    angle: "Goal angle",
    bodyPart: "Shot type",
    pressureNearby: "Defenders nearby",
    keeper: "Goalkeeper",
    keeperOut: "Out of position",
    keeperSet: "Set",
    openPlay: "Open play",
    counter: "Counterattack",
    cross: "Cross",
    penalty: "Penalty",
    head: "Header",
    foot: "Foot",
    pressureTitle: "What followed a pressure episode?",
    episodes: "Episodes",
    known: "Known outcomes",
    regains: "Pressing-team regains",
    of: "of",
    fiveSeconds: "within 5 s",
    unknown: "Incomplete data",
    pressureNote:
      "Each episode shows the recorded outcome during the five seconds after nearby pressure was observed.",
    regained: "Pressing team regained the ball",
    progressed: "Pressed team kept the ball and progressed",
    held: "Pressed team kept the ball; no clear progression",
    incomplete: "Incomplete observation",
    shapeTitle: "Where did the team close down?",
    highPress: "High press",
    midBlock: "Mid-block",
    trigger: "First sustained pressure",
    at: "at",
    zone: "Pitch zone",
    length: "Team length",
    width: "Team width",
    defense: "Defence line",
    midfield: "Midfield line",
    forwards: "Forward line",
    gap: "Line gap",
    shapeNote:
      "Tactic labels are authored for this synthetic scene. Position and spacing values are calculated from the plotted players.",
    pitchLabel: "Synthetic match positions at the pressure trigger",
    playerTitle: "What did each player contribute?",
    playerNote:
      "Event counts stay tied to the player's role; there is no overall rating.",
    progPasses: "Progressive passes",
    recoveries: "Recoveries",
    shotsLabel: "Shots",
    playerXg: "xG",
    completed: "completed",
    attempted: "attempted",
    allData:
      "All data here is generated for demonstration. It is not real match or league data.",
    language: "Language",
    loading: "Preparing the synthetic match…",
    error: "Could not load the demo data.",
    retry: "Retry",
    source: "Generated replay",
  },
  es: {
    back: "Volver a MatchSense",
    eyebrow: "LABORATORIO DE PARTIDO SINTÉTICO",
    title: "Entiende lo que dicen las cifras.",
    intro:
      "Explora las preguntas de los fans con un partido sintético interactivo.",
    shots: "Calidad de ocasión · xG",
    pressure: "Presión · desenlace",
    shape: "Forma del equipo · zona de presión",
    players: "Aportes por jugador",
    simulated: "Ejemplo sintético",
    shotsTitle: "¿Qué tan clara fue la ocasión?",
    shotHelp:
      "Selecciona un remate para ver qué factores forman su estimación.",
    xg: "Goles esperados",
    goals: "Goles anotados",
    totalShots: "remates",
    model: "Modelo demo",
    xgNote:
      "xG estima la probabilidad de que un remate termine en gol. 0,20 significa cerca de 2 de cada 10 ocasiones similares en muchos intentos; este remate aún puede entrar o fallarse.",
    selectedShot: "Remate seleccionado",
    distance: "Distancia",
    angle: "Ángulo a portería",
    bodyPart: "Tipo de remate",
    pressureNearby: "Defensas cercanos",
    keeper: "Portero",
    keeperOut: "Fuera de posición",
    keeperSet: "Bien ubicado",
    openPlay: "Juego abierto",
    counter: "Contraataque",
    cross: "Centro",
    penalty: "Penal",
    head: "Cabeza",
    foot: "Pie",
    pressureTitle: "¿Qué pasó después de la presión?",
    episodes: "Episodios",
    known: "Desenlaces observados",
    regains: "Recuperaciones del equipo que presiona",
    of: "de",
    fiveSeconds: "en 5 s",
    unknown: "Datos incompletos",
    pressureNote:
      "Cada episodio muestra el desenlace registrado durante los cinco segundos posteriores a la presión cercana.",
    regained: "El equipo que presiona recuperó el balón",
    progressed: "El equipo presionado conservó y avanzó",
    held: "El equipo presionado conservó; sin avance claro",
    incomplete: "Observación incompleta",
    shapeTitle: "¿Dónde cerró espacios el equipo?",
    highPress: "Presión alta",
    midBlock: "Bloque medio",
    trigger: "Primera presión sostenida",
    at: "a los",
    zone: "Zona del campo",
    length: "Largo del equipo",
    width: "Ancho del equipo",
    defense: "Línea defensiva",
    midfield: "Línea media",
    forwards: "Línea ofensiva",
    gap: "Distancia entre líneas",
    shapeNote:
      "Las etiquetas tácticas se definieron para esta escena sintética. Las posiciones y distancias se calculan desde los jugadores dibujados.",
    pitchLabel: "Posiciones sintéticas al comenzar la presión",
    playerTitle: "¿Qué aportó cada jugador?",
    playerNote:
      "Los eventos se muestran según el rol; no hay una calificación general.",
    progPasses: "Pases progresivos",
    recoveries: "Recuperaciones",
    shotsLabel: "Remates",
    playerXg: "xG",
    completed: "completados",
    attempted: "intentados",
    allData:
      "Todos los datos son generados para esta demo. No son datos de un partido ni liga real.",
    language: "Idioma",
    loading: "Preparando el partido sintético…",
    error: "No se pudieron cargar los datos de la demo.",
    retry: "Reintentar",
    source: "Repetición generada",
  },
} as const;

function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail?: string;
}) {
  return (
    <div className="min-w-0 rounded-xl border border-stone-200 bg-white p-3">
      <p className="text-xs text-stone-500">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums text-[#173c2b]">
        {value}
      </p>
      {detail && <p className="mt-1 text-xs text-stone-500">{detail}</p>}
    </div>
  );
}

function pressureOutcomeLabel(outcome: string, language: "en" | "es") {
  const labels = {
    en: {
      pressing_team_regained: copy.en.regained,
      pressed_team_kept_and_progressed: copy.en.progressed,
      pressed_team_kept_no_clear_progress: copy.en.held,
      incomplete: copy.en.incomplete,
    },
    es: {
      pressing_team_regained: copy.es.regained,
      pressed_team_kept_and_progressed: copy.es.progressed,
      pressed_team_kept_no_clear_progress: copy.es.held,
      incomplete: copy.es.incomplete,
    },
  };
  return (
    labels[language][outcome as keyof (typeof labels)[typeof language]] ||
    labels[language].incomplete
  );
}

export function InsightsDemo() {
  const [language, setLanguage] = useState<"en" | "es">("en");
  const [data, setData] = useState<Demo | null>(null);
  const [error, setError] = useState(false);
  const [selectedShotId, setSelectedShotId] = useState("");
  const [scenarioId, setScenarioId] = useState("high-press");
  const t = copy[language];
  useEffect(() => {
    let active = true;
    const load = () =>
      api<Demo>("/insights/demo")
        .then((value) => {
          if (!active) return;
          setData(value);
          setSelectedShotId(value.xg.shots[0]?.id || "");
          setError(false);
        })
        .catch(() => {
          if (active) setError(true);
        });
    void load();
    return () => {
      active = false;
    };
  }, []);
  const shot =
    data?.xg.shots.find((item) => item.id === selectedShotId) ||
    data?.xg.shots[0];
  const scenario =
    data?.tactics.scenarios.find((item) => item.id === scenarioId) ||
    data?.tactics.scenarios[0];
  const maxOutcome = useMemo(
    () => Math.max(1, ...Object.values(data?.pressure.summary.outcomes || {})),
    [data],
  );

  return (
    <main className="mx-auto min-h-dvh max-w-7xl px-5 pb-12 sm:px-8 lg:px-12">
      <header className="flex min-h-20 items-center justify-between gap-4 border-b border-emerald-950/10">
        <Link href="/" aria-label="MatchSense home" className="text-xl">
          <MatchSenseBrand />
        </Link>
        <div className="flex items-center gap-3">
          <label htmlFor="insights-language" className="sr-only">
            {t.language}
          </label>
          <select
            id="insights-language"
            value={language}
            onChange={(event) => setLanguage(event.target.value as "en" | "es")}
            className="min-h-11 rounded-lg border border-stone-300 bg-white px-3 text-sm"
          >
            <option value="en">English</option>
            <option value="es">Español</option>
          </select>
          <Link
            href="/"
            className="hidden min-h-11 items-center gap-2 text-sm font-medium text-stone-600 hover:text-emerald-900 sm:inline-flex"
          >
            <ArrowLeft size={16} aria-hidden="true" />
            {t.back}
          </Link>
        </div>
      </header>

      <section className="py-9 sm:py-12">
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold tracking-wide text-emerald-800">
          <ChartNoAxesCombined size={16} aria-hidden="true" />
          {t.eyebrow}
          <span className="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-[10px] tracking-normal text-amber-900">
            {t.simulated}
          </span>
        </div>
        <h1 className="mt-3 max-w-3xl text-balance text-3xl font-bold leading-tight text-[#172721] sm:text-5xl">
          {t.title}
        </h1>
        <p className="mt-3 max-w-2xl text-pretty text-base leading-relaxed text-stone-600">
          {t.intro}
        </p>
        <nav
          aria-label={
            language === "es" ? "Secciones de métricas" : "Metric sections"
          }
          className="mt-6 flex flex-wrap gap-2"
        >
          {[
            ["#xg", t.shots],
            ["#pressure", t.pressure],
            ["#shape", t.shape],
            ["#players", t.players],
          ].map(([href, label]) => (
            <a
              key={href}
              href={href}
              className="inline-flex min-h-10 items-center rounded-full border border-stone-300 bg-white px-3 text-sm font-medium text-stone-700 hover:border-emerald-500 hover:text-emerald-900"
            >
              {label}
            </a>
          ))}
        </nav>
      </section>

      {!data && !error && (
        <p
          role="status"
          className="rounded-xl border border-stone-200 bg-white p-5 text-sm text-stone-600"
        >
          {t.loading}
        </p>
      )}
      {error && (
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
        >
          <span>{t.error}</span>
          <button
            onClick={() => {
              setError(false);
              void api<Demo>("/insights/demo")
                .then((value) => {
                  setData(value);
                  setSelectedShotId(value.xg.shots[0]?.id || "");
                })
                .catch(() => setError(true));
            }}
            className="min-h-10 font-semibold underline"
          >
            {t.retry}
          </button>
        </div>
      )}

      {data && (
        <div className="space-y-6">
          <section
            id="xg"
            className="scroll-mt-5 rounded-2xl border border-stone-200 bg-[#f9fbfa] p-4 sm:p-6"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
                  01 · {t.shots}
                </p>
                <h2 className="mt-2 text-xl font-semibold sm:text-2xl">
                  {t.shotsTitle}
                </h2>
                <p className="mt-1 text-sm text-stone-600">{t.shotHelp}</p>
              </div>
              <span className="rounded-full border border-stone-300 bg-white px-3 py-1 text-xs text-stone-600">
                {data.xg.model_version}
              </span>
            </div>
            <div className="mt-5 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="space-y-3">
                {data.xg.teams.map((team) => (
                  <div
                    key={team.team_id}
                    className="rounded-xl border border-stone-200 bg-white p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-semibold">{team.team_name}</span>
                      <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-900">
                        {team.shots} {t.totalShots}
                      </span>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-3">
                      <Metric label={t.xg} value={team.xg.toFixed(2)} />
                      <Metric label={t.goals} value={team.goals} />
                    </div>
                  </div>
                ))}
                <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm leading-relaxed text-emerald-950">
                  {t.xgNote}
                </p>
                <p className="text-xs leading-relaxed text-stone-500">
                  {data.xg.model_note}
                </p>
              </div>
              <div className="grid gap-4 sm:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
                <div
                  className="max-h-[360px] space-y-2 overflow-y-auto pr-1"
                  aria-label={t.shotsTitle}
                >
                  {data.xg.shots.map((item) => (
                    <button
                      key={item.id}
                      aria-pressed={selectedShotId === item.id}
                      onClick={() => setSelectedShotId(item.id)}
                      className={cn(
                        "flex min-h-14 w-full items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left",
                        selectedShotId === item.id
                          ? "border-emerald-700 bg-emerald-50"
                          : "border-stone-200 bg-white hover:border-emerald-400",
                      )}
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-medium">
                          {item.player_name}
                        </span>
                        <span className="text-xs text-stone-500">
                          {item.team_name}
                        </span>
                      </span>
                      <span className="shrink-0 text-sm font-semibold tabular-nums">
                        {item.xg.toFixed(2)} xG
                      </span>
                    </button>
                  ))}
                </div>
                {shot && (
                  <div className="rounded-xl border border-stone-200 bg-white p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
                      {t.selectedShot}
                    </p>
                    <h3 className="mt-2 text-lg font-semibold">
                      #{shot.id.slice(-2)} · {shot.player_name}
                    </h3>
                    <div className="mt-3 flex items-end gap-2">
                      <span className="text-4xl font-semibold tabular-nums text-emerald-900">
                        {shot.xg.toFixed(2)}
                      </span>
                      <span className="pb-1 text-sm text-stone-500">xG</span>
                    </div>
                    <div
                      className="mt-3 h-2 overflow-hidden rounded-full bg-stone-100"
                      role="meter"
                      aria-label={t.xg}
                      aria-valuemin={0}
                      aria-valuemax={1}
                      aria-valuenow={shot.xg}
                    >
                      <div
                        className="h-full rounded-full bg-emerald-700"
                        style={{ width: `${shot.xg * 100}%` }}
                      />
                    </div>
                    <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
                      <Metric
                        label={t.distance}
                        value={`${shot.distance_m.toFixed(1)} m`}
                      />
                      <Metric
                        label={t.angle}
                        value={`${shot.angle_deg.toFixed(0)}°`}
                      />
                      <Metric
                        label={t.bodyPart}
                        value={shot.body_part === "head" ? t.head : t.foot}
                      />
                      <Metric
                        label={t.pressureNearby}
                        value={shot.defenders_nearby}
                        detail={
                          t.keeper +
                          ": " +
                          (shot.keeper_out_of_position
                            ? t.keeperOut
                            : t.keeperSet)
                        }
                      />
                    </dl>
                  </div>
                )}
              </div>
            </div>
          </section>

          <section
            id="pressure"
            className="scroll-mt-5 rounded-2xl border border-stone-200 bg-white p-4 sm:p-6"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
                  02 · {t.pressure}
                </p>
                <h2 className="mt-2 text-xl font-semibold sm:text-2xl">
                  {t.pressureTitle}
                </h2>
              </div>
              <span className="rounded-full border border-stone-300 px-3 py-1 text-xs text-stone-600">
                {data.pressure.definition_version}
              </span>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <Metric label={t.episodes} value={data.pressure.summary.total} />
              <Metric
                label={t.known}
                value={`${data.pressure.summary.known} / ${data.pressure.summary.total}`}
              />
              <Metric
                label={t.regains}
                value={`${data.pressure.summary.regains} ${t.of} ${data.pressure.summary.known}`}
                detail={t.fiveSeconds}
              />
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr]">
              <div className="space-y-3 rounded-xl bg-stone-50 p-4">
                {[
                  ["pressing_team_regained", t.regained],
                  ["pressed_team_kept_and_progressed", t.progressed],
                  ["pressed_team_kept_no_clear_progress", t.held],
                  ["incomplete", t.incomplete],
                ].map(([key, label]) => {
                  const value = data.pressure.summary.outcomes[key] || 0;
                  return (
                    <div key={key}>
                      <div className="mb-1 flex justify-between gap-3 text-xs">
                        <span>{label}</span>
                        <span className="font-semibold tabular-nums">
                          {value}
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-stone-200">
                        <div
                          className="h-full rounded-full bg-emerald-700"
                          style={{ width: `${(value / maxOutcome) * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
                <p className="pt-1 text-xs leading-relaxed text-stone-600">
                  {data.pressure.definition}
                </p>
              </div>
              <div className="overflow-x-auto rounded-xl border border-stone-200">
                <table className="w-full min-w-[480px] text-left text-xs">
                  <caption className="p-3 text-left font-semibold">
                    {language === "es"
                      ? "Episodios observados · ventana de 5 s"
                      : "Observed episodes · 5 s window"}
                  </caption>
                  <thead className="bg-stone-50 text-stone-500">
                    <tr>
                      <th className="px-3 py-2">
                        {language === "es" ? "Presiona" : "Pressing team"}
                      </th>
                      <th className="px-3 py-2">
                        {language === "es" ? "Presionado" : "Pressed team"}
                      </th>
                      <th className="px-3 py-2">
                        {language === "es" ? "Cerca" : "Nearest"}
                      </th>
                      <th className="px-3 py-2">
                        {language === "es" ? "Desenlace" : "Outcome"}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.pressure.episodes.slice(0, 6).map((episode) => (
                      <tr
                        key={episode.id}
                        className="border-t border-stone-100"
                      >
                        <td className="px-3 py-2">{episode.pressing_team}</td>
                        <td className="px-3 py-2">{episode.pressured_team}</td>
                        <td className="px-3 py-2 tabular-nums">
                          {episode.distance_m.toFixed(1)} m
                        </td>
                        <td className="px-3 py-2">
                          {pressureOutcomeLabel(episode.outcome, language)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-stone-600">
              {t.pressureNote}
            </p>
          </section>

          <section
            id="shape"
            className="scroll-mt-5 rounded-2xl border border-stone-200 bg-[#f9fbfa] p-4 sm:p-6"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
                  03 · {t.shape}
                </p>
                <h2 className="mt-2 text-xl font-semibold sm:text-2xl">
                  {t.shapeTitle}
                </h2>
              </div>
              <div className="flex gap-2">
                {data.tactics.scenarios.map((item) => (
                  <button
                    key={item.id}
                    aria-pressed={scenarioId === item.id}
                    onClick={() => setScenarioId(item.id)}
                    className={cn(
                      "min-h-10 rounded-lg border px-3 text-sm font-medium",
                      scenarioId === item.id
                        ? "border-emerald-800 bg-emerald-800 text-white"
                        : "border-stone-300 bg-white text-stone-700",
                    )}
                  >
                    {item.id === "high-press" ? t.highPress : t.midBlock}
                  </button>
                ))}
              </div>
            </div>
            {scenario && (
              <div className="mt-4 grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
                <div className="rounded-xl border border-[#29463b] bg-[#173c2b] p-2 sm:p-3">
                  <svg
                    viewBox="0 0 600 390"
                    role="img"
                    aria-labelledby="shape-title shape-desc"
                    className="w-full"
                  >
                    <title id="shape-title">{t.pitchLabel}</title>
                    <desc id="shape-desc">
                      {scenario.label}: {scenario.team_length_m} m team length,{" "}
                      {scenario.team_width_m} m width; pressure starts at{" "}
                      {scenario.trigger_x_m} m.
                    </desc>
                    <rect
                      x="18"
                      y="18"
                      width="564"
                      height="354"
                      fill="#245841"
                      stroke="#d1fae5"
                      strokeOpacity=".7"
                    />
                    <path
                      d="M300 18v354M18 195h564"
                      stroke="#d1fae5"
                      strokeOpacity=".4"
                      fill="none"
                    />
                    <circle
                      cx="300"
                      cy="195"
                      r="45"
                      fill="none"
                      stroke="#d1fae5"
                      strokeOpacity=".4"
                    />
                    {scenario.frame.players.map((player) => (
                      <circle
                        key={player.player_id}
                        cx={28 + player.x_m * 5.18}
                        cy={30 + player.y_m * 4.86}
                        r={player.player_id === "away_08" ? 8 : 6}
                        fill={data.teams[player.team_id].color}
                        stroke="#fff"
                        strokeWidth="1.5"
                      >
                        <title>
                          {player.player_id} · {player.role}
                        </title>
                      </circle>
                    ))}
                    <circle
                      cx={28 + scenario.frame.ball.x_m * 5.18}
                      cy={30 + scenario.frame.ball.y_m * 4.86}
                      r="3.5"
                      fill="#fff"
                      stroke="#173c2b"
                      strokeWidth="1"
                    />
                  </svg>
                  <p className="px-2 pb-2 text-xs text-emerald-50/80">
                    {scenario.description}
                  </p>
                </div>
                <div>
                  <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-950">
                    {t.trigger}: {scenario.trigger_x_m.toFixed(0)} m ·{" "}
                    {scenario.trigger_zone} · {t.at} {scenario.trigger_time_s} s
                  </p>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <Metric
                      label={t.length}
                      value={`${scenario.team_length_m} m`}
                    />
                    <Metric
                      label={t.width}
                      value={`${scenario.team_width_m} m`}
                    />
                    <Metric
                      label={t.defense}
                      value={`${scenario.line_heights_m.defender} m`}
                    />
                    <Metric
                      label={t.midfield}
                      value={`${scenario.line_heights_m.midfielder} m`}
                    />
                  </div>
                  <div className="mt-3 rounded-xl border border-stone-200 bg-white p-3">
                    <h3 className="text-sm font-semibold">{t.gap}</h3>
                    <p className="mt-2 text-sm text-stone-600">
                      {t.defense} → {t.midfield}:{" "}
                      <strong>{scenario.line_gaps_m.defense_midfield} m</strong>
                    </p>
                    <p className="mt-1 text-sm text-stone-600">
                      {t.midfield} → {t.forwards}:{" "}
                      <strong>{scenario.line_gaps_m.midfield_forward} m</strong>
                    </p>
                  </div>
                  <p className="mt-3 text-xs leading-relaxed text-stone-600">
                    {t.shapeNote}
                  </p>
                </div>
              </div>
            )}
          </section>

          <section
            id="players"
            className="scroll-mt-5 rounded-2xl border border-stone-200 bg-white p-4 sm:p-6"
          >
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
                04 · {t.players}
              </p>
              <h2 className="mt-2 text-xl font-semibold sm:text-2xl">
                {t.playerTitle}
              </h2>
              <p className="mt-1 text-sm text-stone-600">{t.playerNote}</p>
            </div>
            <div className="mt-4 overflow-x-auto rounded-xl border border-stone-200">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="bg-stone-50 text-xs text-stone-600">
                  <tr>
                    <th className="px-3 py-3">
                      {language === "es" ? "Jugador / rol" : "Player / role"}
                    </th>
                    <th className="px-3 py-3">{t.progPasses}</th>
                    <th className="px-3 py-3">{t.recoveries}</th>
                    <th className="px-3 py-3">{t.shotsLabel}</th>
                    <th className="px-3 py-3">{t.playerXg}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.players.map((player) => (
                    <tr
                      key={player.player_id}
                      className="border-t border-stone-100"
                    >
                      <th scope="row" className="px-3 py-3 font-medium">
                        <span className="block">
                          #{player.number} {player.name}
                        </span>
                        <span className="text-xs font-normal text-stone-500">
                          {player.team_name} · {player.role_code}
                        </span>
                      </th>
                      <td className="px-3 py-3 tabular-nums">
                        {player.progressive_passes_completed}/
                        {player.progressive_passes_attempted}{" "}
                        <span className="text-xs text-stone-500">
                          {t.completed}/{t.attempted}
                        </span>
                      </td>
                      <td className="px-3 py-3 tabular-nums">
                        {player.recoveries}
                      </td>
                      <td className="px-3 py-3 tabular-nums">{player.shots}</td>
                      <td className="px-3 py-3 tabular-nums">
                        {player.xg.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-stone-500">
              {language === "es"
                ? "Pase progresivo: avance sintético de al menos 5 m hacia la portería rival. Los aportes se cuentan; no se convierten en una nota."
                : "Progressive pass: a synthetic pass moving at least 5 m toward the opponent goal. Contributions are counted; they are not converted into a rating."}
            </p>
          </section>

          <p className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-relaxed text-amber-950">
            <ShieldCheck
              size={18}
              className="mt-0.5 shrink-0"
              aria-hidden="true"
            />
            {t.allData}
          </p>
        </div>
      )}
      <footer className="mt-8 flex items-center justify-between border-t border-stone-200 pt-5 text-sm">
        <Link
          href="/"
          className="inline-flex min-h-11 items-center gap-2 font-medium text-emerald-900"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          {t.back}
        </Link>
        <span className="text-xs text-stone-500">{t.source}</span>
      </footer>
    </main>
  );
}
