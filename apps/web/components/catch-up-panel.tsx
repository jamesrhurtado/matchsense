import { useEffect, useRef, useState } from "react";
import { api, Recap, Story, timecode } from "@/lib/api";
import { Button, Card } from "./ui";
import { ListenButton } from "./listen-button";

export function CatchUpPanel({
  path,
  language,
  focus,
  context,
  clock,
  visit,
  teamNames,
  stories,
  onSelect,
  onClose,
}: {
  path: string;
  language: string;
  focus: string;
  context: string;
  clock: number;
  visit: { from: number; returning: boolean } | null;
  teamNames: Record<string, string>;
  stories: Story[];
  onSelect: (id: string) => void;
  onClose: () => void;
}) {
  const es = language === "es";
  const [interval, setInterval] = useState("all");
  const [refresh, setRefresh] = useState(0);
  const key = `${path}:${language}:${focus}:${context}:${interval}:${refresh}:${visit?.from}`;
  const latestClock = useRef(clock);
  latestClock.current = clock;
  const [result, setResult] = useState<{
    key: string;
    data?: Recap;
    error?: string;
  } | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    const now = latestClock.current;
    const from =
      interval === "minute"
        ? Math.max(0, now - 60000)
        : interval === "visit"
          ? Math.min(now, visit?.from ?? now)
          : 0;
    api<Recap>(`${path}/recaps`, {
      method: "POST",
      signal: controller.signal,
      body: JSON.stringify({ language, focus: focus || null, from_ms: from }),
    })
      .then((data) => {
        if (!controller.signal.aborted) setResult({ key, data });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setResult({ key, error: error.message });
      });
    return () => controller.abort();
  }, [key, path, language, focus, interval, visit?.from]);
  // Never keep an old claim visible while a changed source is being rechecked.
  const data = result?.key === key ? result.data : undefined;
  const error = result?.key === key ? result.error : undefined;
  const approved = new Set(
    stories
      .flatMap((s) => [s, ...(s.related_stories || [])])
      .filter((s) => s.approved || s.status === "approved")
      .map((s) => `${s.id}:${s.revision}`),
  );
  const moments =
    data?.moments.filter((m) => approved.has(`${m.story_id}:${m.revision}`)) ||
    [];
  const spokenSummary = data
    ? [
        data.title,
        es
          ? `Intervalo del resumen: ${timecode(data.from_ms ?? 0)} a ${timecode(data.through_ms)}.`
          : `Summary interval: ${timecode(data.from_ms ?? 0)} to ${timecode(data.through_ms)}.`,
        data.match_state
          ? es
            ? `Marcador confirmado actual: ${teamNames.blue || "equipo azul"}, ${data.match_state.score.blue}; ${teamNames.amber || "equipo ámbar"}, ${data.match_state.score.amber}.`
            : `Current confirmed score: ${teamNames.blue || "Blue team"}, ${data.match_state.score.blue}; ${teamNames.amber || "Amber team"}, ${data.match_state.score.amber}.`
          : "",
        moments.length
          ? es
            ? `${moments.length} explicaciones aprobadas.`
            : `${moments.length} approved explanations.`
          : es
            ? "No hay explicaciones aprobadas en este intervalo para este enfoque."
            : "There are no approved explanations for this focus in this interval.",
        ...moments.map(
          (moment) =>
            `${timecode(moment.at_ms)}. ${moment.title}. ${moment.text}`,
        ),
        ...(data.corrections || []).map((notice) =>
          es
            ? `${timecode(notice.at_ms)}. Actualización sobre el momento de ${timecode(notice.story_at_ms)}: ${notice.kind === "source_changed" ? "cambió la fuente y se retiró la explicación" : "el productor retiró la explicación"}.`
            : `${timecode(notice.at_ms)}. Update to the moment at ${timecode(notice.story_at_ms)}: ${notice.kind === "source_changed" ? "the source changed and the explanation was withdrawn" : "the producer withdrew the explanation"}.`,
        ),
        (data.correction_count || 0) > (data.corrections?.length || 0)
          ? es
            ? "Hay más actualizaciones de las que se muestran aquí."
            : "There are more updates than the ones shown here."
          : "",
        es
          ? "Este resumen incluye explicaciones aprobadas; no es una lista de todos los eventos."
          : "This recap includes approved explanations; it is not a list of every event.",
      ]
        .filter(Boolean)
        .join(" ")
    : "";
  return (
    <Card className="mt-5 p-4 md:p-6" data-testid="catch-up-panel">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-xl font-semibold">
          {data?.title || (es ? "Resumen del segmento" : "Segment catch-up")}
        </h2>
        <Button
          aria-label={es ? "Cerrar resumen" : "Close recap"}
          onClick={onClose}
        >
          ×
        </Button>
      </div>
      <label className="mt-4 block text-sm font-medium">
        {es ? "Intervalo del resumen" : "Catch-up interval"}
        <select
          className="mt-2 min-h-11 w-full rounded-lg border border-stone-200 bg-white px-3"
          value={interval}
          onChange={(e) => setInterval(e.target.value)}
        >
          <option value="all">
            {es ? "Todo el segmento" : "Whole segment"}
          </option>
          <option value="minute">{es ? "Último minuto" : "Last minute"}</option>
          {visit && (
            <option value="visit">
              {visit.returning
                ? es
                  ? "Desde mi última visita"
                  : "Since my last visit"
                : es
                  ? "Desde que entré"
                  : "Since I joined"}
            </option>
          )}
        </select>
      </label>
      {error && (
        <p role="alert" className="mt-4 text-sm text-red-800">
          {error}
        </p>
      )}
      {!data && !error && (
        <p className="mt-4 text-sm text-stone-600">
          {es
            ? "Comprobando las explicaciones aprobadas…"
            : "Checking approved explanations…"}
        </p>
      )}
      {data && (
        <>
          <p className="mt-4 text-sm tabular-nums">
            {timecode(data.from_ms ?? 0)}–{timecode(data.through_ms)}
          </p>
          <div className="mt-3">
            <ListenButton
              key={`${key}:audio`}
              heading={es ? "Escuchar resumen" : "Listen to the recap"}
              text={spokenSummary}
              language={language}
            />
          </div>
          <p className="mt-1 text-xs leading-relaxed text-stone-600">
            {es
              ? "Hechos ocurridos en este intervalo; validez y marcador comprobados ahora. Los intervalos de posesión se incluyen por su hora de cierre."
              : "Events in this interval; validity and score checked now. Possession windows are included by their end time."}
          </p>
          {data.match_state && (
            <p className="mt-3 text-sm font-medium">
              {es
                ? "Marcador confirmado actual"
                : "Current source-confirmed score"}
              : {data.match_state.score.blue} : {data.match_state.score.amber}
            </p>
          )}
          {!!data.corrections?.length && (
            <section
              aria-label={
                es
                  ? "Actualizaciones y correcciones"
                  : "Updates and corrections"
              }
              className="mt-4 border-l-2 border-amber-500 pl-3"
            >
              <h3 className="text-sm font-semibold">
                {es
                  ? "Actualizaciones y correcciones"
                  : "Updates and corrections"}
              </h3>
              {data.corrections.map((notice) => (
                <p
                  key={notice.notice_id}
                  className="mt-2 text-sm leading-relaxed"
                >
                  {timecode(notice.at_ms)} · {notice.text}{" "}
                  {es ? "Evento" : "Event"}: {timecode(notice.story_at_ms)}.
                </p>
              ))}
              {(data.correction_count ?? 0) > data.corrections.length && (
                <p className="mt-2 text-xs">
                  {es
                    ? "Se muestran las cinco actualizaciones más recientes."
                    : "Showing the five latest updates."}
                </p>
              )}
            </section>
          )}
          {moments.map((m) => (
            <article
              key={`${m.story_id}:${m.revision}`}
              lang={language}
              className="mt-5 border-t border-stone-100 pt-4"
            >
              <p className="text-xs tabular-nums text-stone-500">
                {timecode(m.at_ms)} · {es ? "Aprobado" : "Approved"}
              </p>
              <h3 className="mt-1 font-semibold">{m.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-stone-600">
                {m.text}
              </p>
              <Button className="mt-3" onClick={() => onSelect(m.story_id)}>
                {es ? "Abrir momento" : "Open moment"}
              </Button>
              {m.similar_moments.length > 1 && (
                <details className="mt-2 text-sm">
                  <summary className="min-h-11 cursor-pointer py-3">
                    {m.similar_moments.length}{" "}
                    {es
                      ? "momentos aprobados similares"
                      : "similar approved moments"}
                  </summary>
                  <p className="text-xs text-stone-600">
                    {es
                      ? "La similitud no demuestra una tendencia."
                      : "Similarity does not establish a trend."}
                  </p>
                  {m.similar_moments
                    .filter((member) =>
                      approved.has(`${member.story_id}:${member.revision}`),
                    )
                    .map((member) => (
                      <Button
                        key={member.story_id}
                        className="mr-2 mt-2"
                        onClick={() => onSelect(member.story_id)}
                      >
                        {timecode(member.at_ms)}
                      </Button>
                    ))}
                </details>
              )}
            </article>
          ))}
          {!moments.length && (
            <p className="mt-4 text-sm text-stone-600">
              {es
                ? "No hay explicaciones aprobadas en este intervalo para este enfoque."
                : "No approved explanations in this interval for this focus."}
            </p>
          )}
          {data.truncated && (
            <p className="mt-4 text-xs text-stone-600">
              {es
                ? "Resumen limitado; historial completo"
                : "Recap shortened; complete approved timeline"}
              : {data.timeline_count}
            </p>
          )}
          <p className="mt-4 text-xs text-stone-600">
            {es
              ? "Solo explicaciones aprobadas; esto no es una lista de todos los eventos."
              : "Approved explanations only; this is not a list of every match event."}
          </p>
        </>
      )}
      <Button className="mt-4" onClick={() => setRefresh((n) => n + 1)}>
        {es ? "Actualizar resumen" : "Refresh recap"}
      </Button>
    </Card>
  );
}
