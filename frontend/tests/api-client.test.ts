import { describe, it, expect, vi, afterEach } from "vitest";
import { ApiError, request } from "@/lib/api/client";

const realFetch = global.fetch;


const BASE = "http://localhost:8000";

afterEach(() => {
  global.fetch = realFetch;
});

function mockFetch(impl: typeof fetch) {
  global.fetch = vi.fn(impl) as unknown as typeof fetch;
}

describe("api client", () => {
  it("composes URL with base and query params", async () => {
    let captured = "";
    mockFetch(async (input) => {
      captured = String(input);
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    });
    await request("/api/v1/farms", { query: { limit: 5, offset: 10 } });
    expect(captured).toBe(`${BASE}/api/v1/farms?limit=5&offset=10`);
  });


  it("returns undefined on 204", async () => {
    mockFetch(async () => new Response(null, { status: 204 }));
    const r = await request<void>("/foo", { method: "DELETE" });
    expect(r).toBeUndefined();
  });

  it("parses JSON success", async () => {
    mockFetch(
      async () =>
        new Response(JSON.stringify({ a: 1 }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
    );
    const r = await request<{ a: number }>("/x");
    expect(r.a).toBe(1);
  });

  it("throws ApiError with detail on non-2xx", async () => {
    mockFetch(
      async () =>
        new Response(JSON.stringify({ detail: "duplicate farm" }), {
          status: 409,
          headers: { "content-type": "application/json" },
        }),
    );
    await expect(request("/x", { method: "POST", body: {} })).rejects.toThrow(
      ApiError,
    );
    try {
      await request("/x", { method: "POST", body: {} });
    } catch (e) {
      const err = e as ApiError;
      expect(err.status).toBe(409);
      expect(err.detail).toBe("duplicate farm");
    }
  });

  it("does not set Content-Type for multipart uploads", async () => {
    let capturedHeaders: HeadersInit | undefined;
    mockFetch(async (_input, init) => {
      capturedHeaders = init?.headers;
      return new Response(JSON.stringify({}), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    });
    const fd = new FormData();
    fd.append("image", new Blob(["x"], { type: "image/png" }), "x.png");
    await request("/upload", { method: "POST", formData: fd });
    const h = capturedHeaders as Record<string, string>;
    expect(h["Content-Type"]).toBeUndefined();
  });

  it("flattens FastAPI validation error array into detail", async () => {
    mockFetch(
      async () =>
        new Response(
          JSON.stringify({
            detail: [
              { loc: ["body", "latitude"], msg: "must be <= 90", type: "x" },
            ],
          }),
          {
            status: 422,
            headers: { "content-type": "application/json" },
          },
        ),
    );
    try {
      await request("/x", { method: "POST", body: {} });
    } catch (e) {
      const err = e as ApiError;
      expect(err.status).toBe(422);
      expect(err.detail).toContain("body.latitude");
      expect(err.detail).toContain("must be <= 90");
    }
  });
});
