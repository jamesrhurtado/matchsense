import { Metrics, cn, timecode } from "@/lib/api";

/** Display precision never participates in the evidence comparison. */
export function displayMetres(value: number) {
  return value.toFixed(1);
}

export function PassComparison({
  metrics,
  language,
}: {
  metrics: Metrics;
  language: string;
}) {
  const es = language === "es";
  if (!metrics.context || metrics.forward_pass_m == null) return null;
  const comparators = [...metrics.context.comparators].sort(
    (a, b) => a.resolution_ms - b.resolution_ms,
  );
  const rows = [
    ...comparators.map((pass, index) => ({
      id: pass.pass_id,
      label: es ? `Anterior ${index + 1}` : `Previous ${index + 1}`,
      at: pass.resolution_ms,
      value: pass.forward_m,
      current: false,
    })),
    {
      id: "current",
      label: es ? "Pase actual" : "Current pass",
      at: metrics.reception_ms ?? 0,
      value: metrics.forward_pass_m,
      current: true,
    },
  ];
  const min = Math.min(0, ...rows.map((row) => row.value));
  const max = Math.max(0, ...rows.map((row) => row.value));
  const span = max - min || 1;
  const zero = (-min / span) * 100;
  const roundedTie = comparators.some(
    (pass) =>
      pass.forward_m !== metrics.forward_pass_m &&
      displayMetres(pass.forward_m) === displayMetres(metrics.forward_pass_m!),
  );
  return (
    <div
      className="border-t border-stone-200 p-3"
      data-testid="pass-comparison"
    >
      <h3 className="text-sm font-semibold">
        {es ? "Desplazamiento hacia adelante" : "Forward displacement"}
      </h3>
      <p className="mt-1 text-xs text-stone-600">
        {es
          ? "El pase actual y los tres pases completados anteriores del equipo"
          : "Current pass and previous three completed team passes"}
      </p>
      <ul
        className="mt-3 space-y-3"
        aria-label={es ? "Comparación de distancias" : "Distance comparison"}
      >
        {rows.map((row) => (
          <li
            key={row.id}
            className={cn(
              "rounded-lg p-2",
              row.current
                ? "border border-emerald-300 bg-emerald-50"
                : "bg-stone-50",
            )}
          >
            <div className="mb-1 flex justify-between gap-2 text-xs tabular-nums">
              <span
                className={row.current ? "font-semibold" : "text-stone-600"}
              >
                {row.label} · {timecode(row.at)}
              </span>
              <span className="font-medium">{displayMetres(row.value)} m</span>
            </div>
            <div
              aria-hidden="true"
              className="relative h-2 rounded bg-stone-200"
            >
              <span
                className="absolute -top-0.5 h-3 border-l border-stone-500"
                style={{ left: `${zero}%` }}
              />
              <span
                className={cn(
                  "absolute h-2 rounded",
                  row.current ? "bg-emerald-700" : "bg-stone-500",
                )}
                style={{
                  left: `${((Math.min(0, row.value) - min) / span) * 100}%`,
                  width: `${(Math.abs(row.value) / span) * 100}%`,
                }}
              />
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-stone-600">
        {es
          ? "Distancias mostradas con un decimal; valores negativos indican retroceso."
          : "Distances shown to one decimal; negative values indicate backward movement."}
        {roundedTie &&
          (es
            ? " Algunos valores parecen iguales al redondear; la comparación usa los valores originales."
            : " Some values appear equal after rounding; the comparison uses original values.")}
      </p>
      <details className="mt-2">
        <summary className="min-h-11 cursor-pointer py-3 text-xs font-medium">
          {es ? "Valores originales y fuentes" : "Original values and sources"}
        </summary>
        <table className="w-full text-left text-xs tabular-nums">
          <caption className="mb-2 text-left text-stone-600">
            {es
              ? "Valores originales sin redondear para comprobar la comparación"
              : "Unrounded source values for checking the comparison"}
          </caption>
          <thead>
            <tr>
              <th scope="col">{es ? "Pase" : "Pass"}</th>
              <th scope="col">{es ? "Recepción" : "Reception"}</th>
              <th scope="col">m</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                className={
                  row.current
                    ? "border-t border-emerald-200 bg-emerald-50"
                    : "border-t border-stone-100"
                }
              >
                <th scope="row" className="break-all py-2 pr-2 font-normal">
                  {row.current ? row.label : row.id}
                </th>
                <td>{timecode(row.at)}</td>
                <td>{String(row.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
      <p className="mt-2 text-xs text-stone-600">
        {es
          ? "Solo esta repetición; no demuestra superioridad táctica."
          : "This replay only; does not establish tactical superiority."}
      </p>
    </div>
  );
}
