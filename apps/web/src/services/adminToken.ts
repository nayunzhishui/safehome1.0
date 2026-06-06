const ADMIN_TOKEN_KEY = "safehome_admin_token";
const LOCAL_API_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);

function shouldUseLocalDefaultAdminToken(): boolean {
  if (!import.meta.env.DEV) {
    return false;
  }
  const configuredBaseUrl = import.meta.env.VITE_SAFEHOME_API_BASE_URL;
  if (!configuredBaseUrl) {
    return true;
  }
  try {
    const host = new URL(configuredBaseUrl).hostname;
    return LOCAL_API_HOSTS.has(host);
  } catch {
    return false;
  }
}

export function getStoredAdminToken(): string {
  if (typeof window === "undefined") {
    return "";
  }
  const stored = window.localStorage.getItem(ADMIN_TOKEN_KEY) || "";
  if (stored) {
    return stored;
  }
  return shouldUseLocalDefaultAdminToken() ? "safehome-local-admin-token" : "";
}

export function setStoredAdminToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(ADMIN_TOKEN_KEY, token);
}
