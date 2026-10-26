"use client";

import { QRCodeSVG } from "qrcode.react";

export function CompanionQR({
  url,
  compact = false,
}: {
  url: string;
  compact?: boolean;
}) {
  return (
    <div
      className={
        compact ? "flex items-center gap-3" : "flex flex-col items-start gap-3"
      }
      data-testid="companion-qr"
    >
      <div className="shrink-0 rounded-lg bg-white p-1">
        <QRCodeSVG
          value={url}
          size={compact ? 176 : 164}
          level="M"
          marginSize={4}
          title="Open this session’s viewer companion"
        />
      </div>
      <div className="min-w-0">
        <p className="font-semibold">Explore this moment</p>
        <p className="mt-1 text-xs leading-relaxed">
          Scan to choose your language, detail and player focus.
        </p>
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="mt-2 block max-w-xs break-all text-xs underline underline-offset-4"
        >
          {url}
        </a>
      </div>
    </div>
  );
}
