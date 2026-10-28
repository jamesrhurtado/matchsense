import { Globe2 } from "lucide-react";
import { cn } from "@/lib/api";

export function AudienceControls({
  language,
  detail,
  focus,
  players,
  setLanguage,
  setDetail,
  setFocus,
}: {
  language: string;
  detail: string;
  focus: string;
  players: { id: string; name: string; number: number }[];
  setLanguage: (s: string) => void;
  setDetail: (s: string) => void;
  setFocus: (s: string) => void;
}) {
  const es = language === "es";

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end gap-3">
        <fieldset>
          <legend className="mb-1 text-xs font-medium text-stone-500">
            {es ? "Estilo de explicación" : "Explanation style"}
          </legend>
          <div
            role="group"
            aria-label={es ? "Estilo de explicación" : "Explanation style"}
            className="inline-flex rounded-lg border border-stone-200 p-1"
          >
            <button
              aria-pressed={detail === "simple"}
              onClick={() => setDetail("simple")}
              className={cn(
                "min-h-10 rounded-md px-3 text-sm",
                detail === "simple"
                  ? "bg-stone-900 text-white"
                  : "text-stone-500",
              )}
            >
              {es ? "Para fans" : "For fans"}
            </button>
            <button
              aria-pressed={detail === "detail"}
              onClick={() => setDetail("detail")}
              className={cn(
                "min-h-10 rounded-md px-3 text-sm",
                detail === "detail"
                  ? "bg-stone-900 text-white"
                  : "text-stone-500",
              )}
            >
              {es ? "Para analistas" : "For analysts"}
            </button>
          </div>
        </fieldset>

        <div className="flex min-h-12 items-center gap-2 rounded-lg border border-stone-200 px-3">
          <Globe2 size={15} className="text-stone-400" />
          <label htmlFor="language" className="sr-only">
            {es ? "Idioma" : "Language"}
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="max-w-28 bg-white text-sm"
          >
            <option value="en">English</option>
            <option value="es">Español</option>
          </select>
        </div>

        <fieldset className="flex flex-col gap-1">
          <legend className="text-xs font-medium text-stone-500">
            {es ? "Seguir equipo o jugador" : "Follow a team or player"}
          </legend>
          <label htmlFor="focus" className="sr-only">
            {es ? "Seguir equipo o jugador" : "Follow a team or player"}
          </label>
          <select
            id="focus"
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            className="min-h-12 max-w-full rounded-lg border border-stone-200 bg-white px-3 text-sm"
          >
            <option value="">
              {es ? "Todas las historias" : "All stories"}
            </option>
            <optgroup label={es ? "Equipos" : "Teams"}>
              <option value="blue">Club del Faro</option>
              <option value="amber">Puerto Lumbre FC</option>
            </optgroup>
            <optgroup label={es ? "Jugadores" : "Players"}>
              {players.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} · {p.id.startsWith("blue") ? "FAR" : "LUM"}{" "}
                  {p.number}
                </option>
              ))}
            </optgroup>
          </select>
        </fieldset>
      </div>

      <p className="text-xs leading-relaxed text-stone-500">
        {es
          ? "Cambia la explicación del momento. Los datos del partido aparecen en Match insights."
          : "Changes the moment’s wording. Match data appears in Match insights."}
      </p>
    </div>
  );
}
