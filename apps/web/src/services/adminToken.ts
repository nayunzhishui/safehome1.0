let memoryAdminToken = "";

function legacyAdminTokenEnabled(): boolean {
  return String(import.meta.env.VITE_ENABLE_LEGACY_ADMIN_TOKEN || "").toLowerCase() === "true";
}

export function getStoredAdminToken(): string {
  return legacyAdminTokenEnabled() ? memoryAdminToken : "";
}

export function setStoredAdminToken(token: string): void {
  memoryAdminToken = legacyAdminTokenEnabled() ? token : "";
}

export function isLegacyAdminTokenEnabled(): boolean {
  return legacyAdminTokenEnabled();
}
