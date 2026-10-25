export type EditorialSummary = {
  angle: string;
  lead: string;
  context: string;
  review: string;
  changes: string[];
  fallback: string | null;
  outcome: string;
};

/** Public, observable selections and verdicts, never private model reasoning. */
export function DecisionSummary({
  summary,
}: {
  summary?: EditorialSummary | null;
}) {
  if (!summary) return null;
  return (
    <section
      className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4"
      aria-label="Editorial decision summary"
    >
      <h3 className="text-sm font-semibold text-emerald-950">
        Why this explanation
      </h3>
      <dl className="mt-3 space-y-3 text-sm text-emerald-950">
        <div>
          <dt className="font-medium">Selected angle · {summary.angle}</dt>
        </div>
        <div>
          <dt className="font-medium">Previous-pass context</dt>
          <dd className="mt-1">{summary.context}</dd>
        </div>
        <div>
          <dt className="font-medium">Review · {summary.outcome}</dt>
          <dd className="mt-1">{summary.review}</dd>
        </div>
      </dl>
      {summary.changes.map((change, i) => (
        <p className="mt-3 text-sm" key={i}>
          {change}
        </p>
      ))}
      {summary.fallback && (
        <p className="mt-3 text-sm font-medium">{summary.fallback}</p>
      )}
    </section>
  );
}
