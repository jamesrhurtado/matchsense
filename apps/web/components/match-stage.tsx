import { Check, ChevronDown, Pause, Radio, ShieldCheck } from "lucide-react";
import { Match, timecode } from "@/lib/api";
import Pitch, { ballOverlapsPlayer, observedBallCarrier } from "./pitch";
import styles from "./match-stage.module.css";
import { MatchSenseBrand } from "./match-sense-brand";

function ClubBadge({ away = false }: { away?: boolean }) {
  return (
    <svg viewBox="0 0 48 56" className={styles.badge} aria-hidden="true">
      <path
        d="M3 3h42v27c0 12-21 23-21 23S3 42 3 30Z"
        fill={away ? "#f4c466" : "#87c3ff"}
      />
      <path d="M7 7h34v22c0 9-17 19-17 19S7 38 7 29Z" fill="#132535" />
      {away ? (
        <path d="m24 12-9 12h5l-8 10h10v8h4v-8h10l-8-10h5Z" fill="#f4c466" />
      ) : (
        <g fill="none" stroke="#87c3ff" strokeWidth="2.5">
          <path d="M24 12v20m-7-14h14M14 29c0 12 20 12 20 0m-20 0-3 5m23-5 3 5" />
          <path d="M13 40q5-4 11 0t11 0" />
        </g>
      )}
    </svg>
  );
}

export function MatchStage({
  match,
  language,
  expired,
  showExplanation = true,
  broadcastOutput = false,
}: {
  match: Match | null;
  language: string;
  expired: boolean;
  showExplanation?: boolean;
  broadcastOutput?: boolean;
}) {
  const es = language === "es";
  const elapsed = match?.clock_ms ?? 0;
  const duration = match?.duration_ms ?? 60000;
  const complete = elapsed >= duration;
  const clock = timecode(match?.match_state?.period_elapsed_ms ?? elapsed);
  const controlTeam = match?.teams.find(
    (team) => team.id === match.frame?.possession_team_id,
  );
  return (
    <section
      className={`${styles.stage} ${broadcastOutput ? styles.broadcastOutput : ""}`}
      aria-label={es ? "Centro del partido" : "Match centre"}
    >
      <div className={styles.masthead}>
        <span className={styles.wordmark}>
          <MatchSenseBrand dark />{" "}
          <span className={styles.channel}>{es ? "Partido" : "Matchday"}</span>
        </span>
      </div>
      <div
        className={styles.scoreboard}
        data-testid={match?.coverage_enabled ? "match-state" : undefined}
      >
        <div className={styles.club}>
          <ClubBadge />
          <div>
            <span className={styles.clubName}>
              {match?.teams.find((t) => t.id === "blue")?.name ?? "Club del Faro"}
            </span>
            <span className={styles.clubCode}>
              FAR <i className={styles.homeDot} />
            </span>
          </div>
        </div>
        <div className={styles.scoreCentre}>
          <span className={styles.score}>
            {match?.score?.blue ?? "—"} : {match?.score?.amber ?? "—"}
          </span>
          <span className={styles.clock}>
            <time>{clock}</time>{" "}
            <span>· P{match?.match_state?.period ?? 1}</span>
          </span>
        </div>
        <div className={`${styles.club} ${styles.away}`}>
          <ClubBadge away />
          <div>
            <span className={styles.clubName}>
              {match?.teams.find((t) => t.id === "amber")?.name ??
                "Puerto Lumbre FC"}
            </span>
            <span className={styles.clubCode}>
              <i className={styles.awayDot} /> LUM
            </span>
          </div>
        </div>
      </div>
      <div className={styles.matchMeta}>
        <span className={styles.playState}>
          {match?.running ? <Radio size={12} /> : <Pause size={12} />}
          {complete
            ? es
              ? "Segmento completo"
              : "Segment complete"
            : match?.running
              ? es
                ? "En curso"
                : match?.session_mode === "live"
                  ? "Simulation running"
                  : "Replay running"
              : es
                ? "En pausa"
                : match?.session_mode === "live"
                  ? "Simulation stopped"
                  : "Replay paused"}
          {match && match.speed !== 1 && ` · ${match.speed}×`}
        </span>
      </div>
      <div className={styles.field}>
        <Pitch
          frame={match?.frame ?? null}
          motionFromFrame={match?.motion_from_frame}
          motionDurationMs={match?.motion_duration_ms}
          players={match?.players ?? []}
          teamNames={Object.fromEntries(
            (match?.teams ?? []).map((team) => [team.id, team.name]),
          )}
          language={language}
          broadcast
        />
        <div className={styles.fieldLegend}>
          <span>
            <i
              className={
                controlTeam?.id === "blue"
                  ? styles.homeDot
                  : controlTeam?.id === "amber"
                    ? styles.awayDot
                    : styles.neutralDot
              }
            />
            {controlTeam
              ? `${es ? "Control" : "In control"}: ${controlTeam.name}`
              : es
                ? "Sin control de equipo observado"
                : "No observed team control"}
          </span>
          <span>
            <i className={styles.ballDot} />
            {es ? "Balón" : "Ball"}
          </span>
        </div>
        <div className={styles.keeperLegend}>
          <span>
            <i className={styles.homeKeeper} />
            {es ? "Portero FAR" : "FAR goalkeeper"}
          </span>
          <span>
            <i className={styles.awayKeeper} />
            {es ? "Portero LUM" : "LUM goalkeeper"}
          </span>
        </div>
        <p className={styles.fieldNote}>
          {observedBallCarrier(match?.frame ?? null)
            ? es
              ? "La insignia de balón identifica al jugador con control observado."
              : "The ball badge identifies the observed ball carrier."
            : ballOverlapsPlayer(match?.frame ?? null)
              ? es
                ? "La línea del balón señala su posición observada."
                : "The ball’s line points to its observed position."
              : es
                ? "El balón muestra su posición observada."
                : "The ball shows its observed position."}
        </p>
      </div>
      <div
        className={styles.progress}
        role="progressbar"
        aria-label={es ? "Progreso del segmento" : "Segment progress"}
        aria-valuemin={0}
        aria-valuemax={duration}
        aria-valuenow={Math.min(elapsed, duration)}
        aria-valuetext={`${timecode(elapsed)} / ${timecode(duration)}`}
      >
        <span
          style={{ width: `${Math.min(100, (elapsed / duration) * 100)}%` }}
        />
      </div>
      {showExplanation && (
        <div className={styles.lowerThird}>
          <div className={styles.momentIcon}>
            {match?.overlay ? <Radio size={22} /> : <ShieldCheck size={22} />}
          </div>
          <div className={styles.momentBody}>
            <div className={styles.momentHeading}>
              <span>{es ? "En la transmisión" : "On the broadcast"}</span>
              {match?.overlay && (
                <span className={styles.approved}>
                  <Check size={12} />
                  {es ? "Aprobado" : "Producer approved"}
                </span>
              )}
            </div>
            {match?.overlay ? (
              <p className={styles.explanation}>{match.overlay}</p>
            ) : (
              <p className={styles.empty}>
                {expired
                  ? es
                    ? "Terminó el intervalo en pantalla. El momento aprobado sigue disponible en el historial."
                    : "Display interval ended. The approved moment remains available in the companion."
                  : es
                    ? "Las historias aprobadas aparecen aquí durante su intervalo de repetición."
                    : match?.session_mode === "live"
                      ? "Producer-approved insights appear here while the match unfolds."
                      : "Approved stories appear here at their eligible replay time."}
              </p>
            )}
            <details className={styles.policy}>
              <summary>
                {es ? "Cómo se elige este texto" : "How this text is selected"}
                <ChevronDown size={12} />
              </summary>
              <p>
                {es
                  ? "Las explicaciones requieren aprobación del productor. "
                  : "Explanations require producer approval. "}
                {match?.overlay_selection_reason?.[language]}
              </p>
            </details>
          </div>
        </div>
      )}
    </section>
  );
}
