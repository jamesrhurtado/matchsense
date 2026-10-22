import { Frame, Metrics } from "@/lib/api";
export default function Pitch({
  frame,
  metrics,
  focus,
  compact = false,
  trails = [],
  highlight = "all",
  language = "en",
}: {
  frame: Frame | null;
  metrics?: Metrics;
  focus?: string | null;
  compact?: boolean;
  language?: string;
  highlight?: string;
  trails?: { x_m: number; y_m: number }[][];
}) {
  const es = language === "es";
  const position = (x: number, y: number) => ({ x: x + 5, y: y + 5 });
  return (
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
        <marker
          id={compact ? "arrow-small" : "arrow"}
          markerWidth="5"
          markerHeight="5"
          refX="4"
          refY="2.5"
          orient="auto"
        >
          <path d="M0 0 L5 2.5 L0 5" fill="#ffffff" />
        </marker>
      </defs>
      <rect width="115" height="78" fill="#153d32" />
      {Array.from({ length: 7 }, (_, i) => (
        <rect
          key={i}
          x={5 + i * 15}
          y="5"
          width="15"
          height="68"
          fill={i % 2 === 0 ? "#1a483b" : "#1d4e40"}
        />
      ))}
      <g fill="none" stroke="#99b8a3" strokeWidth=".25" opacity=".65">
        <rect x="5" y="5" width="105" height="68" />
        <path d="M57.5 5V73" />
        <circle cx="57.5" cy="39" r="9.15" />
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
            metrics.pass_end.x_m < 35 ? 5 : metrics.pass_end.x_m < 70 ? 40 : 75
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
          {["all", "c-forward", "c-context", "c-release", "c-bypass"].includes(
            highlight,
          ) && (
            <path
              d={`M${metrics.pass_start.x_m + 5} ${metrics.pass_start.y_m + 5} L${metrics.pass_end.x_m + 5} ${metrics.pass_end.y_m + 5}`}
              stroke="white"
              strokeWidth=".6"
              strokeDasharray="1 1"
              markerEnd={`url(#${compact ? "arrow-small" : "arrow"})`}
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
      {frame?.players.map((p) => {
        const q = position(p.x_m, p.y_m);
        const highlighted =
          (["all", "c-bypass"].includes(highlight) &&
            metrics?.bypassed_player_ids.includes(p.player_id)) ||
          focus === p.player_id;
        return (
          <g key={p.player_id}>
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
            <circle
              cx={q.x}
              cy={q.y}
              r="1.15"
              fill={p.team_id === "blue" ? "#60a5fa" : "#fbbf24"}
              stroke="#0c3028"
              strokeWidth=".22"
            />
            <text
              x={q.x}
              y={q.y + 0.42}
              textAnchor="middle"
              fill={p.team_id === "blue" ? "#102b46" : "#392b06"}
              fontSize="1.25"
              fontWeight="700"
            >
              {parseInt(p.player_id.split("-")[1])}
            </text>
          </g>
        );
      })}
      {frame?.ball && (
        <>
          <circle
            cx={frame.ball.x_m + 5}
            cy={frame.ball.y_m + 5}
            r="1"
            fill="#0b221b"
            opacity=".4"
          />
          <circle
            cx={frame.ball.x_m + 5}
            cy={frame.ball.y_m + 4.8}
            r=".65"
            fill="white"
            stroke="#14332a"
            strokeWidth=".15"
          />
        </>
      )}
      {!frame && (
        <text x="57.5" y="39" fill="#c6d4c7" fontSize="3" textAnchor="middle">
          Preparing synthetic replay…
        </text>
      )}
    </svg>
  );
}
