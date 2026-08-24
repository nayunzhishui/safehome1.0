/** Auth state helpers for the SafeHome Web client.
 *
 * Bearer tokens are session-scoped instead of persistent localStorage values.
 * This does not make a browser token immune to XSS; CSP and server-side RBAC
 * remain mandatory. It does reduce persistence after the browser session ends.
 */

const AUTH_TOKEN_KEY = "safehome_auth_token";
const AUTH_USER_KEY = "safehome_auth_user";
const PENDING_LOGOUT_KEY = "safehome_pending_logout";
const PENDING_LOGOUT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

export interface AuthUser {
  id: string;
  username?: string;
  role: string;
  nickname?: string;
  anonymous_id?: string;
  status?: string;
  must_change_password?: boolean;
  auth_epoch?: number;
}

export interface PendingLogout {
  user_id: string;
  auth_epoch: number | null;
  requested_at: string;
}

function migrateLegacyLocalStorage(): void {
  if (typeof window === "undefined") return;
  const legacyToken = window.localStorage.getItem(AUTH_TOKEN_KEY);
  const legacyUser = window.localStorage.getItem(AUTH_USER_KEY);
  if (!window.sessionStorage.getItem(AUTH_TOKEN_KEY) && legacyToken) {
    window.sessionStorage.setItem(AUTH_TOKEN_KEY, legacyToken);
  }
  if (!window.sessionStorage.getItem(AUTH_USER_KEY) && legacyUser) {
    window.sessionStorage.setItem(AUTH_USER_KEY, legacyUser);
  }
  // Remove long-lived copies even when migration parsing later fails.
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USER_KEY);
}

export function getStoredAuthToken(): string {
  if (typeof window === "undefined") return "";
  migrateLegacyLocalStorage();
  return window.sessionStorage.getItem(AUTH_TOKEN_KEY) || "";
}

export function getToken(): string {
  return getStoredAuthToken();
}

export function getStoredAuthUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  migrateLegacyLocalStorage();
  try {
    const raw = window.sessionStorage.getItem(AUTH_USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    clearAuthSession();
    return null;
  }
}

export function getUser(): AuthUser | null {
  return getStoredAuthUser();
}

export function saveAuthSession(token: string, user: AuthUser): void {
  if (typeof window === "undefined") return;
  migrateLegacyLocalStorage();
  window.sessionStorage.setItem(AUTH_TOKEN_KEY, token);
  window.sessionStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function login(token: string, user: AuthUser): void {
  saveAuthSession(token, user);
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(AUTH_TOKEN_KEY);
  window.sessionStorage.removeItem(AUTH_USER_KEY);
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USER_KEY);
  window.localStorage.removeItem("safehome_anonymous_user_id");
  window.localStorage.removeItem("safehome_dismissed_data_claim_id");
  window.localStorage.removeItem("safehome:selectedTrainingCard");
  window.localStorage.removeItem("safehome:latestTrainingRecommendation");
  window.localStorage.removeItem("safehome:threeDayLightPlan");
}

export function getPendingLogout(): PendingLogout | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(PENDING_LOGOUT_KEY);
    const parsed = raw ? (JSON.parse(raw) as PendingLogout) : null;
    const requestedAt = parsed ? Date.parse(parsed.requested_at) : Number.NaN;
    if (!parsed?.user_id || !Number.isFinite(requestedAt) || Date.now() - requestedAt > PENDING_LOGOUT_MAX_AGE_MS) {
      window.localStorage.removeItem(PENDING_LOGOUT_KEY);
      return null;
    }
    return parsed;
  } catch {
    window.localStorage.removeItem(PENDING_LOGOUT_KEY);
    return null;
  }
}

export function markPendingLogout(user: AuthUser): void {
  if (typeof window === "undefined" || !user.id) return;
  const marker: PendingLogout = {
    user_id: user.id,
    auth_epoch: Number.isInteger(user.auth_epoch) ? Number(user.auth_epoch) : null,
    requested_at: new Date().toISOString(),
  };
  window.localStorage.setItem(PENDING_LOGOUT_KEY, JSON.stringify(marker));
}

export function clearPendingLogout(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(PENDING_LOGOUT_KEY);
}

export function clearPendingLogoutForUser(userId: string): void {
  const pending = getPendingLogout();
  if (!pending || pending.user_id === userId) {
    clearPendingLogout();
  }
}

export function logout(): void {
  clearAuthSession();
}

export function isLoggedIn(): boolean {
  return !!getStoredAuthToken();
}
