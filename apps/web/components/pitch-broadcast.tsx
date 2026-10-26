"use client";

import { useEffect, useState } from "react";
import { MatchStage } from "@/components/match-stage";
import { MatchSenseBrand } from "@/components/match-sense-brand";
import { useMatch } from "@/hooks/use-match";
import styles from "./pitch-broadcast.module.css";

const FRESH_FOR_MS = 5000;

function useFreshConnection(lastUpdatedAt: number, connected: boolean) {
  const [now, setNow] = useState(0);
  useEffect(() => {
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 500);
    return () => window.clearInterval(timer);
  }, []);
  return connected && lastUpdatedAt > 0 && now - lastUpdatedAt < FRESH_FOR_MS;
}

export function BroadcastStage({ sessionId }: { sessionId: string }) {
  const { match, connected, lastUpdatedAt } = useMatch(sessionId, false, "");
  const fresh = useFreshConnection(lastUpdatedAt, connected);

  return (
    <main className={styles.stagePage}>
      <div className={styles.stageFrame}>
        {fresh ? (
          <MatchStage
            match={match}
            language="en"
            expired={!match?.overlay}
            showExplanation={false}
            broadcastOutput
          />
        ) : (
          <div className={styles.offline}>
            <MatchSenseBrand dark />
            <p>Broadcast feed waiting for a live match connection.</p>
            <span>Reconnect the producer console to resume.</span>
          </div>
        )}
        <div className={styles.syntheticMark}>SYNTHETIC MATCH DEMO</div>
        <div className={styles.companionPrompt}>
          <strong>Explore this moment</strong>
          <span>Companion · /watch/{sessionId}</span>
        </div>
      </div>
    </main>
  );
}

export function BroadcastOverlay({ sessionId }: { sessionId: string }) {
  const { match, connected, lastUpdatedAt } = useMatch(sessionId, false, "");
  const fresh = useFreshConnection(lastUpdatedAt, connected);
  const visible = Boolean(
    fresh && match?.overlay && match.overlay_story_id,
  );

  return (
    <main className={styles.overlayPage} aria-live="polite">
      {visible && (
        <section className={styles.lowerThird} aria-label="Producer-approved insight">
          <span className={styles.label}>MATCHSENSE · APPROVED INSIGHT</span>
          <p>{match?.overlay}</p>
        </section>
      )}
    </main>
  );
}
