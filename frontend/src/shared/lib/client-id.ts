/**
 * Client ID management for anonymous users
 */

const CLIENT_ID_KEY = "client_id";

/**
 * Get or generate client ID (UUID v4)
 * Persists in localStorage
 */
export function getOrCreateClientId(): string {
  // Check if running in browser
  if (typeof window === "undefined") {
    return "";
  }

  // Try to get from localStorage
  let clientId = localStorage.getItem(CLIENT_ID_KEY);

  // Generate new if doesn't exist
  if (!clientId) {
    clientId = crypto.randomUUID();
    localStorage.setItem(CLIENT_ID_KEY, clientId);
  }

  return clientId;
}

/**
 * Get client ID from localStorage (returns empty string if not in browser)
 */
export function getClientId(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return localStorage.getItem(CLIENT_ID_KEY) || "";
}

/**
 * Clear client ID (for testing/logout)
 */
export function clearClientId(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(CLIENT_ID_KEY);
  }
}
