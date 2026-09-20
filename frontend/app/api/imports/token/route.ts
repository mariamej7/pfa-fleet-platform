import {
  createHmac,
  randomBytes,
} from "node:crypto";


const TOKEN_TTL_SECONDS = 900;

export const runtime = "nodejs";
export const dynamic = "force-dynamic";


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


function isSameOrigin(request: Request) {
  const requestUrl = new URL(request.url);
  const origin = request.headers.get("origin");
  const fetchSite = request.headers.get("sec-fetch-site");

  if (!origin || origin !== requestUrl.origin) {
    return false;
  }

  return !fetchSite || fetchSite === "same-origin";
}


export async function POST(
  request: Request
) {
  if (!isSameOrigin(request)) {
    return errorResponse(
      "Origine de la requête refusée.",
      403
    );
  }

  const importApiKey =
    process.env.IMPORT_API_KEY?.trim();

  if (!importApiKey) {
    return errorResponse(
      "L'import est temporairement indisponible.",
      503
    );
  }

  const issuedAt = Math.floor(
    Date.now() / 1000
  ).toString();

  const nonce = randomBytes(16)
    .toString("hex");

  const payload = `${issuedAt}.${nonce}`;

  const signature = createHmac(
    "sha256",
    importApiKey
  )
    .update(payload)
    .digest("hex");

  return Response.json(
    {
      token: `${payload}.${signature}`,
      expires_in: TOKEN_TTL_SECONDS,
    },
    {
      headers: {
        "Cache-Control": "no-store",
      },
    }
  );
}
