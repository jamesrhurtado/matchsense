import { ArrowLeft, Clock3, ScanLine } from "lucide-react";
import { cn, Evidence, Story, Variant, timecode } from "@/lib/api";
import { Button, Card, Tag } from "./ui";
import { InlineEvidence } from "./inline-evidence";

/** Focus uses verified roles only. Legacy packages cannot establish missing roles. */
export function relevantStories(stories: Story[], focus: string) {
  return !focus
    ? stories
    : stories.filter(
        (story) =>
          story.team_id === focus ||
          story.passer_id === focus ||
          story.receiver_id === focus,
      );
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
  return (
    <div
      className={cn(
        "space-y-2",
        producer ? "border-b border-stone-100 p-3" : "mt-3",
      )}
      role="group"
      aria-label={
        producer
          ? "Story queue moments"
          : es
            ? "Momentos aprobados"
            : "Approved moments"
      }
    >
      {stories.map((item, index) => (
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
              {es ? "Momento" : "Moment"} {index + 1} ·{" "}
              {timecode(item.eligible_from_ms)}
            </span>
            <span className="block text-xs">
              {item.titles?.[language] || item.title}
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
                    ready: "Listo",
                  }[item.status] || item.status
                : item.status}
          </span>
        </button>
      ))}
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
  workflowPending,
  overlayId,
  onSelect,
  onEvidence,
  onRecap,
  onWholePlay,
  controls,
}: {
  story: Story | null | undefined;
  stories: Story[];
  variant: Variant | null;
  evidence?: Evidence | null;
  language: string;
  detail: string;
  focus: string;
  workflowPending: boolean;
  overlayId?: string | null;
  onSelect: (id: string) => void;
  onEvidence: () => void;
  onRecap: () => void;
  onWholePlay: () => void;
  controls: React.ReactNode;
}) {
  const es = language === "es";
  return (
    <Card className="p-4 md:p-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="mb-1 text-xs font-semibold text-emerald-800">
            {es ? "LA EXPLICACIÓN" : "THE EXPLANATION"}
          </p>
          <h2 className="text-balance text-xl font-semibold">
            {story
              ? story.titles?.[language] || story.title
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
              ? "No hay participación aprobada en este intervalo."
              : "No approved involvement in this interval."}
          </p>
          <p className="mt-2 text-pretty text-xs leading-relaxed text-stone-600">
            {es
              ? "Solo se muestra participación verificada como pasador, receptor o equipo en posesión."
              : "Only verified passer, receiver, or possession-team involvement appears here. Older stories may lack that information."}
          </p>
          <Button className="mt-3" onClick={onWholePlay}>
            <ArrowLeft size={14} />
            {es ? "Jugada completa" : "Whole play"}
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
              ? "Las explicaciones aparecerán después de la aprobación del productor."
              : "Explanations appear once the producer approves a supported story.")}
        </p>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={!story} onClick={onEvidence}>
          <ScanLine size={15} />
          {es ? "Ver evidencia" : "Show why"}
        </Button>
        <Button onClick={onRecap}>
          <Clock3 size={15} />
          {es ? "Ponerme al día" : "Catch me up"}
        </Button>
      </div>
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
                : "Relevant approved history"
              : es
                ? "Historial aprobado"
                : "Approved history"}{" "}
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
