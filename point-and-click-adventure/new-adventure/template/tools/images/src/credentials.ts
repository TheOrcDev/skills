// Which gateway credential is available. The AI SDK uses AI_GATEWAY_API_KEY when
// it has a value and otherwise falls back to VERCEL_OIDC_TOKEN.

export type Credential =
  | { kind: "api-key" }
  | { kind: "oidc"; expiresAt: Date | null }
  | { kind: "none" };

/** Reads the expiry from a JWT's payload without validating it or exposing the token. */
function jwtExpiry(token: string): Date | null {
  try {
    const payload = JSON.parse(Buffer.from(token.split(".")[1], "base64url").toString("utf8")) as { exp?: number };
    return typeof payload.exp === "number" ? new Date(payload.exp * 1000) : null;
  } catch {
    return null;
  }
}

export function currentCredential(env: Record<string, string | undefined> = process.env): Credential {
  if (env.AI_GATEWAY_API_KEY) return { kind: "api-key" };
  if (env.VERCEL_OIDC_TOKEN) return { kind: "oidc", expiresAt: jwtExpiry(env.VERCEL_OIDC_TOKEN) };
  return { kind: "none" };
}

export function describeCredential(credential: Credential, now = new Date()): string {
  switch (credential.kind) {
    case "api-key":
      return "AI_GATEWAY_API_KEY: set";
    case "oidc": {
      if (!credential.expiresAt) return "VERCEL_OIDC_TOKEN: set (expiry unknown)";
      const minutes = Math.round((credential.expiresAt.getTime() - now.getTime()) / 60_000);
      return minutes > 0
        ? `VERCEL_OIDC_TOKEN: set, expires ${credential.expiresAt.toISOString()} (in ${minutes} min)`
        : `VERCEL_OIDC_TOKEN: EXPIRED at ${credential.expiresAt.toISOString()}; pull a fresh one`;
    }
    case "none":
      return "no gateway credential: put AI_GATEWAY_API_KEY (or a VERCEL_OIDC_TOKEN) in .env and run from the repository root";
  }
}

export function credentialUsable(credential: Credential, now = new Date()): boolean {
  if (credential.kind === "none") return false;
  if (credential.kind === "oidc" && credential.expiresAt) return credential.expiresAt.getTime() > now.getTime();
  return true;
}
