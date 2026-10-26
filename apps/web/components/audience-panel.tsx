import { useState } from "react";
import { ArrowLeft, Clock3, ScanLine } from "lucide-react";
import {
  cn,
  Evidence,
  Metrics,
  Player,
  Story,
  Variant,
  timecode,
} from "@/lib/api";
import { Button, Card, Tag } from "./ui";
import { InlineEvidence } from "./inline-evidence";
import { ListenButton } from "./listen-button";
import { StoryPlayers } from "./story-players";

/** Focus uses verified roles only. Legacy packages cannot establish missing roles. */
export function relevantStories(stories: Story[], focus: string) {
  return !focus
    ? stories
    : stories
        .flatMap((story) => [story, ...(story.related_stories || [])])
        .filter(
          (story) =>
            story.team_id === focus ||
            story.passer_id === focus ||
            story.receiver_id === focus ||
            Object.values(story.participants || {}).includes(focus) ||
            (story.family === "possession" &&
              ["blue", "amber"].includes(focus)),
        )
        .filter(
          (story, index, rows) =>
            rows.findIndex(
              (other) =>
                (other.incident_id || other.id) ===
                (story.incident_id || story.id),
            ) === index,
        );
}

function describePassLocation(
  metrics: Metrics,
  teamName: string,
  language: string,
) {
  const start = metrics.pass_start;
  const end = metrics.pass_end;
  const forward = metrics.forward_pass_m ?? metrics.facts?.forward_m;
  if (!start || !end || forward == null) return "";
  const deltaX = end.x_m - start.x_m;
  if (Math.abs(deltaX) < 0.1 || Math.abs(forward) < 0.1) return "";

  // Signed progression identifies which end this team attacks for this pass.
  const attacksRight = Math.sign(deltaX) === Math.sign(forward);
  const attackingX = (x: number) => (attacksRight ? x : 105 - x);
  const attackingY = (y: number) => (attacksRight ? y : 68 - y);
  const third = (x: number) => {
    const progress = attackingX(x);
    if (progress < 35) return language === "es" ? "defensivo" : "defensive";
    if (progress < 70) return language === "es" ? "medio" : "middle";
    return language === "es" ? "ofensivo" : "attacking";
  };
  const channel = (y: number) => {
    const across = attackingY(y);
    if (across < 68 / 3)
      return language === "es" ? "carril izquierdo" : "left channel";
    if (across >= (2 * 68) / 3)
      return language === "es" ? "carril derecho" : "right channel";
    return language === "es" ? "carril central" : "central channel";
  };
  const origin = `${channel(start.y_m)} del tercio ${third(start.x_m)}`;
  const destination = `${channel(end.y_m)} del tercio ${third(end.x_m)}`;
  return language === "es"
    ? `Ubicación observada: para ${teamName}, el pase comenzó por el ${origin} y terminó por el ${destination}. La fuente registra el inicio y la recepción, no la trayectoria intermedia del balón.`
    : `Observed locations: for ${teamName}, the pass began in the ${origin} and ended in the ${destination}. The source records the start and reception, not the ball's intermediate path.`;
}

export function StoryPicker({
  stories,
  selected,
  onSelect,
  producer = false,
  language = "en",
}: {
  stories: Story[];
  selected: string;
  onSelect: (id: string) => void;
  producer?: boolean;
  language?: string;
}) {
  const es = language === "es";
  const [family, setFamily] = useState("");
  const [showArchive, setShowArchive] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const mixed = stories.some((s) => s.family && s.family !== "pass");
  const priority: Record<string, number> = {
    goal: 0,
    shot: 1,
    pressure: 2,
    recovery: 3,
    possession: 4,
    pass: 5,
  };
  const ranked =
    producer && mixed
      ? [...stories].sort(
          (a, b) =>
            (priority[a.family || "pass"] ?? 6) -
              (priority[b.family || "pass"] ?? 6) ||
            (b.occurrence_ms ?? b.eligible_from_ms) -
              (a.occurrence_ms ?? a.eligible_from_ms),
        )
      : stories;
  const groups = new Map<string, Story[]>();
  for (const item of ranked) {
    const key = producer && mixed ? item.incident_id || item.id : item.id;
    groups.set(key, [...(groups.get(key) || []), item]);
  }
  const visible = [...groups.values()]
    .flat()
    .filter(
      (s) =>
        !producer ||
        !mixed ||
        showArchive ||
        (s.queue_state === "live" &&
          !["suppressed", "retracted", "superseded"].includes(s.status)),
    );
  return (
    <div
      className={cn(
        "space-y-2",
        producer ? "border-b border-stone-100 p-3" : "mt-3",
      )}
      role="group"
      aria-label={
        producer
          ? "Suggested insights"
          : es
            ? "Información del partido aprobada"
            : "Approved match insights"
      }
    >
      {mixed && (
        <label className="block text-sm">
          {es ? "Categoría" : "Event family"}
          <select
            aria-label={es ? "Categoría" : "Event family"}
            value={family}
            onChange={(e) => setFamily(e.target.value)}
            className="my-2 min-h-11 w-full rounded border border-stone-200 bg-white px-3"
          >
            <option value="">{es ? "Todos" : "All events"}</option>
            {[
              ["goal", "Goals", "Goles"],
              ["shot", "Shots", "Remates"],
              [
                "pressure",
                "Nearby pressure change",
                "Cambio de presión cercana",
              ],
              ["recovery", "Control changes", "Cambios de control"],
              ["possession", "Possession", "Posesión"],
              ["pass", "Passes", "Pases"],
            ].map(([id, en, esLabel]) => (
              <option value={id} key={id}>
                {es ? esLabel : en}
              </option>
            ))}
          </select>
        </label>
      )}
      {producer && mixed && (
        <label className="flex min-h-11 items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={showArchive}
            onChange={(e) => setShowArchive(e.target.checked)}
          />
          {es ? "Incluir candidatos archivados" : "Include archived candidates"}
        </label>
      )}
      {visible
        .filter(
          (s) => !producer || !mixed || showArchive || s.queue_state === "live",
        )
        .flatMap((s) =>
          family && s.family !== family && s.related_stories?.length
            ? s.related_stories.filter((related) => related.family === family)
            : [s],
        )
        .filter((s) => !family || (s.family || "pass") === family)
        .filter(
          (s, index) =>
            !producer ||
            !mixed ||
            showAll ||
            family ||
            showArchive ||
            index < 3 ||
            s.id === selected,
        )
        .map((item, index) => (
          <div key={item.id}>
            {producer &&
              mixed &&
              !family &&
              (groups.get(item.incident_id || item.id)?.length || 0) > 1 &&
              groups.get(item.incident_id || item.id)?.[0].id === item.id && (
                <p className="mb-2 mt-3 text-xs font-medium text-stone-500">
                  {groups.get(item.incident_id || item.id)?.length} explanations
                  · same incident
                </p>
              )}
            <button
              key={item.id}
              type="button"
              aria-pressed={selected === item.id}
              onClick={() => onSelect(item.id)}
              className={cn(
                "flex min-h-11 w-full items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left text-sm",
                selected === item.id
                  ? "border-emerald-300 bg-emerald-50 text-emerald-950"
                  : "border-stone-200 bg-white text-stone-600 hover:bg-stone-50",
              )}
            >
              <span className="min-w-0">
                <span className="block font-medium">
                  {es ? "Información" : "Insight"} {index + 1} ·{" "}
                  {timecode(item.eligible_from_ms)}
                </span>
                <span className="block text-xs">
                  {item.family && (
                    <span className="capitalize">
                      {(
                        {
                          goal: es ? "Gol" : "Goal",
                          shot: es ? "Remate" : "Shot",
                          pressure: es ? "Presión cercana" : "Nearby pressure",
                          recovery: es ? "Control" : "Control",
                          possession: es ? "Posesión" : "Possession",
                          pass: es ? "Pase" : "Pass",
                        } as Record<string, string>
                      )[item.family] || item.family}{" "}
                      ·{" "}
                    </span>
                  )}
                  {item.family === "pressure"
                    ? es
                      ? "Cambio de presión cercana"
                      : "Nearby pressure change"
                    : item.titles?.[language] || item.title}
                </span>
              </span>
              <span className="shrink-0 text-xs capitalize">
                {item.approved && item.status === "expired"
                  ? es
                    ? "Aprobado · archivo"
                    : "Approved · archived"
                  : es
                    ? {
                        approved: "Aprobado",
                        expired: "Archivado",
                        ready: "Listo para revisar",
                      }[item.status] || item.status
                    : item.status === "ready"
                      ? "Ready to review"
                      : item.status}
              </span>
            </button>
          </div>
        ))}
      {producer && mixed && !family && !showArchive && visible.length > 3 && (
        <button
          type="button"
          onClick={() => setShowAll((value) => !value)}
          className="min-h-11 w-full rounded-lg px-3 text-left text-sm font-medium text-emerald-800"
        >
          {showAll
            ? "Show fewer suggestions"
            : `Show all ${visible.length} suggestions`}
        </button>
      )}
    </div>
  );
}
export function AudiencePanel({
  story,
  stories,
  variant,
  evidence,
  language,
  detail,
  focus,
  players,
  teamNames,
  workflowPending,
  overlayId,
  onSelect,
  onEvidence,
  onRecap,
  onWholePlay,
  viewingEarlier,
  onReturnLive,
  controls,
  flagship = false,
}: {
  story: Story | null | undefined;
  stories: Story[];
  variant: Variant | null;
  evidence?: Evidence | null;
  language: string;
  detail: string;
  focus: string;
  players: Player[];
  teamNames: Record<string, string>;
  workflowPending: boolean;
  overlayId?: string | null;
  onSelect: (id: string) => void;
  onEvidence: () => void;
  onRecap: () => void;
  onWholePlay: () => void;
  viewingEarlier: boolean;
  onReturnLive: () => void;
  controls: React.ReactNode;
  flagship?: boolean;
}) {
  const es = language === "es";
  const matchingEvidence =
    story &&
    evidence?.story.id === story.id &&
    evidence.story.revision === story.revision
      ? evidence
      : null;
  const evidenceVariant =
    matchingEvidence?.story.variants.find(
      (item) =>
        item.language === language &&
        item.detail === "detail" &&
        item.focus === (focus || null),
    ) ??
    matchingEvidence?.story.variants.find(
      (item) =>
        item.language === language && item.detail === "detail" && !item.focus,
    );
  const locationText =
    matchingEvidence?.story.metrics.family === "pass" ||
    matchingEvidence?.story.metrics.family === "pressure"
      ? describePassLocation(
          matchingEvidence.story.metrics,
          teamNames[matchingEvidence.story.metrics.team_id || ""] ||
            matchingEvidence.story.metrics.team_id ||
            "",
          language,
        )
      : "";
  const evidenceText = [evidenceVariant?.text, locationText]
    .filter(Boolean)
    .join(" ");
  return (
    <Card className="p-4 md:p-6">
      {viewingEarlier && (
        <div
          className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3"
          data-testid="earlier-moment"
        >
          <p role="status" className="text-sm font-medium text-amber-950">
            {es
              ? "Estás viendo un momento anterior"
              : "Viewing an earlier moment"}{" "}
            · {timecode(story?.eligible_from_ms || 0)}
          </p>
          <Button onClick={onReturnLive}>
            {es ? "Volver al directo" : "Return to live"}
          </Button>
        </div>
      )}
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="mb-1 text-xs font-semibold text-emerald-800">
            {es ? "LA EXPLICACIÓN" : "THE EXPLANATION"}
          </p>
          <h2 className="text-balance text-xl font-semibold">
            {story
              ? story.family === "pressure"
                ? es
                  ? "Cambio de presión cercana"
                  : "Nearby pressure change"
                : story.titles?.[language] || story.title
              : focus
                ? es
                  ? "Tu enfoque seleccionado"
                  : "Your selected focus"
                : workflowPending
                  ? es
                    ? "Revisión de IA en curso"
                    : "AI review in progress"
                  : es
                    ? "Se está preparando el siguiente momento"
                    : "The next story is taking shape"}
          </h2>
        </div>
        <Tag>
          {story
            ? story.id === overlayId
              ? es
                ? "Aprobado · en pantalla"
                : "Approved · on air"
              : es
                ? "Aprobado · historial"
                : "Approved · history"
            : workflowPending
              ? es
                ? "Revisando evidencia"
                : "Reviewing evidence"
              : es
                ? "Observando el juego"
                : "Watching the play"}
        </Tag>
      </div>
      {focus && !stories.length ? (
        <div className="mt-4">
          <p className="text-pretty text-base leading-relaxed">
            {es
              ? "No hay historias aprobadas que involucren esta selección en este intervalo."
              : "No approved stories involving this selection in this interval."}
          </p>
          <p className="mt-2 text-pretty text-xs leading-relaxed text-stone-600">
            {es
              ? "Este filtro solo cambia las historias mostradas; el partido continúa y pueden haber ocurrido otras acciones."
              : "This filter only changes which approved stories appear. The match continues, and other events may have happened."}
          </p>
          <Button className="mt-3" onClick={onWholePlay}>
            <ArrowLeft size={14} />
            {es ? "Ver todas las historias" : "Show all stories"}
          </Button>
        </div>
      ) : (
        <p
          data-testid="audience-explanation"
          lang={language}
          className={cn(
            "mt-3 text-pretty leading-relaxed",
            detail === "simple" ? "text-base" : "text-sm text-stone-600",
          )}
        >
          {(detail === "detail" && variant?.clauses
            ? variant.clauses
                .slice(0, 2)
                .map((c) => c.text)
                .join(" ")
            : variant?.text) ||
            (es
              ? "La cancha muestra el partido en curso. Aquí aparecen las explicaciones aprobadas; «Ponerme al día» abre el resumen."
              : "The pitch shows the match in progress. Approved explanations appear here; “Catch me up” opens the recap.")}
        </p>
      )}

      {story && variant?.text && (
        <div className="mt-2">
          <ListenButton
            text={variant.text}
            evidenceText={evidenceText}
            heading={es ? "Escuchar este momento" : "Listen to this moment"}
            language={language}
          />
        </div>
      )}

      {story && (
        <StoryPlayers
          story={story}
          players={players}
          teamNames={teamNames}
          language={language}
        />
      )}

      {flagship &&
        story?.why_now &&
        (story.family !== "pressure" ||
          /previous three|tres pases anteriores/i.test(
            story.why_now[language] || "",
          )) && (
          <section
            className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4"
            aria-label={es ? "Por qué este momento" : "Why this moment"}
          >
            <h3 className="text-sm font-semibold text-emerald-950">
              {es ? "¿Por qué este momento?" : "Why this moment?"}
            </h3>
            <p
              lang={language}
              className="mt-2 text-pretty text-sm leading-relaxed text-emerald-950"
            >
              {story.why_now[language]}
            </p>
            <p className="mt-3 text-xs text-emerald-900">
              {es ? "Estado de evidencia" : "Evidence status"}:{" "}
              {story.evidence_state === "complete"
                ? es
                  ? "Observaciones requeridas disponibles"
                  : "Required observations available"
                : story.evidence_state === "awaiting_outcome"
                  ? es
                    ? "Resultado sin confirmar"
                    : "Outcome unconfirmed"
                  : es
                    ? "Observaciones limitadas"
                    : "Limited observations"}
            </p>
          </section>
        )}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={!story} onClick={onEvidence}>
          <ScanLine size={15} />
          {es ? "Ver evidencia" : flagship ? "Check the evidence" : "Show why"}
        </Button>
        <Button onClick={onRecap}>
          <Clock3 size={15} />
          {es ? "Ponerme al día" : "Catch me up"}
        </Button>
      </div>
      <p className="mt-2 text-xs text-stone-500">
        {es
          ? "El resumen reúne historias aprobadas de este segmento."
          : "The recap collects approved stories from this segment."}
      </p>
      {story && evidence && (
        <InlineEvidence
          key={`${story.id}:${story.revision}`}
          evidence={evidence}
          variant={variant}
          language={language}
          focus={focus}
        />
      )}
      <div className="mt-4 border-t border-stone-100 pt-4">{controls}</div>
      {detail === "detail" && (
        <p className="mt-4 text-pretty text-xs leading-relaxed text-stone-600">
          {es
            ? "Las mediciones describen solo esta secuencia. Selecciona una afirmación para ver su evidencia."
            : "Measures describe this sequence only. Select a fact to inspect its evidence."}
        </p>
      )}
      {stories.length > 0 && (
        <details className="mt-4">
          <summary className="min-h-11 cursor-pointer py-3 text-sm font-medium text-stone-600">
            {focus
              ? es
                ? "Historial aprobado relevante"
                : "Relevant approved insights"
              : es
                ? "Historial aprobado"
                : "Approved match insights"}{" "}
            · {stories.length}
          </summary>
          <StoryPicker
            stories={stories}
            selected={story?.id || ""}
            onSelect={onSelect}
            language={language}
          />
        </details>
      )}
    </Card>
  );
}
