// Server-only runtime proxy. API_URL is never embedded in the browser bundle.
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
const MAX_BODY_BYTES = 64 * 1024;

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const backend = new URL(process.env.API_URL || 'http://127.0.0.1:8000');
  if (!['http:', 'https:'].includes(backend.protocol) || backend.username || backend.password) {
    return Response.json({ detail: { code: 'invalid_backend_configuration' } }, { status: 503 });
  }
  // Reject encoded separators and traversal rather than allowing a path to change the origin.
  if (path.some(segment => !segment || /[/\\]/.test(segment) || segment === '.' || segment === '..')) {
    return Response.json({ detail: { code: 'invalid_path' } }, { status: 400 });
  }
  const target = new URL(`/api/${path.map(encodeURIComponent).join('/')}`, backend);
  target.search = new URL(request.url).search;
  const headers = new Headers({ 'Accept-Encoding': 'identity' });
  for (const name of ['accept', 'content-type', 'x-producer-token', 'last-event-id']) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  let body: Uint8Array<ArrayBuffer> | undefined;
  if (!['GET', 'HEAD'].includes(request.method) && request.body) {
    if (Number(request.headers.get('content-length')) > MAX_BODY_BYTES) {
      return Response.json({ detail: { code: 'request_too_large' } }, { status: 413 });
    }
    const reader = request.body.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BODY_BYTES) {
        await reader.cancel();
        return Response.json({ detail: { code: 'request_too_large' } }, { status: 413 });
      }
      chunks.push(value);
    }
    body = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 90_000);
  const signal = AbortSignal.any([request.signal, controller.signal]);
  try {
    const upstream = await fetch(target, { method: request.method, headers, body, signal, cache: 'no-store', redirect: 'manual' });
    const responseHeaders = new Headers({ 'Cache-Control': 'no-store' });
    for (const name of ['content-type', 'retry-after', 'www-authenticate', 'location']) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    if (upstream.headers.get('content-type')?.includes('text/event-stream')) {
      // Streams intentionally outlive the ordinary request deadline. Cancellation still propagates.
      clearTimeout(timer);
      responseHeaders.set('X-Accel-Buffering', 'no');
      return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
    }
    const responseBody = await upstream.arrayBuffer();
    return new Response(request.method === 'HEAD' || [204, 304].includes(upstream.status) ? null : responseBody, { status: upstream.status, headers: responseHeaders });
  } catch {
    return Response.json({ detail: { code: controller.signal.aborted ? 'backend_timeout' : 'backend_unavailable' } }, { status: controller.signal.aborted ? 504 : 502 });
  } finally { clearTimeout(timer); }
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE, proxy as HEAD, proxy as OPTIONS };
