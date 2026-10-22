"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, Match } from "@/lib/api";

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
      setMatch((previous) =>
        previous &&
        previous.session_id === data.session_id &&
        previous.cursor > data.cursor
          ? previous
          : data,
      );
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
      const timer = setInterval(refresh, 350);
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
      setMatch((previous) =>
        previous &&
        previous.session_id === data.session_id &&
        previous.cursor > data.cursor
          ? previous
          : data,
      );
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
  }, [id, isProducer, refresh, selectedStoryId, context]);
  return { match, error, connected, refresh };
}
