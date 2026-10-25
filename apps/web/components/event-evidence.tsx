import { Evidence, timecode } from "@/lib/api";

/** Family-specific facts; coordinates never stand in for missing tracking. */
export function EventEvidence({
  data,
  language = "en",
  compact = false,
}: {
  data: Evidence;
  language?: string;
  compact?: boolean;
}) {
  const teams: Record<string, string> = {
    blue: "Harbor City",
    amber: "Alder Rovers",
  };
  const m = data.story.metrics;
  const f = m.facts!;
  const es = language === "es";
  const text = data.story.variants.find(
    (v) => v.language === language && v.detail === "detail" && !v.focus,
  )?.text;
  const location = f.location;
  const name = (id: string | null) =>
    id
      ? data.story.entities?.players.find((p) => p.id === id)?.name ||
        teams[id] ||
        id
      : es
        ? "sin identificar"
        : "unknown";
  const roleNames: Record<string, string> = {
    recovering_player: es ? "Jugador que recupera" : "Recovering player",
    passer: es ? "Pasador" : "Passer",
    receiver: es ? "Receptor" : "Receiver",
  };
  const labels: Record<string, string[]> = {
    pressure: ["Nearby pressure change", "Cambio de presión cercana"],
    recovery: ["Change of control", "Cambio de control"],
    shot: ["Shot outcome", "Resultado del remate"],
    goal: ["Confirmed goal", "Gol confirmado"],
    possession: ["Possession interval", "Intervalo de posesión"],
  };
  if (compact && m.family === "pressure" && f.before && f.after)
    return (
      <section
        aria-label={es ? "Resumen de la medición" : "Measurement summary"}
        className="mt-4 rounded-xl border border-stone-200 p-3"
      >
        <div className="flex flex-wrap items-center justify-between gap-3 tabular-nums">
          <div>
            <p className="text-xs text-stone-600">
              {es ? "Rivales cercanos · media" : "Nearby opponents · average"}
            </p>
            <p className="mt-1 text-xl font-semibold text-emerald-900">
              {f.before.mean.toFixed(1)} → {f.after.mean.toFixed(1)}
            </p>
          </div>
          <div>
            <p className="text-xs text-stone-600">
              {es ? "Hacia delante" : "Forward pass"}
            </p>
            <p className="mt-1 text-xl font-semibold">
              {f.forward_m?.toFixed(1)} m
            </p>
          </div>
        </div>
        <p className="mt-2 text-xs text-stone-600">
          {es
            ? "Radio 6 m · 2 s antes / después · cobertura"
            : "6 m radius · 2 s before / after · coverage"}{" "}
          {(Math.min(f.before.coverage, f.after.coverage) * 100).toFixed(1)}%
        </p>
      </section>
    );
  return (
    <section
      className="mt-4 space-y-3 rounded-xl border border-stone-200 bg-white p-4 text-sm"
      data-testid="event-evidence"
    >
      <h3 className="font-semibold">
        {es ? "Evidencia del evento" : "Event evidence"} ·{" "}
        {labels[m.family || ""]?.[es ? 1 : 0] || m.family}
      </h3>
      <p lang={language} className="leading-relaxed">
        {text}
      </p>
      <p className="text-xs tabular-nums text-stone-600">
        {es ? "Intervalo observado" : "Observed interval"}:{" "}
        {timecode(m.window_start_ms || 0)}–{timecode(m.window_end_ms || 0)} ·{" "}
        {es ? "Disponible" : "Available"} {timecode(data.cutoff_ms)}
      </p>
      {m.family === "pressure" && f.before && f.after && (
        <div className="space-y-4" data-testid="pressure-evidence">
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              [
                es ? "ANTES DEL PASE" : "BEFORE THE PASS",
                f.before.mean.toFixed(1),
                `${timecode(f.before.start_ms)}–${timecode(f.before.end_ms)}`,
              ],
              [
                es ? "DISTANCIA HACIA DELANTE" : "FORWARD DISTANCE",
                `${f.forward_m?.toFixed(1)} m`,
                es ? "Posesión posterior: 3 s" : "Subsequent possession: 3 s",
              ],
              [
                es ? "TRAS LA RECEPCIÓN" : "AFTER RECEPTION",
                f.after.mean.toFixed(1),
                `${timecode(f.after.start_ms)}–${timecode(f.after.end_ms)}`,
              ],
            ].map(([label, value, interval]) => (
              <div
                key={label}
                className="rounded-xl border border-emerald-200 bg-emerald-50 p-4"
              >
                <p className="text-xs font-semibold text-emerald-900">
                  {label}
                </p>
                <p className="mt-2 text-3xl font-semibold tabular-nums text-emerald-950">
                  {value}
                </p>
                <p className="mt-2 text-xs tabular-nums text-emerald-900">
                  {interval}
                </p>
              </div>
            ))}
          </div>
          <p className="text-pretty text-xs leading-relaxed text-stone-600">
            {es
              ? "Rivales a 6 m: medias ponderadas por tiempo, alrededor del pasador antes y del receptor después. No es una probabilidad ni una medida de intención táctica."
              : "Opponents within 6 m: time-weighted averages around the passer before and the receiver after. This is a proximity measure, not a probability or a measure of tactical intent."}
          </p>
          <p className="text-xs leading-relaxed tabular-nums">
            {es
              ? `Datos observados: antes ${(f.before.coverage * 100).toFixed(0)}% (${(f.before.known_ms / 1000).toFixed(1)} de 2.0 s); después ${(f.after.coverage * 100).toFixed(0)}% (${(f.after.known_ms / 1000).toFixed(1)} de 2.0 s).`
              : `Observed data coverage: before ${(f.before.coverage * 100).toFixed(0)}% (${(f.before.known_ms / 1000).toFixed(1)} of 2.0 s); after ${(f.after.coverage * 100).toFixed(0)}% (${(f.after.known_ms / 1000).toFixed(1)} of 2.0 s).`}
          </p>
          {f.stands_out && (
            <table className="w-full text-left text-xs tabular-nums">
              <caption className="mb-2 text-left font-medium">
                {es
                  ? "Los tres pases anteriores del equipo · últimos 120 s de esta repetición"
                  : "Previous three team passes · prior 120 s of this replay"}
              </caption>
              <thead>
                <tr>
                  <th scope="col">{es ? "Recepción" : "Reception"}</th>
                  <th scope="col">{es ? "Avance" : "Forward distance"}</th>
                </tr>
              </thead>
              <tbody>
                {f.comparators?.map((c) => (
                  <tr key={c.pass_id}>
                    <td className="py-2">{timecode(c.resolution_ms)}</td>
                    <td>{c.forward_m.toFixed(1)} m</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <details>
            <summary className="min-h-11 cursor-pointer py-3 font-medium">
              {es ? "Comparar perspectivas" : "Compare audience views"}
            </summary>
            <div className="grid gap-3 sm:grid-cols-2">
              {["simple", "detail"].map((detail) => (
                <article key={detail} className="rounded-lg bg-stone-50 p-3">
                  <h4 className="font-semibold">
                    {detail === "simple"
                      ? es
                        ? "Para seguir el partido"
                        : "For the casual viewer"
                      : es
                        ? "Para el analista"
                        : "For the analyst"}
                  </h4>
                  <p className="mt-2 text-pretty leading-relaxed">
                    {
                      data.story.variants.find(
                        (v) =>
                          v.language === language &&
                          v.detail === detail &&
                          !v.focus,
                      )?.text
                    }
                  </p>
                </article>
              ))}
            </div>
            <p className="mt-3 text-xs text-stone-600">
              {es
                ? "El selector de enfoque muestra el papel verificado del pasador o receptor usando los mismos hechos aprobados."
                : "The focus selector shows the verified passer or receiver role using these same approved facts."}
            </p>
          </details>
        </div>
      )}
      {m.family === "shot" &&
        (location ? (
          <div>
            <svg
              viewBox="0 0 105 68"
              role="img"
              aria-label={
                es ? "Ubicación observada del remate" : "Observed shot location"
              }
              className="mx-auto w-full max-w-xs rounded-lg bg-emerald-950"
            >
              <rect
                x="1"
                y="1"
                width="103"
                height="66"
                fill="none"
                stroke="#d1fae5"
                strokeWidth="0.5"
              />
              <line
                x1="52.5"
                y1="1"
                x2="52.5"
                y2="67"
                stroke="#d1fae5"
                strokeWidth="0.5"
              />
              <circle
                cx={location.x_m}
                cy={location.y_m}
                r="2"
                fill="#fbbf24"
              />
            </svg>
            <p className="mt-2 text-xs tabular-nums">
              x {location.x_m} m · y {location.y_m} m ·{" "}
              {es
                ? "Solo ubicación; sin trayectoria inferida"
                : "Location only; no inferred trajectory"}
            </p>
          </div>
        ) : (
          <p>{es ? "Ubicación no disponible." : "Location unavailable."}</p>
        ))}
      {m.family === "possession" && (
        <div className="overflow-x-auto">
          <table className="w-full text-left tabular-nums">
            <caption className="mb-2 text-left">
              {es
                ? "Tiempo integrado en segundos"
                : "Integrated time in seconds"}
            </caption>
            <thead>
              <tr>
                <th scope="col">{es ? "Equipo" : "Team"}</th>
                <th scope="col">s</th>
                <th scope="col">%</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(f.team_ms || {}).map(([team, ms]) => (
                <tr key={team}>
                  <th scope="row" className="py-2 font-normal">
                    {teams[team] || team}
                  </th>
                  <td>{ms / 1000}</td>
                  <td>
                    {f.percentages ? f.percentages[team].toFixed(1) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs">
            {es ? "Base asignada" : "Assigned denominator"}:{" "}
            {(f.assigned_ms || 0) / 1000} s · {es ? "Cobertura" : "Coverage"}:{" "}
            {((f.coverage || 0) * 100).toFixed(1)}%
          </p>
          <p className="mt-2 text-xs">
            {es
              ? "Fuera de juego / suelto / desconocido"
              : "Dead / loose / unknown"}
            : {(f.dead_ms || 0) / 1000} / {(f.loose_ms || 0) / 1000} /{" "}
            {(f.unknown_ms || 0) / 1000} s
          </p>
        </div>
      )}
      {m.family === "goal" && (
        <p>
          {es
            ? "Cambio de marcador observado en la confirmación"
            : "Observed score transition at confirmation"}
          :{" "}
          {Object.entries(f.score_before || {})
            .map(([team, score]) => `${teams[team] || team} ${score}`)
            .join(" · ")}{" "}
          →{" "}
          {Object.entries(f.score || {})
            .map(([team, score]) => `${teams[team] || team} ${score}`)
            .join(" · ")}
          .{" "}
          {es
            ? "El marcador actual se muestra por separado."
            : "Current score is shown separately."}
        </p>
      )}
      {m.family === "recovery" && (
        <p>
          {(f.previous_team_id && name(f.previous_team_id)) ||
            (es
              ? "Sin equipo anterior confirmado"
              : "No confirmed previous team")}{" "}
          → {name(f.new_team_id || null)} · {es ? "Atribución" : "Attribution"}:{" "}
          {Object.entries(m.participants || {})
            .map(
              ([role, actor]) => `${roleNames[role] || role}: ${name(actor)}`,
            )
            .join(", ")}
        </p>
      )}
      {!!data.related_stories?.length && (
        <details>
          <summary className="min-h-11 cursor-pointer py-3 font-medium">
            {es
              ? "Eventos vinculados del incidente"
              : "Linked incident stories"}
          </summary>
          {data.related_stories.map((related) => (
            <article
              key={related.id}
              className="mt-3 rounded-lg bg-stone-50 p-3"
            >
              <p className="text-xs break-all">
                {related.family} · {related.id} · r{related.revision}
              </p>
              <p className="mt-2">{related.texts[language]}</p>
              <p className="mt-2 text-xs break-all">
                {es ? "Fuentes" : "Sources"}:{" "}
                {related.source_message_ids.join(", ")}
              </p>
            </article>
          ))}
        </details>
      )}
      <details>
        <summary className="min-h-11 cursor-pointer py-3 font-medium">
          {es ? "Detalles técnicos de la fuente" : "Technical source details"} ·{" "}
          {es ? "Observaciones fuente" : "Source observations"} ·{" "}
          {m.source_message_ids.length}
        </summary>
        <p className="mb-3 text-xs leading-relaxed text-stone-600">
          {es
            ? "Registro técnico para comprobar qué versión de las observaciones respalda esta explicación. Si cambia la fuente, se necesita una nueva aprobación. Los códigos identifican registros; no son puntuaciones."
            : "Technical audit of the exact observations behind this explanation. A source correction requires a new approval. These codes identify records; they are not scores."}
        </p>
        <p className="mb-2 text-xs break-all">
          {es ? "Revisión" : "Evidence revision"}:{" "}
          {data.story.evidence_revision}
        </p>
        <ul className="max-h-52 space-y-2 overflow-auto text-xs">
          {(
            data.sources ||
            m.source_message_ids.map((message_id) => ({
              message_id,
              timeline_ms: undefined,
              revision: undefined,
              hash: undefined,
              kind: undefined,
            }))
          ).map((source) => (
            <li
              key={source.message_id}
              className="break-all rounded bg-stone-50 p-2"
            >
              <span className="mb-1 block font-medium">
                {source.kind === "tracking_frame"
                  ? es
                    ? "Posiciones observadas"
                    : "Observed positions"
                  : es
                    ? "Observación del evento"
                    : "Event observation"}
              </span>
              {source.message_id}
              {"timeline_ms" in source
                ? ` · ${timecode(source.timeline_ms!)} · r${source.revision}`
                : ""}
              {"hash" in source && <span className="block">{source.hash}</span>}
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
