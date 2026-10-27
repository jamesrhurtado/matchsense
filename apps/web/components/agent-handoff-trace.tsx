import {
  ArrowRight,
  CheckCircle2,
  Circle,
  LoaderCircle,
  ShieldCheck,
  UserRoundCheck,
} from "lucide-react";
import type { EditorialSummary } from "./decision-summary";

type TraceEntry = {
  role?: string;
  action?: string;
  status?: string;
  duration_ms?: number;
  plan?: { angle?: string; simple_claim_ids?: string[]; detail_claim_ids?: string[] };
  verdicts?: { verdict?: string }[];
};

function textStatus(status: string | undefined, language: "en" | "es") {
  const labels: Record<string, [string, string]> = {
    propose: ["Selected a supported angle", "Eligió un enfoque respaldado"],
    supported: ["Supported the facts and wording", "Respaldó los datos y la redacción"],
    revise: ["Requested one focused revision", "Pidió una revisión puntual"],
    reject: ["Rejected the unsupported candidate", "Rechazó la propuesta sin respaldo"],
    abstain: ["Found no defensible explanation", "No encontró una explicación defendible"],
    needs_evidence: ["Requested more evidence", "Solicitó más evidencia"],
    failed: ["Could not complete this step", "No pudo completar este paso"],
    started: ["Working now", "Trabajando ahora"],
  };
  const label = labels[status || ""];
  return label ? label[language === "es" ? 1 : 0] : language === "es" ? "Sin decisión registrada" : "No decision recorded";
}

function Badge({ children, active, complete }: { children: string; active?: boolean; complete?: boolean }) {
  const Icon = active ? LoaderCircle : complete ? CheckCircle2 : Circle;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${active ? "bg-sky-100 text-sky-900" : complete ? "bg-emerald-100 text-emerald-900" : "bg-stone-100 text-stone-600"}`}>
      <Icon size={13} className={active ? "animate-spin" : ""} aria-hidden="true" />
      {children}
    </span>
  );
}

function StepCard({
  number,
  title,
  description,
  status,
  active,
  complete,
  children,
}: {
  number: string;
  title: string;
  description: string;
  status: string;
  active?: boolean;
  complete?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <section className="min-w-0 rounded-xl border border-stone-200 bg-white p-4" aria-label={title}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">{number}</p>
        <Badge active={active} complete={complete}>{status}</Badge>
      </div>
      <h4 className="mt-3 text-sm font-semibold text-stone-950">{title}</h4>
      <p className="mt-1 text-sm leading-relaxed text-stone-600">{description}</p>
      {children}
    </section>
  );
}

/** Displays recorded agent actions and the human approval boundary, never model prompts or private reasoning. */
export function AgentHandoffTrace({
  trace: rawTrace,
  summary,
  pending = false,
  language = "en",
}: {
  trace?: unknown;
  summary?: EditorialSummary | null;
  pending?: boolean;
  language?: "en" | "es";
}) {
  const es = language === "es";
  const trace = Array.isArray(rawTrace) ? rawTrace as TraceEntry[] : [];
  const directorCalls = trace.filter((entry) => entry.role === "Story Director" && entry.action === "model_decision");
  const reviewerCalls = trace.filter((entry) => entry.role === "Claim Reviewer" && entry.action === "model_decision");
  const selections = trace.filter((entry) => entry.role === "Story Director" && entry.action === "select_claims");
  const reviews = trace.filter((entry) => entry.role === "Claim Reviewer" && entry.action === "claim_verdicts");
  const latestReview = reviews.at(-1);
  const fallback = trace.some((entry) => entry.action === "template_fallback") || Boolean(summary?.fallback);
  const directorCall = directorCalls.at(-1);
  const reviewerCall = reviewerCalls.at(-1);
  const selected = selections.at(-1);
  const directorActive = directorCall?.status === "started" || (!directorCall && pending);
  const reviewerActive = reviewerCall?.status === "started" || (Boolean(selected) && !reviewerCall && pending);
  const directorComplete = Boolean(selected);
  const reviewerComplete = reviewerCall?.status === "supported" || reviewerCall?.status === "revise" || reviewerCall?.status === "reject";
  const directorStatus = selected
    ? (es ? "Propuesta entregada" : "Proposal handed off")
    : directorCall
      ? textStatus(directorCall.status, language)
      : fallback
        ? (es ? "Plantilla factual de recuperación" : "Recovered with factual template")
        : pending
          ? (es ? "En cola" : "Queued")
          : (es ? "Sin ejecución registrada" : "No run recorded");
  const reviewerStatus = reviewerCall
    ? textStatus(reviewerCall.status, language)
    : fallback
      ? (es ? "No disponible en esta recuperación" : "Skipped in recovery path")
      : pending && !selected
        ? (es ? "Esperando al Director" : "Waiting for Director")
        : pending
          ? (es ? "Esperando revisión" : "Waiting for review")
          : (es ? "Sin revisión registrada" : "No review recorded");
  const plan = selected?.plan;
  const angle = plan?.angle || summary?.angle;
  const claimIds = plan?.simple_claim_ids || [];
  const verdicts = latestReview?.verdicts || [];
  const supportedCount = verdicts.filter((verdict) => verdict.verdict === "supported").length;
  const firstRepair = reviews.some((entry) => entry.status === "revise");

  return (
    <section className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 sm:p-5" aria-label={es ? "Traspaso entre agentes" : "Agent handoff"} aria-live={pending ? "polite" : undefined}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-emerald-950">{es ? "Así colaboran los agentes" : "How the agents work together"}</h3>
          <p className="mt-1 max-w-3xl text-sm leading-relaxed text-emerald-950/75">
            {es
              ? "Comparten la misma evidencia verificada, pero cumplen roles distintos. El Director propone; el Reviewer comprueba por separado."
              : "Both agents use the same verified evidence, but have different jobs. The Director proposes; the Reviewer checks it independently."}
          </p>
        </div>
        <span className="rounded-full border border-emerald-200 bg-white/80 px-2.5 py-1 text-xs font-medium text-emerald-950">
          {es ? "Estado del flujo" : "Workflow state"}
        </span>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr] md:items-stretch">
        <StepCard
          number={es ? "Paso 1" : "Step 1"}
          title="Story Director"
          description={es ? "Selecciona el momento y el enfoque usando los hechos disponibles." : "Selects the moment and angle using the available facts."}
          status={directorStatus}
          active={directorActive}
          complete={directorComplete}
        >
          {(angle || claimIds.length > 0) && (
            <p className="mt-3 rounded-lg bg-stone-50 px-3 py-2 text-xs text-stone-700">
              {angle ? `${es ? "Enfoque" : "Angle"}: ${angle.replaceAll("_", " ")}` : ""}
              {claimIds.length ? ` · ${es ? "afirmaciones" : "claims"}: ${claimIds.join(", ")}` : ""}
            </p>
          )}
        </StepCard>

        <div className="flex items-center justify-center text-emerald-700" aria-label={es ? "Traspaso de evidencia compartida" : "Shared evidence handoff"}>
          <ArrowRight size={20} className="rotate-90 md:rotate-0" aria-hidden="true" />
        </div>

        <StepCard
          number={es ? "Paso 2" : "Step 2"}
          title="Claim Reviewer"
          description={es ? "Recibe el plan y vuelve a contrastar cada afirmación y su redacción." : "Receives the plan and independently checks each claim and its wording."}
          status={reviewerStatus}
          active={reviewerActive}
          complete={reviewerComplete}
        >
          {latestReview && verdicts.length > 0 && (
            <p className="mt-3 rounded-lg bg-stone-50 px-3 py-2 text-xs text-stone-700">
              {es ? "Afirmaciones respaldadas" : "Supported claims"}: {supportedCount}/{verdicts.length}
            </p>
          )}
          {firstRepair && (
            <p className="mt-2 text-xs font-medium text-amber-800">
              {es ? "El Director ajustó la selección y el Reviewer la volvió a comprobar." : "The Director revised the selection and the Reviewer checked it again."}
            </p>
          )}
        </StepCard>

        <div className="flex items-center justify-center text-emerald-700" aria-label={es ? "Traspaso para aprobación humana" : "Handoff for human approval"}>
          <ArrowRight size={20} className="rotate-90 md:rotate-0" aria-hidden="true" />
        </div>

        <StepCard
          number={es ? "Paso 3" : "Step 3"}
          title={es ? "Productor · tú" : "Producer · you"}
          description={es ? "Decides si se publica. Ningún agente aprueba ni emite el contenido." : "You decide whether it is published. Neither agent approves or broadcasts content."}
          status={es ? "Aprobación humana" : "Human approval"}
          complete={false}
        >
          <div className="mt-3 flex items-center gap-2 text-xs font-medium text-stone-600">
            <UserRoundCheck size={15} aria-hidden="true" />
            {es ? "El control editorial sigue contigo" : "Editorial control stays with you"}
          </div>
        </StepCard>
      </div>

      {fallback && (
        <p className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950">
          <ShieldCheck size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
          <span>{es ? "Recuperación: se usó una plantilla basada en hechos verificados. La aprobación del productor sigue siendo necesaria." : "Recovery: a source-scoped factual template was used. Producer approval is still required."}</span>
        </p>
      )}

      {selected && !firstRepair && reviewerCall?.status === "supported" && (
        <p className="mt-3 text-sm text-emerald-950/80">
          {es ? "Resultado de la revisión: el Reviewer respaldó la propuesta original; no hizo falta cambiarla." : "Review result: the Reviewer supported the original proposal; no repair was needed."}
        </p>
      )}
      {summary?.changes?.map((change, index) => (
        <p key={index} className="mt-3 rounded-lg bg-white/80 p-3 text-sm text-stone-700">{change}</p>
      ))}
    </section>
  );
}
