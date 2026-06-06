export class ApiError extends Error {
  status: number;
  detail: string;
  body: unknown;
  constructor(status: number, detail: string, body: unknown) {
    super(detail || `HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.body = body;
  }
}

export function getApiBaseUrl(): string {
  // Vercel exposes runtime env via process.env on the server, while Vite
  // exposes build-time public env via import.meta.env in the browser bundle.
  const viteEnv =
    (import.meta as unknown as { env?: Record<string, string | undefined> })
      .env ?? {};
  const processEnv = (globalThis as unknown as {
    process?: { env?: Record<string, string | undefined> };
  }).process?.env;
  const raw =
    typeof window === "undefined"
      ? (processEnv?.API_INTERNAL_BASE_URL ??
          processEnv?.VITE_API_BASE_URL ??
          viteEnv.VITE_API_BASE_URL ??
          "http://localhost:8000")
      : (viteEnv.VITE_API_BASE_URL ?? "http://localhost:8000");
  return raw.replace(/\/+$/, "");
}

function extractDetail(body: unknown, status: number): string {
  if (body && typeof body === "object") {
    const b = body as Record<string, unknown>;
    if (typeof b.detail === "string") return b.detail;
    if (Array.isArray(b.detail)) {
      // FastAPI validation error shape
      const msgs = b.detail
        .map((d) => {
          if (d && typeof d === "object" && "msg" in d) {
            const loc = Array.isArray((d as { loc?: unknown[] }).loc)
              ? (d as { loc: unknown[] }).loc.join(".")
              : "";
            return loc
              ? `${loc}: ${(d as { msg: string }).msg}`
              : (d as { msg: string }).msg;
          }
          return null;
        })
        .filter(Boolean);
      if (msgs.length) return msgs.join("; ");
    }
    if (typeof b.message === "string") return b.message;
  }
  return `HTTP ${status}`;
}

export type RequestOptions = {
  method?: string;
  query?: Record<string, string | number | boolean | undefined | null>;
  body?: unknown;
  formData?: FormData;
  signal?: AbortSignal;
};

export async function request<T>(
  path: string,
  opts: RequestOptions = {},
): Promise<T> {
  const base = getApiBaseUrl();
  const finalUrl = new URL(base + (path.startsWith("/") ? path : `/${path}`));
  if (opts.query) {
    for (const [k, v] of Object.entries(opts.query)) {
      if (v === undefined || v === null) continue;
      finalUrl.searchParams.set(k, String(v));
    }
  }


  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;
  if (opts.formData) {
    body = opts.formData;
    // Do NOT set Content-Type; browser sets multipart boundary.
  } else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  headers["Accept"] = "application/json";

  let res: Response;
  try {
    res = await fetch(finalUrl.toString(), {
      method: opts.method ?? "GET",
      headers,
      body,
      signal: opts.signal,
    });
  } catch (err) {
    throw new ApiError(
      0,
      err instanceof Error ? err.message : "Network error",
      null,
    );
  }

  if (res.status === 204) return undefined as T;

  const contentType = res.headers.get("content-type") ?? "";
  let parsed: unknown = null;
  if (contentType.includes("application/json")) {
    try {
      parsed = await res.json();
    } catch {
      parsed = null;
    }
  } else {
    const text = await res.text();
    parsed = text || null;
  }

  if (!res.ok) {
    throw new ApiError(res.status, extractDetail(parsed, res.status), parsed);
  }
  return parsed as T;
}
