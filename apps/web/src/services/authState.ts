/** Minimal auth state helpers for the SafeHome Web client. */

const AUTH_TOKEN_KEY = "safehome_auth_token";
const AUTH_USER_KEY = "safehome_auth_user";

export interface AuthUser {
  id: string;
  username?: string;
  role: string;
  nickname?: string;
  anonymous_id?: string;
  status?: string;
}

export function getStoredAuthToken(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(AUTH_TOKEN_KEY) || "";
}

export function getToken(): string {
  return getStoredAuthToken();
}

export function getStoredAuthUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(AUTH_USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function getUser(): AuthUser | null {
  return getStoredAuthUser();
}

export function saveAuthSession(token: string, user: AuthUser): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function login(token: string, user: AuthUser): void {
  saveAuthSession(token, user);
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USER_KEY);
}

export function logout(): void {
  clearAuthSession();
}

export function isLoggedIn(): boolean {
  return !!getStoredAuthToken();
}
