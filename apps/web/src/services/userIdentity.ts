const STORAGE_KEY = "safehome_anonymous_user_id";

function generateAnonymousUserId(): string {
  const randomPart = Math.random().toString(16).slice(2, 8);
  return `web_user_${Date.now()}_${randomPart}`;
}

export function getAnonymousUserId(): string {
  if (typeof window === "undefined" || !window.localStorage) {
    return generateAnonymousUserId();
  }

  const existing = window.localStorage.getItem(STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const generated = generateAnonymousUserId();
  window.localStorage.setItem(STORAGE_KEY, generated);
  return generated;
}

export { STORAGE_KEY as ANONYMOUS_USER_STORAGE_KEY };
