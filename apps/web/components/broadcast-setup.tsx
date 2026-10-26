"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, Check, Copy, Radio } from "lucide-react";
import { Match } from "@/lib/api";
import { companionUrl } from "@/lib/broadcast-links";
import { CompanionQR } from "./companion-qr";
import { Button, Tag } from "./ui";

export function BroadcastSetup({
  id,
  match,
  connected,
  publicBase = "",
}: {
  id: string;
  match: Match | null;
  connected: boolean;
  publicBase?: string;
}) {
  const [origin, setOrigin] = useState("");
  const [copied, setCopied] = useState("");
  const [copyError, setCopyError] = useState("");
  useEffect(() => {
    setOrigin(window.location.origin);
  }, []);
  const publicUrl =
    match?.session_id === id ? companionUrl(publicBase, origin, id) : null;
  const sources = [
    {
      key: "stage",
      label: "Broadcast stage",
      description: "OBS source 1 · the synthetic match",
      url: `${origin}/broadcast/${encodeURIComponent(id)}`,
    },
    {
      key: "overlay",
      label: "OBS overlay",
      description: "OBS source 2 · approved explanation, above the stage",
      url: `${origin}/overlay/${encodeURIComponent(id)}`,
    },
    {
      key: "companion",
      label: "Viewer companion",
      description: publicUrl
        ? "For your audience · this same session"
        : "Local rehearsal · opens on this Mac",
      url: publicUrl || `${origin}/watch/${encodeURIComponent(id)}`,
    },
  ];
  async function copy(key: string, url: string) {
    setCopyError("");
    setCopied("");
    try {
      await navigator.clipboard.writeText(url);
      setCopied(key);
    } catch {
      setCopyError(
        "Could not copy. Select the link below and copy it manually.",
      );
    }
  }
  return (
    <section
      id="broadcast-setup"
      aria-labelledby="broadcast-setup-heading"
      className="my-5 rounded-2xl border border-emerald-200 bg-white p-4 shadow-sm sm:p-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2
            id="broadcast-setup-heading"
            className="flex items-center gap-2 text-lg font-semibold"
          >
            <Radio size={18} aria-hidden="true" /> Prepare broadcast
          </h2>
          <p className="mt-1 text-sm text-stone-600">
            One session, from the producer desk to YouTube and the fan.
          </p>
        </div>
        <Tag
          className={
            connected
              ? "bg-emerald-50 text-emerald-900"
              : "bg-amber-50 text-amber-900"
          }
        >
          {connected ? "App feed connected" : "App feed reconnecting"}
        </Tag>
      </div>
      <div className="mt-5 grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <div className="min-w-0 space-y-3">
          {sources.map((source) => (
            <div
              key={source.key}
              className="rounded-xl border border-stone-200 p-3 sm:p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold">{source.label}</h3>
                  <p className="mt-1 text-xs text-stone-600">
                    {source.description}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    disabled={!origin}
                    onClick={() => void copy(source.key, source.url)}
                    aria-label={`Copy ${source.label} link`}
                  >
                    {copied === source.key ? (
                      <Check size={15} aria-hidden="true" />
                    ) : (
                      <Copy size={15} aria-hidden="true" />
                    )}
                    {copied === source.key ? "Copied" : "Copy"}
                  </Button>
                  <a
                    href={origin ? source.url : undefined}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Open ${source.label}`}
                    className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-stone-300 px-3 text-sm font-semibold hover:bg-emerald-50"
                  >
                    Open <ArrowUpRight size={14} aria-hidden="true" />
                  </a>
                </div>
              </div>
              <p className="mt-2 select-all break-all font-mono text-xs leading-relaxed text-stone-600">
                {origin ? source.url : "Preparing links…"}
              </p>
            </div>
          ))}
          <p role="status" className="text-sm text-emerald-800">
            {copied
              ? `${sources.find((s) => s.key === copied)?.label} link copied.`
              : ""}
          </p>
          {copyError && (
            <p role="alert" className="text-sm text-red-800">
              {copyError}
            </p>
          )}
        </div>
        <div className="min-w-0 rounded-xl bg-stone-50 p-4">
          <h3 className="font-semibold">Rehearse the main demo</h3>
          <ol className="mt-3 list-decimal space-y-3 pl-5 text-sm leading-relaxed text-stone-600">
            <li>
              Add both OBS browser sources at{" "}
              <span className="font-medium tabular-nums">1920 × 1080</span>.
              Keep the overlay above the stage.
            </li>
            <li>
              Let the match play. Review the evidence and approve one
              explanation; the overlay stays blank until then.
            </li>
            <li>
              Verify the story in the actual YouTube player, then open this
              session’s companion on the iPhone.
            </li>
          </ol>
          <p className="mt-4 border-t border-stone-200 pt-3 text-xs leading-relaxed text-stone-600">
            {!match
              ? "Waiting for the session’s execution details."
              : match.execution === "ai"
                ? "AI session: check the review trace for actual model execution and any fallback."
                : "Template rehearsal: this session does not demonstrate live AI execution."}{" "}
            App connection does not confirm OBS or YouTube delivery.
          </p>
          <p className="mt-3 text-xs leading-relaxed text-stone-600">
            YouTube may be delayed. The companion follows the app clock, not the
            video playback position.
          </p>
          <div className="mt-5 border-t border-stone-200 pt-4">
            {publicUrl ? (
              <>
                <CompanionQR url={publicUrl} />
                <p className="mt-3 text-xs leading-relaxed text-stone-600">
                  Test this link on the iPhone before recording. It must reach
                  this same session and backend.
                </p>
              </>
            ) : (
              <>
                <h4 className="text-sm font-semibold">
                  Companion QR is not available locally
                </h4>
                <p className="mt-2 text-sm leading-relaxed text-stone-600">
                  Publish this version at a public HTTPS address to show a
                  scannable companion QR here and on the broadcast stage. A
                  localhost link will not open this Mac’s session on the iPhone.
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
