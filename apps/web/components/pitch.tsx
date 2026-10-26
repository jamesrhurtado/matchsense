"use client";

import { useId, useState } from "react";
import type { CSSProperties, KeyboardEvent } from "react";
import { Frame, Metrics, Player } from "@/lib/api";
import styles from "./pitch.module.css";
export function ballOverlapsPlayer(frame: Frame | null) {
  return Boolean(
    frame?.ball &&
    frame.players.some(
      (p) => Math.hypot(p.x_m - frame.ball!.x_m, p.y_m - frame.ball!.y_m) < 3,
    ),
  );
}

export function observedBallCarrier(frame: Frame | null) {
  if (!frame?.ball || !frame.controlling_player_id) return undefined;
  return frame.players.find(
    (p) =>
      p.player_id === frame.controlling_player_id &&
      Math.hypot(p.x_m - frame.ball!.x_m, p.y_m - frame.ball!.y_m) < 3,
  );
}

export default function Pitch({
  frame,
  motionFromFrame,
  motionDurationMs,
  metrics,
  focus,
  compact = false,
  trails = [],
  highlight = "all",
  language = "en",
  broadcast = false,
  players = [],
  teamNames = {},
}: {
  players?: Player[];
  teamNames?: Record<string, string>;
  broadcast?: boolean;
  frame: Frame | null;
  motionFromFrame?: Frame | null;
  motionDurationMs?: number | null;
  metrics?: Metrics;
  focus?: string | null;
  compact?: boolean;
  language?: string;
  highlight?: string;
  trails?: { x_m: number; y_m: number }[][];
}) {
  const es = language === "es";
  const uid = useId().replace(/:/g, "");
  const [hoveredPlayerId, setHoveredPlayerId] = useState<string | null>(null);
  const [selectedPlayerId, setSelectedPlayerId] = useState<string | null>(null);
  const previousPlayerIds = new Set(
    motionFromFrame?.players.map((player) => player.player_id) ?? [],
  );
  const motionStyle = motionDurationMs
    ? ({
        "--frame-motion-duration": `${motionDurationMs}ms`,
      } as CSSProperties)
    : undefined;
  const carrier = broadcast ? observedBallCarrier(frame) : undefined;
  const ballLinked = broadcast && !carrier && ballOverlapsPlayer(frame);
  const ball = frame?.ball;
  // Only the ball symbol is offset. The dot and leader preserve its source position.
  const offset =
    ballLinked && ball
      ? ([
          [-3.5, -3.5],
          [3.5, -3.5],
          [-3.5, 3.5],
          [3.5, 3.5],
        ]
          .filter(
            ([x, y]) =>
              ball.x_m + x >= 0 &&
              ball.x_m + x <= 105 &&
              ball.y_m + y >= 0 &&
              ball.y_m + y <= 68,
          )
          .sort((a, b) => {
            const clearance = (d: number[]) =>
              Math.min(
                ...frame!.players.map((p) =>
                  Math.hypot(p.x_m - ball.x_m - d[0], p.y_m - ball.y_m - d[1]),
                ),
              );
            return clearance(b) - clearance(a);
          })[0] ?? [0, 0])
      : [0, 0];
  const keeperCarrier =
    players.find((p) => p.id === carrier?.player_id)?.role === "keeper";
  const badgeDx = keeperCarrier ? 2.7 : 2.3;
  const badgeDy = keeperCarrier ? 2.3 : 1.8;
  const badgeCorners = carrier
    ? [
        [badgeDx, badgeDy],
        [-badgeDx, badgeDy],
        [badgeDx, -badgeDy],
        [-badgeDx, -badgeDy],
      ].filter(
        ([x, y]) =>
          carrier.x_m + x >= 0 &&
          carrier.x_m + x <= 105 &&
          carrier.y_m + y >= 0 &&
          carrier.y_m + y <= 68,
      )
    : [];
  const badgeClearance = ([x, y]: number[]) =>
    Math.min(
      ...(frame?.players ?? [])
        .filter((p) => p.player_id !== carrier?.player_id)
        .map((p) =>
          Math.hypot(p.x_m - carrier!.x_m - x, p.y_m - carrier!.y_m - y),
        ),
    );
  // Prefer a stable corner; move only when another player would obscure the badge.
  const badgeOffset = badgeCorners.find((p) => badgeClearance(p) >= 2.6) ??
    badgeCorners.sort((a, b) => badgeClearance(b) - badgeClearance(a))[0] ?? [
      badgeDx,
      badgeDy,
    ];
  const ballX = carrier
    ? carrier.x_m + 5 + badgeOffset[0]
    : (ball?.x_m ?? 0) + 5 + offset[0];
  const ballY = carrier
    ? carrier.y_m + 5 + badgeOffset[1]
    : (ball?.y_m ?? 0) + 5 + offset[1];
  const ballRadius = carrier ? 0.85 : 1.15;
  const activePlayerId = hoveredPlayerId ?? selectedPlayerId;
  const activePlayer = players.find((player) => player.id === activePlayerId);
  const activeTeamName = activePlayer
    ? (teamNames[activePlayer.team_id] ?? activePlayer.team_id)
    : "";
  const identityText = activePlayer
    ? `${es ? "Jugador" : "Player"} #${activePlayer.number} ${activePlayer.name} · ${activeTeamName}${
        activePlayer.role === "keeper"
          ? ` · ${es ? "Portero" : "Goalkeeper"}`
          : ""
      }`
    : null;
  const broadcastBall =
    ball && broadcast ? (
      <g
        data-testid="broadcast-ball"
        className={motionFromFrame?.ball ? styles.movingMarker : undefined}
        style={motionStyle}
        data-carrier-id={carrier?.player_id}
        data-source-x={ball.x_m}
        data-source-y={ball.y_m}
      >
        <title>
          {carrier
            ? es
              ? "Insignia de balón junto al jugador con control observado; las coordenadas exactas se conservan en la evidencia."
              : "Ball badge beside the observed carrier; exact coordinates are preserved in the evidence."
            : ballLinked
              ? es
                ? "Balón: la línea termina en su posición observada; el símbolo está separado para mostrar al jugador."
                : "Ball: the line ends at its observed position; the symbol is offset to reveal the player."
              : es
                ? "Posición observada del balón"
                : "Observed ball position"}
        </title>
        {ballLinked && (
          <>
            <line
              data-testid="ball-position-link"
              className={motionFromFrame?.ball ? styles.movingLink : undefined}
              x1={ball.x_m + 5}
              y1={ball.y_m + 5}
              x2={ballX}
              y2={ballY}
              stroke="white"
              strokeWidth=".25"
              strokeDasharray=".5 .4"
            />
            <circle
              data-testid="ball-observed-position"
              cx={ball.x_m + 5}
              cy={ball.y_m + 5}
              r=".3"
              fill="white"
              stroke="#11252d"
              strokeWidth=".1"
            />
          </>
        )}
        <circle
          cx={ballX}
          cy={ballY}
          r={ballRadius + 0.3}
          fill="#0b191f"
          opacity=".5"
        />
        <circle
          data-testid="ball-symbol"
          cx={ballX}
          cy={ballY}
          r={ballRadius}
          fill="white"
          stroke="#10232c"
          strokeWidth=".2"
        />
        <path
          className={motionFromFrame?.ball ? styles.movingBallIcon : undefined}
          transform={`translate(${ballX} ${ballY})`}
          d={`M0 ${-ballRadius * 0.48}l${ballRadius * 0.45} ${ballRadius * 0.33}-${ballRadius * 0.17} ${ballRadius * 0.53}h-${ballRadius * 0.56}l-${ballRadius * 0.17}-${ballRadius * 0.53}Z`}
          fill="#23333e"
        />
      </g>
    ) : null;
  const position = (x: number, y: number) => ({ x: x + 5, y: y + 5 });
  return (
    <>
      <svg
        viewBox="0 0 115 78"
        role="img"
        aria-label={
          metrics
            ? es
              ? "Cancha con desplazamiento medido del pase y posiciones registradas"
              : "Evidence pitch with measured pass displacement and recorded positions"
            : es
              ? "Cancha sintética con 22 jugadores ficticios"
              : "Synthetic football pitch with 22 fictional players"
        }
        className="block w-full"
      >
        <defs>
          <radialGradient id={`${uid}-grass`} cx="50%" cy="40%" r="70%">
            <stop offset="0" stopColor="#2f7259" />
            <stop offset="1" stopColor="#153f35" />
          </radialGradient>
          <radialGradient id={`${uid}-light`}>
            <stop offset="0" stopColor="#d2f5de" stopOpacity=".07" />
            <stop offset="1" stopColor="#d2f5de" stopOpacity="0" />
          </radialGradient>
          <linearGradient id={`${uid}-blue`} x2="0" y2="1">
            <stop stopColor="#c4e6ff" />
            <stop offset="1" stopColor="#69adf3" />
          </linearGradient>
          <linearGradient id={`${uid}-amber`} x2="0" y2="1">
            <stop stopColor="#ffe4a2" />
            <stop offset="1" stopColor="#e6ae45" />
          </linearGradient>
          <pattern
            id={`${uid}-grain`}
            width=".8"
            height=".8"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M0 .2H.3M.4 .6H.7"
              stroke="#c4efcb"
              strokeWidth=".05"
              opacity=".14"
            />
          </pattern>
          <marker
            id={`${uid}-arrow`}
            markerWidth="5"
            markerHeight="5"
            refX="4"
            refY="2.5"
            orient="auto"
          >
            <path d="M0 0 L5 2.5 L0 5" fill="#ffffff" />
          </marker>
        </defs>
        <rect
          width="115"
          height="78"
          fill={broadcast ? "#0b191f" : "#153d32"}
        />
        {broadcast && (
          <rect
            x="3.8"
            y="3.8"
            width="107.4"
            height="70.4"
            rx=".6"
            fill={`url(#${uid}-grass)`}
            stroke="#7bab9133"
            strokeWidth=".15"
          />
        )}
        {Array.from({ length: 7 }, (_, i) => (
          <rect
            key={i}
            x={5 + i * 15}
            y="5"
            width="15"
            height="68"
            fill={
              broadcast
                ? i % 2 === 0
                  ? "#ffffff04"
                  : "#0000000a"
                : i % 2 === 0
                  ? "#1a483b"
                  : "#1d4e40"
            }
          />
        ))}
        {broadcast && (
          <>
            <rect
              x="5"
              y="5"
              width="105"
              height="68"
              fill={`url(#${uid}-grain)`}
            />
            <rect
              x="5"
              y="5"
              width="105"
              height="68"
              fill={`url(#${uid}-light)`}
            />
          </>
        )}
        <g
          fill="none"
          stroke={broadcast ? "#c0dccb" : "#99b8a3"}
          strokeWidth={broadcast ? ".2" : ".25"}
          opacity={broadcast ? ".5" : ".65"}
        >
          <rect x="5" y="5" width="105" height="68" />
          <path d="M57.5 5V73" />
          <circle cx="57.5" cy="39" r="9.15" />
          {broadcast && (
            <>
              <circle cx="57.5" cy="39" r=".3" fill="#c0dccb" />
              <circle cx="16" cy="39" r=".22" fill="#c0dccb" />
              <circle cx="99" cy="39" r=".22" fill="#c0dccb" />
              <path d="M21.5 31.69a9.15 9.15 0 0 1 0 14.62M93.5 31.69a9.15 9.15 0 0 0 0 14.62" />
              <path d="M5 6a1 1 0 0 0 1-1M109 5a1 1 0 0 0 1 1M5 72a1 1 0 0 1 1 1M109 73a1 1 0 0 1 1-1" />
            </>
          )}
          <rect x="5" y="18.84" width="16.5" height="40.32" />
          <rect x="93.5" y="18.84" width="16.5" height="40.32" />
          <rect x="5" y="29.84" width="5.5" height="18.32" />
          <rect x="104.5" y="29.84" width="5.5" height="18.32" />
          <rect x="3.5" y="35.34" width="1.5" height="7.32" />
          <rect x="110" y="35.34" width="1.5" height="7.32" />
        </g>
        {metrics && (highlight === "c-zone" || highlight === "c-reception") && (
          <rect
            x={
              metrics.pass_end.x_m < 35
                ? 5
                : metrics.pass_end.x_m < 70
                  ? 40
                  : 75
            }
            y={5}
            width={35}
            height={68}
            fill="#a7f3d022"
            stroke="#a7f3d0"
            strokeWidth=".6"
            strokeDasharray="2 1"
          >
            <title>{es ? "Tercio de recepción" : "Reception third"}</title>
          </rect>
        )}
        {metrics && (
          <g>
            {(highlight === "all" || highlight === "c-pressure") && (
              <circle
                cx={metrics.pass_start.x_m + 5}
                cy={metrics.pass_start.y_m + 5}
                r={metrics.pressure_radius_m}
                fill="#fbbf2422"
                stroke="#fcd34d"
                strokeWidth=".25"
                strokeDasharray="1 1"
              />
            )}
            {[
              "all",
              "c-forward",
              "c-context",
              "c-release",
              "c-bypass",
            ].includes(highlight) && (
              <path
                d={`M${metrics.pass_start.x_m + 5} ${metrics.pass_start.y_m + 5} L${metrics.pass_end.x_m + 5} ${metrics.pass_end.y_m + 5}`}
                stroke="white"
                strokeWidth=".6"
                strokeDasharray="1 1"
                markerEnd={`url(#${uid}-arrow)`}
              />
            )}
          </g>
        )}
        {trails.map((points, index) => (
          <polyline
            key={index}
            points={points
              .map((point) => `${point.x_m + 5},${point.y_m + 5}`)
              .join(" ")}
            fill="none"
            stroke="#a7f3d0"
            strokeWidth=".6"
            opacity=".85"
          >
            <title>
              {es
                ? "Posiciones observadas; los intervalos sin datos no se unen"
                : "Observed player positions; gaps are not connected"}
            </title>
          </polyline>
        ))}
        {/* Free-ball source anchors are behind players, keeping shirt numbers clear. */}
        {!carrier && broadcastBall}
        {frame?.players.map((p) => {
          const q = position(p.x_m, p.y_m);
          const player = players.find((player) => player.id === p.player_id);
          const keeper = broadcast && player?.role === "keeper";
          const keeperColor = p.team_id === "blue" ? "#d7c7ff" : "#ffa9a4";
          const interactive = broadcast;
          const selected = selectedPlayerId === p.player_id;
          const shirtNumber =
            player?.number ?? parseInt(p.player_id.split("-")[1]);
          const teamName =
            teamNames[p.team_id] ??
            (p.team_id === "blue" ? "Harbor City" : "Alder Rovers");
          const playerLabel = `${es ? "Jugador" : "Player"} #${shirtNumber}, ${player?.name ?? (es ? "nombre no disponible" : "name unavailable")}, ${teamName}${keeper ? (es ? ", portero" : ", goalkeeper") : ""}`;
          const activate = () =>
            setSelectedPlayerId((current) =>
              current === p.player_id ? null : p.player_id,
            );
          const handleKeyDown = (event: KeyboardEvent<SVGGElement>) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              activate();
            }
          };
          const highlighted =
            (["all", "c-bypass"].includes(highlight) &&
              metrics?.bypassed_player_ids.includes(p.player_id)) ||
            focus === p.player_id;
          return (
            <g
              key={p.player_id}
              data-player-id={p.player_id}
              data-role={player?.role}
              className={
                interactive
                  ? `${styles.playerMarker}${previousPlayerIds.has(p.player_id) ? ` ${styles.movingMarker}` : ""}`
                  : undefined
              }
              style={
                previousPlayerIds.has(p.player_id) ? motionStyle : undefined
              }
              role={interactive ? "button" : undefined}
              tabIndex={interactive ? 0 : undefined}
              aria-label={interactive ? playerLabel : undefined}
              aria-pressed={interactive ? selected : undefined}
              onPointerEnter={
                interactive ? () => setHoveredPlayerId(p.player_id) : undefined
              }
              onPointerLeave={
                interactive
                  ? () =>
                      setHoveredPlayerId((current) =>
                        current === p.player_id ? null : current,
                      )
                  : undefined
              }
              onFocus={
                interactive ? () => setHoveredPlayerId(p.player_id) : undefined
              }
              onBlur={
                interactive
                  ? () =>
                      setHoveredPlayerId((current) =>
                        current === p.player_id ? null : current,
                      )
                  : undefined
              }
              onClick={interactive ? activate : undefined}
              onKeyDown={interactive ? handleKeyDown : undefined}
            >
              <title>{playerLabel}</title>
              {interactive && (
                <circle
                  className={styles.focusRing}
                  cx={q.x}
                  cy={q.y}
                  r="2.65"
                />
              )}
              {broadcast && (
                <circle
                  cx={q.x}
                  cy={q.y + 0.4}
                  r="1.65"
                  fill="#001a17"
                  opacity=".4"
                />
              )}
              {broadcast && frame.controlling_player_id === p.player_id && (
                <circle
                  cx={q.x}
                  cy={q.y}
                  data-testid="controlled-player-indicator"
                  r={keeper ? "2.25" : "1.9"}
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth=".28"
                  opacity=".85"
                />
              )}
              {highlighted && (
                <circle
                  cx={q.x}
                  cy={q.y}
                  r="2.1"
                  fill="none"
                  stroke={p.team_id === "blue" ? "white" : "#fde68a"}
                  strokeWidth=".35"
                />
              )}
              {keeper ? (
                <rect
                  x={q.x - 1.65}
                  y={q.y - 1.65}
                  width="3.3"
                  height="3.3"
                  rx=".45"
                  fill={keeperColor}
                  stroke="#192333"
                  strokeWidth=".25"
                />
              ) : (
                <circle
                  cx={q.x}
                  cy={q.y}
                  r={broadcast ? "1.45" : "1.15"}
                  fill={
                    broadcast
                      ? `url(#${uid}-${p.team_id === "blue" ? "blue" : "amber"})`
                      : p.team_id === "blue"
                        ? "#60a5fa"
                        : "#fbbf24"
                  }
                  stroke={broadcast ? "#112f2c" : "#0c3028"}
                  strokeWidth=".22"
                />
              )}
              <text
                x={q.x}
                y={q.y + 0.42}
                textAnchor="middle"
                fill={p.team_id === "blue" ? "#102b46" : "#392b06"}
                fontSize={broadcast ? "1.45" : "1.25"}
                fontWeight="700"
              >
                {shirtNumber}
              </text>
            </g>
          );
        })}
        {carrier && broadcastBall}
        {ball && !broadcast && (
          <>
            <circle
              cx={ball.x_m + 5}
              cy={ball.y_m + 5}
              r="1"
              fill="#0b221b"
              opacity=".4"
            />
            <circle
              cx={ball.x_m + 5}
              cy={ball.y_m + 4.8}
              r=".65"
              fill="white"
              stroke="#14332a"
              strokeWidth=".15"
            />
          </>
        )}
        {!frame && (
          <text x="57.5" y="39" fill="#c6d4c7" fontSize="3" textAnchor="middle">
            {es
              ? "Preparando la repetición sintética…"
              : "Preparing synthetic replay…"}
          </text>
        )}
      </svg>
      {broadcast && (
        <p className={styles.playerIdentity}>
          {identityText ??
            (es
              ? "Selecciona un jugador para ver su nombre, dorsal y posición."
              : "Select a player to see their name, number and role.")}
        </p>
      )}
    </>
  );
}
