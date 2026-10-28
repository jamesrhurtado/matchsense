"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "./ui";

type ObsStatus = {
  status: string;
  scene?: string | null;
  stream_active?: boolean | null;
  reconnecting?: boolean | null;
  skipped_frames?: number | null;
  total_frames?: number | null;
  render_fps?: number | null;
};

const reasons: Record<string, string> = {
  disabled: "OBS monitoring is not enabled on the broadcast host.",
  unavailable_on_cloud:
    "OBS monitoring requires the API on the broadcast computer.",
  unavailable:
    "OBS is unavailable. Check OBS is open and its WebSocket server is enabled.",
  authentication_required:
    "OBS requires a WebSocket password on the broadcast host.",
  authentication_failed_or_unavailable:
    "OBS did not complete authentication. Check its WebSocket password and connection.",
  configuration_error:
    "The OBS port configured on the broadcast host is invalid.",
  protocol_error:
    "OBS responded unexpectedly. Check that OBS WebSocket version 5 is enabled.",
};

export function ObsStatusPanel() {
  const [status, setStatus] = useState<ObsStatus | null>(null);
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);
  const refresh = useCallback(async () => {
    setChecking(true);
    try {
      const result = await api<ObsStatus>("/broadcast/obs-status", {}, true);
      setStatus(result);
      setError("");
    } catch {
      setStatus(null);
      setError(
        "Could not check OBS. Verify your producer access and try again.",
      );
    } finally {
      setChecking(false);
    }
  }, []);
  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 15000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  return (
    <section
      aria-labelledby="obs-status-heading"
      className="mt-4 border-t border-stone-200 pt-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 id="obs-status-heading" className="text-sm font-semibold">
          OBS on the broadcast host
        </h4>
        <Button disabled={checking} onClick={() => void refresh()}>
          {checking ? "Checking…" : "Check OBS"}
        </Button>
      </div>
      <div
        role="status"
        aria-live="polite"
        className="mt-2 text-sm leading-relaxed text-stone-700"
      >
        {error ||
          (!status ? (
            "Checking OBS…"
          ) : status.status !== "connected" ? (
            reasons[status.status] || "OBS status is unavailable."
          ) : (
            <>
              <p>
                <strong>Connected.</strong>{" "}
                {status.reconnecting
                  ? "Stream reconnecting."
                  : status.stream_active === true
                    ? "OBS stream is active."
                    : status.stream_active === false
                      ? "OBS stream is stopped."
                      : "Stream status unavailable."}
              </p>
              <p>Scene: {status.scene || "unavailable"}.</p>
              {(typeof status.skipped_frames === "number" ||
                typeof status.render_fps === "number") && (
                <details className="mt-2 text-xs text-stone-600">
                  <summary className="min-h-9 cursor-pointer py-2">
                    Output performance
                  </summary>
                  {typeof status.skipped_frames === "number" &&
                    typeof status.total_frames === "number" && (
                      <p>
                        Skipped output frames: {status.skipped_frames} of{" "}
                        {status.total_frames}.
                      </p>
                    )}
                  {typeof status.render_fps === "number" && (
                    <p className="mt-1">
                      Render: {status.render_fps.toFixed(1)} fps.
                    </p>
                  )}
                </details>
              )}
            </>
          ))}
      </div>
    </section>
  );
}
