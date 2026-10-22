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
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="inline-flex rounded-lg border border-stone-200 p-1">
        <button
          aria-pressed={detail === "simple"}
          onClick={() => setDetail("simple")}
          className={cn(
            "min-h-10 rounded-md px-3 text-sm",
            detail === "simple" ? "bg-stone-900 text-white" : "text-stone-500",
          )}
        >
          {language === "es" ? "Explicar fácil" : "Explain simply"}
        </button>
        <button
          aria-pressed={detail === "detail"}
          onClick={() => setDetail("detail")}
          className={cn(
            "min-h-10 rounded-md px-3 text-sm",
            detail === "detail" ? "bg-stone-900 text-white" : "text-stone-500",
          )}
        >
          {language === "es" ? "Ver detalle" : "Show the detail"}
        </button>
      </div>
      <div className="flex min-h-12 items-center gap-2 rounded-lg border border-stone-200 px-3">
        <Globe2 size={15} className="text-stone-400" />
        <label htmlFor="language" className="sr-only">
          {language === "es" ? "Idioma" : "Language"}
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
      <label htmlFor="focus" className="sr-only">
        {language === "es"
          ? "Seguir a un jugador o equipo"
          : "Follow a player or team"}
      </label>
      <select
        id="focus"
        value={focus}
        onChange={(e) => setFocus(e.target.value)}
        className="min-h-12 max-w-full rounded-lg border border-stone-200 bg-white px-3 text-sm"
      >
        <option value="">
          {language === "es" ? "Jugada completa" : "Whole play"}
        </option>
        <optgroup label={language === "es" ? "Equipos" : "Teams"}>
          <option value="blue">Harbor City</option>
          <option value="amber">Alder Rovers</option>
        </optgroup>
        <optgroup label={language === "es" ? "Jugadores" : "Players"}>
          {players.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} · {p.id.startsWith("blue") ? "HBC" : "ALD"} {p.number}
            </option>
          ))}
        </optgroup>
      </select>
    </div>
  );
}
