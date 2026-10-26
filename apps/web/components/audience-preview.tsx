import { useState } from "react";
import { Player, Story } from "@/lib/api";
import { useStoryVariant } from "@/hooks/use-story-variant";
import { StoryPlayers } from "./story-players";

function Preview({
  path,
  story,
  players,
  teamNames,
  language,
}: {
  path: string;
  story: Story;
  players: Player[];
  teamNames?: Record<string, string>;
  language: string;
}) {
  const simple = useStoryVariant(
    path,
    story,
    story.status,
    language,
    "simple",
    "",
    true,
  );
  const detail = useStoryVariant(
    path,
    story,
    story.status,
    language,
    "detail",
    "",
    true,
  );
  const [mobileView, setMobileView] = useState("simple");
  const es = language === "es";
  return (
    <>
      <p className="mt-3 text-xs text-stone-600">
        {story.approved
          ? es
            ? "Esta es la redacción aprobada que ven los espectadores junto al partido. La vista previa no cambia la aprobación."
            : "This is the approved wording viewers see beside the match. Previewing does not change approval."
          : es
            ? "Al aprobarla, esta redacción aparecerá junto al partido. La vista previa no la comparte."
            : "After approval, viewers see this wording beside the match. Previewing does not share it."}
      </p>
      <label className="mt-3 block text-sm sm:hidden">
        {es ? "Perspectiva de vista previa" : "Preview audience"}
        <select
          className="mt-2 min-h-11 w-full rounded-lg border border-stone-200 px-3"
          value={mobileView}
          onChange={(e) => setMobileView(e.target.value)}
        >
          <option value="simple">
            {es ? "Seguir el partido" : "Casual viewer"}
          </option>
          <option value="detail">{es ? "Analista" : "Analyst"}</option>
        </select>
      </label>
      <div
        className="mt-4 grid gap-4 sm:grid-cols-2"
        data-testid="audience-preview"
      >
        <div className="sm:col-span-2">
          <StoryPlayers
            story={story}
            players={players}
            teamNames={teamNames}
            language={language}
          />
        </div>
        {[
          ["simple", simple],
          ["detail", detail],
        ].map(([kind, variant]) => (
          <section
            key={kind as string}
            className={`${mobileView === kind ? "block" : "hidden"} min-w-0 sm:block`}
          >
            <h4 className="text-sm font-semibold">
              {kind === "simple"
                ? es
                  ? "Para seguir el partido"
                  : "Casual viewer"
                : es
                  ? "Analista"
                  : "Analyst"}
            </h4>
            <p
              lang={language}
              className="mt-2 text-sm leading-relaxed text-stone-600"
            >
              {typeof variant === "object" && variant
                ? variant.text
                : es
                  ? "Cargando esta revisión…"
                  : "Loading this revision…"}
            </p>
          </section>
        ))}
      </div>
    </>
  );
}

/** The child mounts only on demand; changing audience never calls a model. */
export function AudiencePreview({
  path,
  story,
  players,
  teamNames,
  onInspect,
}: {
  path: string;
  story: Story;
  players: Player[];
  teamNames?: Record<string, string>;
  onInspect?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [language, setLanguage] = useState("en");
  return (
    <details
      className="mt-4 border-t border-stone-100 pt-2"
      onToggle={(e) => {
        setOpen(e.currentTarget.open);
        if (e.currentTarget.open) onInspect?.();
      }}
    >
      <summary className="min-h-11 cursor-pointer py-3 text-sm font-medium">
        {language === "es"
          ? story.approved
            ? "Vista de espectadores · texto aprobado"
            : "Vista de espectadores · borrador"
          : story.approved
            ? "Viewer preview · approved wording"
            : "Viewer preview · draft wording"}
      </summary>
      <label className="block text-sm">
        {language === "es" ? "Idioma de vista previa" : "Preview language"}
        <select
          aria-label="Preview language"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="ml-3 min-h-11 rounded-lg border border-stone-200 px-3"
        >
          <option value="en">English</option>
          <option value="es">Español</option>
        </select>
      </label>
      {open && (
        <Preview
          key={`${story.id}:${story.revision}`}
          path={path}
          story={story}
          players={players}
          teamNames={teamNames}
          language={language}
        />
      )}
    </details>
  );
}
