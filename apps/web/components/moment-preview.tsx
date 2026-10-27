"use client";

import { useState } from "react";
import { ArrowRight, Check, ScanLine, ShieldCheck } from "lucide-react";
import { ListenButton } from "./listen-button";
import { cn } from "@/lib/api";

// Curated presentation of the documented Pressure Swing synthetic fixture.
// This is not a live session, an AI run, or a producer publication.
export function MomentPreview() {
  const [language, setLanguage] = useState("en");
  const [detailed, setDetailed] = useState(false);
  const [evidence, setEvidence] = useState(false);
  const es = language === "es";
  return (
    <section
      id="moment-preview"
      tabIndex={-1}
      aria-label="Interactive match example"
      className="min-w-0 scroll-mt-6 overflow-hidden rounded-2xl border border-[#29463b] bg-[#132c24] text-white shadow-xl"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/15 px-5 py-4">
        <span className="flex items-center gap-2 text-xs font-medium text-emerald-100">
          <span
            className="size-2 rounded-full bg-emerald-300"
            aria-hidden="true"
          />
          {es ? "EJEMPLO PREPARADO" : "PREPARED EXAMPLE"}
        </span>
        <span className="text-xs text-white/65">
          {es
            ? "Datos sintéticos · sin llamadas de IA"
            : "Synthetic data · no AI calls"}
        </span>
      </div>
      <div className="flex items-center justify-between gap-3 px-5 pt-5 text-sm font-semibold sm:px-6">
        <span>
          Club del Faro <span className="mx-1 font-normal text-white/50">vs</span>{" "}
          Puerto Lumbre FC
        </span>
        <span className="shrink-0 rounded-md bg-white/10 px-2 py-1 font-mono text-xs tabular-nums">
          01:31
        </span>
      </div>
      <div className="px-4 pt-4 sm:px-6">
        <svg
          viewBox="0 0 600 265"
          role="img"
          aria-labelledby="moment-pitch-title moment-pitch-desc"
          className="w-full rounded-lg bg-[#245841]"
        >
          <title id="moment-pitch-title">
            {es
              ? "Esquema de un pase de 30 metros hacia delante"
              : "Schematic of a 30-metre forward pass"}
          </title>
          <desc id="moment-pitch-desc">
            {es
              ? "Antes del pase, el promedio de rivales a seis metros del pasador era 2.0. Después, el promedio alrededor del receptor era 0.4. El esquema no representa coordenadas exactas."
              : "Before the pass, an average of 2.0 opponents were within six metres of the passer. After reception, the average around the receiver was 0.4. The diagram does not show exact coordinates."}
          </desc>
          {[0, 2, 4, 6].map((n) => (
            <rect
              key={n}
              x={18 + n * 80}
              y="15"
              width="80"
              height="235"
              fill="#ffffff"
              opacity="0.035"
            />
          ))}
          <g fill="none" stroke="#c7e4d3" strokeOpacity="0.4" strokeWidth="1.5">
            <rect x="18" y="15" width="564" height="235" />
            <path d="M300 15v235M18 68h65v129H18M582 68h-65v129h65" />
            <circle cx="300" cy="132" r="42" />
          </g>
          <circle
            cx="182"
            cy="150"
            r="50"
            fill="#ffffff"
            fillOpacity="0.07"
            stroke="#d1fae5"
            strokeDasharray="4 5"
            strokeOpacity="0.45"
          />
          <circle
            cx="410"
            cy="105"
            r="50"
            fill="#a7f3d0"
            fillOpacity="0.12"
            stroke="#a7f3d0"
            strokeDasharray="4 5"
          />
          <path
            d="M200 146L388 110"
            stroke="#d1fae5"
            strokeWidth="3"
            strokeDasharray="7 5"
          />
          <path
            d="M378 103l15 6-12 12"
            fill="none"
            stroke="#d1fae5"
            strokeWidth="3"
          />
          <g fill="#e9b86a" stroke="#173c2b" strokeWidth="2">
            <circle cx="158" cy="123" r="10" />
            <circle cx="210" cy="176" r="10" />
          </g>
          <g fill="#d1fae5" stroke="#132c24" strokeWidth="3">
            <circle cx="182" cy="150" r="13" />
            <circle cx="410" cy="105" r="13" />
          </g>
          <rect x="263" y="104" width="68" height="26" rx="6" fill="#132c24" />
          <text
            x="297"
            y="122"
            textAnchor="middle"
            fill="white"
            fontSize="13"
            fontFamily="inherit"
          >
            30 m →
          </text>
          <g
            fill="#ecfdf5"
            fontFamily="inherit"
            fontSize="12"
            textAnchor="middle"
          >
            <text x="182" y="220">
              {es ? "ANTES · PASADOR" : "BEFORE · PASSER"}
            </text>
            <text x="410" y="181">
              {es ? "DESPUÉS · RECEPTOR" : "AFTER · RECEIVER"}
            </text>
          </g>
        </svg>
        <p className="mt-2 text-xs text-white/60">
          {es
            ? "Esquema ilustrativo de la jugada; no son posiciones exactas."
            : "Illustrative play diagram; not exact player positions."}
        </p>
      </div>
      <div className="px-5 pb-5 pt-5 sm:px-6 sm:pb-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-semibold text-emerald-200">
            {es ? "QUÉ CAMBIÓ" : "WHAT CHANGED"}
          </span>
          <div
            className="flex items-center gap-1 rounded-lg border border-white/20 p-1"
            aria-label="Example language"
          >
            {[
              ["en", "EN"],
              ["es", "ES"],
            ].map(([value, label]) => (
              <button
                key={value}
                aria-label={
                  value === "en" ? "Example in English" : "Ejemplo en español"
                }
                aria-pressed={language === value}
                onClick={() => setLanguage(value)}
                className={cn(
                  "min-h-9 min-w-10 rounded-md px-2 text-xs font-semibold",
                  language === value
                    ? "bg-emerald-100 text-emerald-950"
                    : "text-white/75 hover:bg-white/10",
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <h2 className="mt-3 text-balance text-2xl font-semibold leading-tight sm:text-3xl">
          {es
            ? "Un pase hacia menos rivales cercanos."
            : "One pass. Fewer opponents nearby."}
        </h2>
        <div
          aria-live="polite"
          className="mt-3 min-h-24 text-pretty text-sm leading-relaxed text-white/80"
        >
          <p>
            {detailed
              ? es
                ? "El pase avanzó 30 m. El promedio de rivales a 6 m bajó de 2.0 alrededor del pasador a 0.4 alrededor del receptor, comparando dos ventanas de 2 s con cobertura completa."
                : "The pass advanced 30 m. Average opponents within 6 m fell from 2.0 around the passer to 0.4 around the receiver, comparing two fully covered 2 s windows."
              : es
                ? "El balón avanzó 30 metros. Tras la recepción, había menos rivales cerca del receptor, en promedio, que alrededor del pasador antes del pase."
                : "The ball moved 30 metres forward. After reception, the receiver had fewer opponents nearby on average than the passer had before the pass."}
          </p>
        </div>
        <div className="mt-3 grid grid-cols-3 divide-x divide-white/15 rounded-xl border border-white/15 py-4 text-center">
          {[
            ["2.0", es ? "Antes" : "Before"],
            ["30 m", es ? "Avance" : "Forward"],
            ["0.4", es ? "Después" : "After"],
          ].map(([value, label]) => (
            <div key={label}>
              <p className="text-2xl font-semibold tabular-nums text-emerald-100">
                {value}
              </p>
              <p className="mt-1 text-xs text-white/65">{label}</p>
            </div>
          ))}
        </div>
        <div className="mt-2">
          <ListenButton
            dark
            language={language}
            text={
              es
                ? "Ejemplo sintético de Pressure Swing. El pase avanzó treinta metros. El promedio de rivales a seis metros bajó de dos alrededor del pasador a cero coma cuatro alrededor del receptor. Se comparan dos segundos antes del pase con dos segundos desde la recepción, con cobertura completa. Esto mide proximidad, no intención táctica ni la causa de un gol."
                : "Synthetic Pressure Swing example. The pass advanced thirty metres. Average opponents within six metres fell from two around the passer to zero point four around the receiver. This compares two seconds before release with two seconds from reception, with complete coverage. This measures proximity, not tactical intent or the cause of a goal."
            }
          />
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
          <button
            aria-pressed={detailed}
            onClick={() => setDetailed(!detailed)}
            className="min-h-11 rounded-lg px-2 text-sm text-emerald-100 underline decoration-white/30 underline-offset-4 hover:bg-white/10"
          >
            {detailed
              ? es
                ? "Explicar fácil"
                : "Explain simply"
              : es
                ? "Ver detalle"
                : "Show the detail"}
          </button>
          <button
            aria-expanded={evidence}
            aria-controls="example-evidence"
            onClick={() => setEvidence(!evidence)}
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-white/25 px-3 text-sm font-semibold hover:bg-white/10"
          >
            <ScanLine size={16} aria-hidden="true" />
            {es ? "Ver la evidencia" : "Check the evidence"}
            <ArrowRight size={14} aria-hidden="true" />
          </button>
        </div>
        {evidence && (
          <div
            id="example-evidence"
            className="mt-4 rounded-xl bg-white p-4 text-stone-800"
          >
            <h3 className="flex items-center gap-2 text-sm font-semibold">
              <ShieldCheck size={16} aria-hidden="true" />
              {es
                ? "Qué sostiene esta explicación"
                : "What supports this explanation"}
            </h3>
            <ul className="mt-3 space-y-2 text-sm leading-relaxed">
              <li className="flex gap-2">
                <Check
                  size={16}
                  className="mt-0.5 shrink-0 text-emerald-800"
                  aria-hidden="true"
                />
                {es
                  ? "Dos segundos antes del pase y dos desde la recepción; radio de 6 m."
                  : "Two seconds before release and two from reception; 6 m radius."}
              </li>
              <li className="flex gap-2">
                <Check
                  size={16}
                  className="mt-0.5 shrink-0 text-emerald-800"
                  aria-hidden="true"
                />
                {es
                  ? "Cobertura observada: 100% en ambas ventanas."
                  : "Observed coverage: 100% in both windows."}
              </li>
            </ul>
            <p className="mt-3 border-t border-stone-200 pt-3 text-xs leading-relaxed text-stone-600">
              {es
                ? "Mide proximidad, no intención táctica ni la causa de un gol. Ejemplo preparado del escenario sintético Pressure Swing, disponible para revisar en la consola cuando esté habilitado."
                : "Measures proximity, not tactical intent or the cause of a goal. Prepared example from the synthetic Pressure Swing scenario, available for review in the desk when enabled."}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
