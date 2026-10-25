import { useState } from "react";
import { Story } from "@/lib/api";
import { useStoryVariant } from "@/hooks/use-story-variant";

function Preview({
  path,
  story,
  language,
}: {
  path: string;
  story: Story;
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
        {es
          ? "Mismos hechos y revisión. Esta vista previa no publica nada."
          : "Same facts and revision. Previewing does not publish anything."}
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
  onInspect,
}: {
  path: string;
  story: Story;
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
        Preview for viewers · {story.approved ? "approved" : "draft"}
      </summary>
      <label className="block text-sm">
        Preview language
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
          language={language}
        />
      )}
    </details>
  );
}
