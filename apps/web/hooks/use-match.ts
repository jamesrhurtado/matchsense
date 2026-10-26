"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, Match } from "@/lib/api";

function frameSignature(frame: Match["frame"]) {
  if (!frame) return "missing";
  return `${frame.players
    .map((player) => `${player.player_id}:${player.x_m}:${player.y_m}`)
    .join("|")}:${frame.ball?.x_m ?? "-"}:${frame.ball?.y_m ?? "-"}`;
}

function withMotion(previous: Match | null, next: Match): Match {
  if (!previous || !next.frame || next.frame_time_ms == null) {
    return { ...next, motion_from_frame: null };
  }
  if (previous.frame_time_ms == null) {
    return { ...next, motion_from_frame: null };
  }
  const delta = next.frame_time_ms - previous.frame_time_ms;
  if (delta > 0) {
    const maxGapMs = 2000 / Math.max(1, next.tracking_hz ?? 10);
    const canAnimate = delta <= maxGapMs && previous.frame !== null;
    return {
      ...next,
      motion_from_frame: canAnimate ? previous.frame : null,
      motion_duration_ms: canAnimate
        ? Math.round(delta / Math.max(0.25, next.speed || 1))
        : null,
    };
  }
  if (
    delta === 0 &&
    frameSignature(previous.frame) === frameSignature(next.frame)
  ) {
    return {
      ...next,
      motion_from_frame: previous.motion_from_frame ?? null,
      motion_duration_ms: previous.motion_duration_ms ?? null,
    };
  }
  return { ...next, motion_from_frame: null };
}

export function useMatch(
  id: string,
  isProducer: boolean,
  selectedStoryId: string,
) {
  const [match, setMatch] = useState<Match | null>(null);
  const [error, setError] = useState("");
  const [connected, setConnected] = useState(false);
  const context = `${id}:${isProducer}:${selectedStoryId}`;
  const currentContext = useRef(context);
  currentContext.current = context;
  const refreshing = useRef<string | null>(null);
  const pollInterval = isProducer && match?.running
    ? Math.max(
        25,
        1000 /
          (Math.max(1, match.tracking_hz ?? 10) * Math.max(0.25, match.speed || 1)),
      )
    : 350;
  const refresh = useCallback(async () => {
    if (refreshing.current === context) return;
    refreshing.current = context;
    try {
      const data = await api<Match>(
        `/replay-sessions/${id}/snapshot${selectedStoryId ? `?story_id=${encodeURIComponent(selectedStoryId)}` : ""}`,
        {},
        isProducer,
      ).catch((error) => {
        if (!selectedStoryId) throw error;
        return api<Match>(`/replay-sessions/${id}/snapshot`, {}, isProducer);
      });
      if (currentContext.current !== context) return;
      setMatch((previous) => {
        if (
          previous &&
          previous.session_id === data.session_id &&
          previous.cursor > data.cursor
        )
          return previous;
        return withMotion(
          previous?.session_id === data.session_id ? previous : null,
          data,
        );
      });
      setConnected(true);
      setError("");
    } catch (e) {
      if (currentContext.current === context) {
        setError((e as Error).message);
        setConnected(false);
      }
    } finally {
      if (refreshing.current === context) refreshing.current = null;
    }
  }, [id, isProducer, selectedStoryId, context]);
  useEffect(() => {
    void refresh();
    if (isProducer) {
      const timer = setInterval(refresh, pollInterval);
      return () => clearInterval(timer);
    }
    const source = new EventSource(`/api/replay-sessions/${id}/stream`);
    const update = (event: MessageEvent) => {
      if (currentContext.current !== context) return;
      if (selectedStoryId) {
        void refresh();
        return;
      }
      const data: Match = JSON.parse(event.data);
      setMatch((previous) => {
        if (
          previous &&
          previous.session_id === data.session_id &&
          previous.cursor > data.cursor
        )
          return previous;
        return withMotion(
          previous?.session_id === data.session_id ? previous : null,
          data,
        );
      });
      setConnected(true);
      setError("");
    };
    source.addEventListener("resync", update as EventListener);
    source.addEventListener("state_update", update as EventListener);
    source.onerror = () => {
      if (currentContext.current === context) setConnected(false);
    };
    const recovery = setInterval(() => void refresh(), 2000);
    return () => {
      source.close();
      clearInterval(recovery);
    };
  }, [id, isProducer, refresh, selectedStoryId, context, pollInterval]);
  return { match, error, connected, refresh };
}
