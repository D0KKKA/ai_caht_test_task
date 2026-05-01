import { cookies } from "next/headers";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const DEFAULT_BACKEND_ORIGIN = "http://localhost:8000";

export async function GET(request: Request) {
  return proxyRequest(request);
}

export async function POST(request: Request) {
  return proxyRequest(request);
}

export async function DELETE(request: Request) {
  return proxyRequest(request);
}

export async function OPTIONS(request: Request) {
  return proxyRequest(request);
}

async function proxyRequest(request: Request): Promise<Response> {
  const headers = new Headers(request.headers);
  const cookieStore = await cookies();
  const clientId = cookieStore.get("client_id")?.value;

  if (!headers.get("x-client-id") && clientId) {
    headers.set("x-client-id", clientId);
  }

  headers.delete("host");
  headers.delete("connection");
  headers.delete("content-length");

  const upstreamResponse = await fetch(getTargetUrl(request.url), {
    method: request.method,
    headers,
    body: canHaveBody(request.method) ? await request.text() : undefined,
    cache: "no-store",
    redirect: "manual",
  });

  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}

function getTargetUrl(requestUrl: string): string {
  const { pathname, search } = new URL(requestUrl);
  return `${getBackendOrigin()}${pathname}${search}`;
}

function getBackendOrigin(): string {
  if (process.env.BACKEND_URL) {
    return normalizeBackendOrigin(process.env.BACKEND_URL);
  }

  if (process.env.NEXT_PUBLIC_API_URL) {
    return normalizeBackendOrigin(process.env.NEXT_PUBLIC_API_URL);
  }

  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}/_backend`;
  }

  return DEFAULT_BACKEND_ORIGIN;
}

function normalizeBackendOrigin(value: string): string {
  return value.replace(/\/+$/, "").replace(/\/api\/v1$/, "");
}

function canHaveBody(method: string): boolean {
  return method !== "GET" && method !== "HEAD";
}
