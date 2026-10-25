"use client";
import { useEffect, useState } from "react";
import { api, Story, Variant } from "@/lib/api";

/** A response is visible only for its exact story revision and preferences. */
export function useStoryVariant(
  path: string,
  story: Story | null | undefined,
  status: string | undefined,
  language: string,
  detail: string,
  focus: string,
  isProducer: boolean,
) {
  const key = `${story?.id}:${story?.revision}:${language}:${detail}:${focus}`;
  const [result, setResult] = useState<{
    key: string;
    variant: Variant;
  } | null>(null);
  useEffect(() => {
    if (!story) return;
    let ignore = false;
    api<Variant>(
      `${path}/stories/${story.id}/variants?language=${language}&detail=${detail}${focus ? `&focus=${encodeURIComponent(focus)}` : ""}`,
      {},
      isProducer,
    )
      .then((variant) => {
        if (
          !ignore &&
          variant.story_id === story.id &&
          variant.revision === story.revision
        )
          setResult({ key, variant });
      })
      .catch(() => {
        if (!ignore) setResult(null);
      });
    return () => {
      ignore = true;
    };
  }, [
    path,
    story?.id,
    story?.revision,
    status,
    language,
    detail,
    focus,
    isProducer,
    key,
  ]);
  return story && result?.key === key ? result.variant : null;
}
