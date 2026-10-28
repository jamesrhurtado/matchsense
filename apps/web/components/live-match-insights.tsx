"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, Clock3, Shield, Target, UsersRound } from "lucide-react";
import { api, timecode } from "@/lib/api";
import { Card, Tag } from "./ui";

type PlayerRow = {
  id: string;
  team_id: string;
  name: string;
  number: number;
  role: string;
  progressive_passes_completed: number;
  progressive_passes_attempted: number;
  passes_completed: number;
  recoveries: number;
  shots: number;
  confirmed_goals: number;
};

type ShotRow = {
  id: string;
  time_ms: number;
  team_id: string;
  team_name: string;
  player_id: string | null;
  player_name: string | null;
  outcome: string;
  xg: number | null;
  distance_m: number | null;
  angle_deg: number | null;
  nearby_defenders: number | null;
  body_part: string | null;
  play_type: string | null;
  reason: string | null;
};

type LiveInsights = {
  match_id: string;
  clock_ms: number;
  synthetic: true;
  progressive_pass_threshold_m: number;
  players: PlayerRow[];
  shots: ShotRow[];
  shooting: {
    teams: {
      team_id: string;
      team_name: string;
      shots: number;
      confirmed_goals: number;
      xg: number;
      xg_shots: number;
    }[];
    xg_model_version: string;
    xg_label: string;
    xg_note: string;
  };
  pressure: {
    definition: {
      radius_m: number;
      consecutive_frames: number;
      outcome_window_ms: number;
      progression_threshold_m: number;
      note: string;
    };
    episodes: {
      id: string;
      time_ms: number;
      pressing_team_id: string;
      pressured_team_id: string;
      carrier_id: string;
      outcome: string;
      progression_m: number | null;
      window_end_ms: number;
    }[];
    summary: {
      total: number;
      known: number;
      pending: number;
      incomplete: number;
      regains: number;
      outcomes: Record<string, number>;
    };
  };
};

const copy = {
  en: {
    title: "Match insights",
    subtitle: "Numbers from this match, updated as its feed arrives.",
    synthetic: "Synthetic match data",
    updated: "Through",
    loading: "Reading the match feed…",
    error: "Match metrics are unavailable right now.",
    shots: "Shots",
    goals: "Confirmed goals",
    xg: "xG",
    shotOutcomes: "Shooting summary",
    shotDetails: (count: number) => `Shot details · ${count}`,
    noShots: "No shots have been recorded yet.",
    waiting: "Waiting for result",
    goal: "Confirmed goal",
    pendingConfirmation: "Goal awaiting confirmation",
    cancelled: "Goal cancelled",
    unknown: "Result unavailable",
    saved: "Saved",
    blocked: "Blocked",
    offTarget: "Off target",
    players: "Player contributions",
    noPlayers: "Player contributions will appear when the feed records them.",
    progressive: "Progressive passes",
    progressiveHelp: (meters: number) =>
      `Completed / attempts · ${meters} m or more forward`,
    recoveries: "Recoveries",
    playerShots: "Shots",
    pressure: "Under pressure",
    pressureDetails: "Pressure details and recent episodes",
    pressureSummary: (
      known: number,
      progressed: number,
      held: number,
      regains: number,
    ) => {
      const kept = progressed + held;
      const parts = [
        kept
          ? `The team facing pressure kept the ball ${kept === known ? `in all ${known} recorded moments` : `in ${kept} of ${known} recorded moments`}${progressed ? ` and moved forward in ${progressed}` : ""}${held ? `, and made no clear progress in ${held}` : ""}.`
          : "",
        regains
          ? `The pressing team won the ball back in ${regains} recorded moments.`
          : "",
      ].filter(Boolean);
      return parts.join(" ");
    },
    noPressure: "No complete pressure episodes yet.",
    pressureHelp:
      "A pressure episode starts when an opponent is within 4 m for two observed frames. We observe the next five seconds; 5 m of forward ball movement counts as progress.",
    regains: "Pressing team gained possession",
    progressed: "Kept possession and progressed",
    held: "Kept possession, no clear progress",
    incomplete: "Incomplete evidence",
    pending: "Waiting for five second outcome",
    notEnough: "Not enough location or tracking data for an estimate",
  },
  es: {
    title: "Datos del partido",
    subtitle: "Cifras de este partido, actualizadas con su flujo de datos.",
    synthetic: "Datos sintéticos",
    updated: "Hasta",
    loading: "Leyendo los datos del partido…",
    error: "Los datos del partido no están disponibles ahora.",
    shots: "Remates",
    goals: "Goles confirmados",
    xg: "xG",
    shotOutcomes: "Resumen de remates",
    shotDetails: (count: number) => `Detalles de remates · ${count}`,
    noShots: "Todavía no se registraron remates.",
    waiting: "Esperando el resultado",
    goal: "Gol confirmado",
    pendingConfirmation: "Gol pendiente de confirmación",
    cancelled: "Gol anulado",
    unknown: "Resultado no disponible",
    saved: "Atajado",
    blocked: "Bloqueado",
    offTarget: "Desviado",
    players: "Aportes de jugadores",
    noPlayers: "Los aportes aparecerán cuando el flujo registre acciones.",
    progressive: "Pases progresivos",
    progressiveHelp: (meters: number) =>
      `Completados / intentos · al menos ${meters} m hacia delante`,
    recoveries: "Recuperaciones",
    playerShots: "Remates",
    pressure: "Bajo presión",
    pressureDetails: "Detalles de presión y episodios recientes",
    pressureSummary: (
      known: number,
      progressed: number,
      held: number,
      regains: number,
    ) => {
      const kept = progressed + held;
      const parts = [
        kept
          ? `El equipo que recibió la presión conservó el balón ${kept === known ? `en las ${known} jugadas con resultado registrado` : `en ${kept} de ${known} jugadas con resultado registrado`}${progressed ? ` y avanzó en ${progressed}` : ""}${held ? `; en ${held} no logró un avance claro` : ""}.`
          : "",
        regains
          ? `El equipo que presionaba recuperó el balón en ${regains} jugadas.`
          : "",
      ].filter(Boolean);
      return parts.join(" ");
    },
    noPressure: "Todavía no hay episodios de presión completos.",
    pressureHelp:
      "Un episodio empieza cuando un rival está a 4 m durante dos fotogramas observados. Se observan los cinco segundos siguientes; avanzar 5 m cuenta como progreso.",
    regains: "El equipo que presiona recuperó la posesión",
    progressed: "Conservó y avanzó",
    held: "Conservó sin avance claro",
    incomplete: "Evidencia incompleta",
    pending: "Esperando el resultado de cinco segundos",
    notEnough: "Faltan datos de ubicación o seguimiento para estimarlo",
  },
};

type CopyLabel = Exclude<
  keyof (typeof copy)["en"],
  "shotDetails" | "pressureSummary"
>;

const outcomeLabels: Record<string, CopyLabel> = {
  pending: "waiting",
  goal: "goal",
  pending_confirmation: "pendingConfirmation",
  cancelled: "cancelled",
  unknown: "unknown",
  saved: "saved",
  blocked: "blocked",
  off_target: "offTarget",
};

const pressureLabels: Record<string, CopyLabel> = {
  pressing_team_gained_possession: "regains",
  pressured_team_kept_and_progressed: "progressed",
  pressured_team_kept_no_clear_progress: "held",
  incomplete: "incomplete",
  pending: "pending",
};

function xgValue(value: number | null) {
  return value === null ? "—" : value.toFixed(2);
}

export function LiveMatchInsights({
  sessionId,
  clockMs,
  language,
}: {
  sessionId: string;
  clockMs: number;
  language: string;
}) {
  const [result, setResult] = useState<{
    key: string;
    data?: LiveInsights;
    error?: string;
  } | null>(null);
  const es = language === "es";
  const t = copy[es ? "es" : "en"];
  const key = `${sessionId}:${Math.floor(clockMs / 1000)}`;
  const label = (name: string) => {
    const value = t[name as keyof typeof t];
    return typeof value === "string" ? value : "";
  };

  useEffect(() => {
    const controller = new AbortController();
    api<LiveInsights>(`/replay-sessions/${sessionId}/insights`, {
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted) setResult({ key, data });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setResult({ key, error: error.message });
      });
    return () => controller.abort();
  }, [key, sessionId]);

  const data = result?.key === key ? result.data : undefined;
  const error = result?.key === key ? result.error : undefined;
  const activePlayers = useMemo(
    () =>
      (data?.players || []).slice().sort((a, b) => {
        const teamOrder = a.team_id.localeCompare(b.team_id);
        return teamOrder || a.number - b.number;
      }),
    [data?.players],
  );

  return (
    <Card id="live-match-insights" className="mt-5 overflow-hidden">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-[#d9e3dd] bg-[#f6f9f7] px-4 py-4 md:px-6">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-[#172721]">
            <Activity size={18} aria-hidden="true" /> {t.title}
          </h2>
          <p className="mt-1 text-sm text-stone-600">{t.subtitle}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {data && (
            <Tag className="bg-white">
              <Clock3 size={13} aria-hidden="true" /> {t.updated}{" "}
              {timecode(data.clock_ms)}
            </Tag>
          )}
          <Tag className="border-amber-200 bg-amber-50 text-amber-900">
            {t.synthetic}
          </Tag>
        </div>
      </header>

      {error && (
        <p
          role="alert"
          className="m-4 rounded-lg bg-red-50 p-3 text-sm text-red-800 md:m-6"
        >
          {t.error}
        </p>
      )}
      {!data && !error && (
        <p className="p-5 text-sm text-stone-600" role="status">
          {t.loading}
        </p>
      )}
      {data && (
        <div className="space-y-6 p-4 md:p-6">
          <section aria-labelledby="live-shooting-heading">
            <div className="mb-3 flex items-center gap-2">
              <Target
                size={17}
                className="text-emerald-800"
                aria-hidden="true"
              />
              <h3
                id="live-shooting-heading"
                className="font-semibold text-[#172721]"
              >
                {t.shotOutcomes}
              </h3>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {data.shooting.teams.map((team) => (
                <div
                  key={team.team_id}
                  className="rounded-xl border border-stone-200 p-4"
                >
                  <p className="font-semibold text-[#172721]">
                    {team.team_name}
                  </p>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p className="text-xs text-stone-500">{t.shots}</p>
                      <p className="mt-1 text-xl font-semibold tabular-nums">
                        {team.shots}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">{t.goals}</p>
                      <p className="mt-1 text-xl font-semibold tabular-nums">
                        {team.confirmed_goals}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">{t.xg}</p>
                      <p className="mt-1 text-xl font-semibold tabular-nums">
                        {xgValue(team.xg_shots ? team.xg : null)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {data.shots.length ? (
              <details className="mt-3 overflow-hidden rounded-xl border border-stone-200">
                <summary className="min-h-12 cursor-pointer bg-[#f6f9f7] px-4 py-3 text-sm font-semibold text-[#172721]">
                  {t.shotDetails(data.shots.length)}
                </summary>
                <div className="p-3 md:p-4">
                  <ul className="divide-y divide-stone-100 rounded-lg border border-stone-200">
                    {data.shots
                      .slice(-8)
                      .reverse()
                      .map((shot) => {
                        const outcomeKey =
                          outcomeLabels[shot.outcome] || "unknown";
                        const details = [
                          shot.body_part === "head"
                            ? es
                              ? "Cabeza"
                              : "Header"
                            : shot.body_part
                              ? es
                                ? "Pie"
                                : "Foot"
                              : null,
                          shot.play_type?.replaceAll("_", " "),
                          shot.distance_m !== null
                            ? `${shot.distance_m.toFixed(1)} m`
                            : null,
                          shot.angle_deg !== null
                            ? `${shot.angle_deg.toFixed(1)}°`
                            : null,
                          shot.nearby_defenders !== null
                            ? `${shot.nearby_defenders} ${es ? "rivales a 4 m" : "opponents within 4 m"}`
                            : null,
                        ].filter(Boolean);
                        return (
                          <li
                            key={shot.id}
                            className="flex flex-wrap items-center justify-between gap-2 px-3 py-3 text-sm md:px-4"
                          >
                            <div className="min-w-0">
                              <p className="truncate font-medium text-[#172721]">
                                {shot.player_name ||
                                  (es
                                    ? "Jugador no identificado"
                                    : "Unidentified player")}
                                <span className="font-normal text-stone-500">
                                  {" "}
                                  · {shot.team_name} · {timecode(shot.time_ms)}
                                </span>
                              </p>
                              <p className="mt-1 text-xs text-stone-600">
                                {label(outcomeKey)}
                                {shot.reason ? ` · ${t.notEnough}` : ""}
                              </p>
                              {details.length > 0 && (
                                <p className="mt-1 text-xs text-stone-500">
                                  {details.join(" · ")}
                                </p>
                              )}
                            </div>
                            {shot.xg !== null && (
                              <span className="shrink-0 rounded-full bg-[#edf4ef] px-3 py-1 font-semibold tabular-nums text-[#194b37]">
                                {t.xg} {xgValue(shot.xg)}
                              </span>
                            )}
                          </li>
                        );
                      })}
                  </ul>
                </div>
              </details>
            ) : (
              <p className="mt-3 rounded-xl border border-dashed border-stone-300 p-4 text-sm text-stone-600">
                {t.noShots}
              </p>
            )}
          </section>

          <section aria-labelledby="live-pressure-heading">
            <div className="mb-3 flex items-center gap-2">
              <Shield
                size={17}
                className="text-emerald-800"
                aria-hidden="true"
              />
              <h3
                id="live-pressure-heading"
                className="font-semibold text-[#172721]"
              >
                {t.pressure}
              </h3>
            </div>
            {data.pressure.summary.known ? (
              <>
                <p className="text-sm leading-relaxed text-stone-700">
                  {t.pressureSummary(
                    data.pressure.summary.known,
                    data.pressure.summary.outcomes[
                      "pressured_team_kept_and_progressed"
                    ] || 0,
                    data.pressure.summary.outcomes[
                      "pressured_team_kept_no_clear_progress"
                    ] || 0,
                    data.pressure.summary.outcomes[
                      "pressing_team_gained_possession"
                    ] || 0,
                  )}
                </p>
                <details className="mt-3 overflow-hidden rounded-xl border border-stone-200">
                  <summary className="min-h-12 cursor-pointer bg-[#f6f9f7] px-4 py-3 text-sm font-semibold text-[#172721]">
                    {t.pressureDetails}
                  </summary>
                  <div className="space-y-3 p-3 md:p-4">
                    <ul className="grid gap-2 sm:grid-cols-2">
                      {Object.entries(data.pressure.summary.outcomes)
                        .filter(([, count]) => count > 0)
                        .map(([outcome, count]) => {
                          const labelKey =
                            pressureLabels[outcome] || "incomplete";
                          return (
                            <li
                              key={outcome}
                              className="flex items-center justify-between gap-3 rounded-lg bg-[#f6f9f7] px-3 py-3 text-sm"
                            >
                              <span className="text-stone-700">
                                {label(labelKey)}
                              </span>
                              <span className="font-semibold tabular-nums text-[#172721]">
                                {count}
                              </span>
                            </li>
                          );
                        })}
                    </ul>
                    <p className="text-xs leading-relaxed text-stone-600">
                      {t.pressureHelp}
                    </p>
                    {!!data.pressure.episodes.length && (
                      <ul className="divide-y divide-stone-100 rounded-xl border border-stone-200">
                        {data.pressure.episodes
                          .slice(-4)
                          .reverse()
                          .map((episode) => {
                            const outcomeKey =
                              pressureLabels[episode.outcome] || "incomplete";
                            const pressingTeam =
                              data.shooting.teams.find(
                                (team) =>
                                  team.team_id === episode.pressing_team_id,
                              )?.team_name || episode.pressing_team_id;
                            const pressuredTeam =
                              data.shooting.teams.find(
                                (team) =>
                                  team.team_id === episode.pressured_team_id,
                              )?.team_name || episode.pressured_team_id;
                            return (
                              <li
                                key={episode.id}
                                className="flex flex-wrap items-center justify-between gap-2 px-3 py-3 text-sm md:px-4"
                              >
                                <span className="text-stone-700">
                                  {timecode(episode.time_ms)} · {pressingTeam}{" "}
                                  {es ? "presiona a" : "presses"}{" "}
                                  {pressuredTeam}
                                </span>
                                <span className="font-medium text-[#172721]">
                                  {label(outcomeKey)}
                                </span>
                              </li>
                            );
                          })}
                      </ul>
                    )}
                  </div>
                </details>
              </>
            ) : (
              <p className="rounded-xl border border-dashed border-stone-300 p-4 text-sm text-stone-600">
                {t.noPressure}
              </p>
            )}
          </section>

          <details className="overflow-hidden rounded-xl border border-stone-200">
            <summary className="flex min-h-12 cursor-pointer items-center gap-2 bg-[#f6f9f7] px-4 py-3 text-sm font-semibold text-[#172721]">
              <UsersRound
                size={17}
                className="text-emerald-800"
                aria-hidden="true"
              />
              {t.players}
            </summary>
            <div className="space-y-3 p-3 md:p-4">
              {activePlayers.length ? (
                <div className="overflow-x-auto rounded-xl border border-stone-200">
                  <table className="w-full min-w-[620px] text-left text-sm">
                    <thead className="bg-[#f6f9f7] text-xs text-stone-600">
                      <tr>
                        <th className="px-3 py-3 font-medium">
                          {es ? "Jugador" : "Player"}
                        </th>
                        <th className="px-3 py-3 font-medium">
                          {t.progressive}
                        </th>
                        <th className="px-3 py-3 font-medium">
                          {t.recoveries}
                        </th>
                        <th className="px-3 py-3 font-medium">
                          {t.playerShots}
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100">
                      {activePlayers.map((player) => (
                        <tr key={player.id}>
                          <th
                            scope="row"
                            className="px-3 py-3 font-medium text-[#172721]"
                          >
                            {player.name}{" "}
                            <span className="text-stone-500">
                              #{player.number}
                            </span>
                            <span className="mt-0.5 block text-xs font-normal text-stone-500">
                              {data.shooting.teams.find(
                                (team) => team.team_id === player.team_id,
                              )?.team_name || player.team_id}
                            </span>
                          </th>
                          <td className="px-3 py-3 tabular-nums">
                            {player.progressive_passes_completed} /{" "}
                            {player.progressive_passes_attempted}
                          </td>
                          <td className="px-3 py-3 tabular-nums">
                            {player.recoveries}
                          </td>
                          <td className="px-3 py-3 tabular-nums">
                            {player.shots}
                            {player.confirmed_goals
                              ? ` · ${player.confirmed_goals} ${es ? "gol" : "goal"}`
                              : ""}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="rounded-xl border border-dashed border-stone-300 p-4 text-sm text-stone-600">
                  {t.noPlayers}
                </p>
              )}
              <p className="text-xs leading-relaxed text-stone-500">
                {t.progressiveHelp(data.progressive_pass_threshold_m)}
              </p>
            </div>
          </details>
        </div>
      )}
    </Card>
  );
}
