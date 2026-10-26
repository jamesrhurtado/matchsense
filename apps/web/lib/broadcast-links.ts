/** A QR is for a public HTTPS deployment of this same app/session, never a local address. */
export function publicOrigin(value: string): string | null {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase().replace(/\.$/, "");
    if (
      url.protocol !== "https:" ||
      url.username ||
      url.password ||
      url.search ||
      url.hash ||
      url.pathname !== "/"
    )
      return null;
    if (
      !host.includes(".") ||
      host.includes(":") ||
      host.endsWith(".localhost") ||
      host.endsWith(".local") ||
      host.endsWith(".lan") ||
      host.endsWith(".home.arpa") ||
      host.endsWith(".internal") ||
      host.endsWith(".test") ||
      host.endsWith(".invalid")
    )
      return null;
    // Conservatively exclude IP literals, including private, loopback and reserved ranges.
    if (/^[\d.]+$/.test(host)) return null;
    return url.origin;
  } catch {
    return null;
  }
}

export function companionUrl(
  configured: string,
  currentOrigin: string,
  sessionId: string,
) {
  const origin = publicOrigin(configured || currentOrigin);
  return origin ? `${origin}/watch/${encodeURIComponent(sessionId)}` : null;
}
