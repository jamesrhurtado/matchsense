"use client";
import { useEffect } from "react";
import { api, Story, Variant } from "@/lib/api";

/** Two animation frames after content commit. No user identity or wall clock. */
export function useRenderAck(
  path: string,
  story: Story | null | undefined,
  variant: Variant | null,
  enabled: boolean,
) {
  useEffect(() => {
    if (!enabled || !story || !variant) return;
    const start = performance.now();
    let second = 0;
    const first = requestAnimationFrame(() => {
      second = requestAnimationFrame(() => {
        void api(`${path}/stories/${story.id}/render-ack`, {
          method: "POST",
          body: JSON.stringify({
            revision: story.revision,
            evidence_revision: story.evidence_revision,
            event_id: crypto.randomUUID(),
            paint_interval_ms: Math.min(60000, performance.now() - start),
          }),
        }).catch(() => {
          /* Missing acknowledgment remains missing telemetry. */
        });
      });
    });
    return () => {
      cancelAnimationFrame(first);
      cancelAnimationFrame(second);
    };
  }, [path, story?.id, story?.revision, variant?.id, enabled]);
}
