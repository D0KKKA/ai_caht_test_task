const CLIENT_ID_KEY = "client_id";
const CLIENT_ID_COOKIE_MAX_AGE = 60 * 60 * 24 * 365;

export function getOrCreateClientId(): string {
  if (typeof window === "undefined") {
    return "";
  }

  let clientId = localStorage.getItem(CLIENT_ID_KEY) || readClientIdFromCookie();

  if (!clientId) {
    clientId = crypto.randomUUID();
  }

  persistClientId(clientId);
  return clientId;
}

export function getClientId(): string {
  if (typeof window === "undefined") {
    return "";
  }

  const clientId = localStorage.getItem(CLIENT_ID_KEY) || readClientIdFromCookie();

  if (clientId) {
    persistClientId(clientId);
  }

  return clientId || "";
}

export function clearClientId(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(CLIENT_ID_KEY);
    document.cookie = `${CLIENT_ID_KEY}=; Max-Age=0; Path=/; SameSite=Lax`;
  }
}

function persistClientId(clientId: string): void {
  localStorage.setItem(CLIENT_ID_KEY, clientId);
  document.cookie =
    `${CLIENT_ID_KEY}=${encodeURIComponent(clientId)}; ` +
    `Max-Age=${CLIENT_ID_COOKIE_MAX_AGE}; Path=/; SameSite=Lax`;
}

function readClientIdFromCookie(): string {
  const cookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${CLIENT_ID_KEY}=`));

  if (!cookie) {
    return "";
  }

  const [, value = ""] = cookie.split("=");
  return decodeURIComponent(value);
}
