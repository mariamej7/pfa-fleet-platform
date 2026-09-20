const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

const UUID_PATTERN =
  /^(?:[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/i;

type ImportRouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

type StreamingRequestInit = RequestInit & {
  duplex?: "half";
};

export const runtime = "nodejs";
export const maxDuration = 300;


function isAllowedPath(path: string[]) {
  if (
    path.length === 1 &&
    path[0] === "upload"
  ) {
    return true;
  }

  return (
    path.length === 2 &&
    UUID_PATTERN.test(path[0]) &&
    (path[1] === "validate" ||
      path[1] === "analyze")
  );
}


function isSameOrigin(request: Request) {
  const requestUrl = new URL(request.url);
  const origin = request.headers.get("origin");
  const fetchSite = request.headers.get("sec-fetch-site");

  if (origin && origin !== requestUrl.origin) {
    return false;
  }

  return !fetchSite || fetchSite === "same-origin";
}


function errorResponse(
  detail: string,
  status: number
) {
  return Response.json(
    { detail },
    {
      status,
      headers: {
        "Cache-Control": "no-store",
      },
    }
  );
}


export async function POST(
  request: Request,
  context: ImportRouteContext
) {
  if (!isSameOrigin(request)) {
    return errorResponse(
      "Origine de la requête refusée.",
      403
    );
  }

  const { path } = await context.params;

  if (!isAllowedPath(path)) {
    return errorResponse(
      "Route d'import inconnue.",
      404
    );
  }

  const importApiKey =
    process.env.IMPORT_API_KEY;

  if (!importApiKey) {
    return errorResponse(
      "L'import est temporairement indisponible.",
      503
    );
  }

  const backendUrl = (
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    DEFAULT_BACKEND_URL
  ).replace(/\/$/, "");

  const upstreamUrl = new URL(
    `${backendUrl}/api/imports/${path
      .map(encodeURIComponent)
      .join("/")}`
  );

  upstreamUrl.search =
    new URL(request.url).search;

  const headers = new Headers({
    "X-Import-Key": importApiKey,
  });

  const contentType =
    request.headers.get("content-type");

  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  const requestInit: StreamingRequestInit = {
    method: "POST",
    headers,
    cache: "no-store",
  };

  if (request.body) {
    requestInit.body = request.body;
    requestInit.duplex = "half";
  }

  try {
    const upstreamResponse = await fetch(
      upstreamUrl,
      requestInit
    );

    const responseHeaders = new Headers({
      "Cache-Control": "no-store",
    });

    const responseContentType =
      upstreamResponse.headers.get("content-type");

    const retryAfter =
      upstreamResponse.headers.get("retry-after");

    if (responseContentType) {
      responseHeaders.set(
        "Content-Type",
        responseContentType
      );
    }

    if (retryAfter) {
      responseHeaders.set(
        "Retry-After",
        retryAfter
      );
    }

    return new Response(
      upstreamResponse.body,
      {
        status: upstreamResponse.status,
        headers: responseHeaders,
      }
    );

  } catch {
    return errorResponse(
      "Le service d'analyse ne répond pas encore. Réessayez dans un instant.",
      502
    );
  }
}
