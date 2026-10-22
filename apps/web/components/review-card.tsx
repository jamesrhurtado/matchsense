import { useEffect, useState } from "react";
import { ShieldCheck, ArrowUpRight } from "lucide-react";
import { Evidence } from "@/lib/api";
import { Button, Card, Tag } from "./ui";

export function ReviewCard({
  data,
  busy,
  onEdit,
}: {
  data: Evidence;
  busy: boolean;
  onEdit: (text: string, angle: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [copy, setCopy] = useState(data.story.review.revised_text);
  const r = data.story.review;
  const [angle, setAngle] = useState(
    data.story.narrative_plan?.angle || "progression",
  );
  useEffect(
    () => setCopy(data.story.review.revised_text),
    [data.story.id, data.story.revision],
  );
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <ShieldCheck size={16} />
          Wording review
        </h3>
        <Tag>{r.status}</Tag>
      </div>
      {data.story.mode?.includes("fallback") && (
        <p
          role="status"
          className="mt-3 rounded-lg bg-amber-50 p-3 text-pretty text-xs leading-relaxed text-amber-900"
        >
          Factual fallback used. AI wording was unavailable or did not pass
          review. This candidate uses verified template facts and still requires
          producer approval.
        </p>
      )}
      <p className="mt-3 text-pretty text-xs leading-relaxed text-stone-500">
        {r.reason}
      </p>
      {r.proposed_text && r.cycles > 0 && (
        <div className="mt-4 space-y-3 border-l-2 border-amber-400 pl-3">
          <p className="text-xs text-stone-500">Proposed wording reviewed</p>
          <p className="text-sm text-stone-500 line-through">
            {r.proposed_text}
          </p>
          <p className="text-sm leading-relaxed">{r.revised_text}</p>
        </div>
      )}
      {editing ? (
        <div className="mt-4">
          <label
            htmlFor="editor-angle"
            className="mb-2 block text-xs text-stone-600"
          >
            Emphasis
          </label>
          <select
            id="editor-angle"
            value={angle}
            onChange={(event) => setAngle(event.target.value)}
            className="mb-4 min-h-11 w-full rounded-lg border border-stone-200 px-3 text-sm"
          >
            <option value="progression">Ball movement</option>
            <option value="reception">Verified reception</option>
            <option
              value="historical_contrast"
              disabled={
                data.story.metrics.context?.relation !== "greater_than_each"
              }
            >
              Previous-pass comparison
            </option>
          </select>
          <label
            htmlFor="editor-copy"
            className="mb-2 block text-xs text-stone-500"
          >
            Suggest an emphasis or wording for evidence review
          </label>
          <textarea
            id="editor-copy"
            maxLength={1000}
            value={copy}
            onChange={(e) => setCopy(e.target.value)}
            rows={4}
            className="w-full rounded-lg border border-stone-200 p-3 text-sm"
          />
          <p className="mt-2 text-xs leading-relaxed text-stone-400">
            {data.story.mode?.includes("local")
              ? "Suggestions select supported facts and emphasis; custom sentences are not copied into the package. The resulting exact revision requires approval."
              : "Suggestions select supported facts and emphasis; the reviewer may revise or reject unsupported requests. Review the resulting exact revision before approval."}{" "}
            Editing invalidates any approval.
          </p>
          <div className="mt-3 flex gap-2">
            <Button
              disabled={busy || !copy.trim()}
              onClick={() => {
                onEdit(copy, angle);
                setEditing(false);
              }}
              tone="primary"
            >
              Submit for review
            </Button>
            <Button onClick={() => setEditing(false)}>Cancel</Button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setEditing(true)}
          className="mt-4 text-sm font-medium text-emerald-800"
        >
          Suggest an emphasis
          <ArrowUpRight size={13} className="ml-1 inline" />
        </button>
      )}
    </Card>
  );
}
