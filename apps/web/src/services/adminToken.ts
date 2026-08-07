let memoryAdminToken = "";

/**
 * Legacy static admin tokens are a development-only compatibility path.
 * Production Web authorization is Bearer-session based.
 */
export function isLegacyAdminTokenAvailable(): boolean {
  return Boolean(import.meta.env.DEV || import.meta.env.MODE === "test");
}

export function getStoredAdminToken(): string {
  return isLegacyAdminTokenAvailable() ? memoryAdminToken : "";
}

export function setStoredAdminToken(token: string): void {
  if (!isLegacyAdminTokenAvailable()) {
    memoryAdminToken = "";
    throw new Error("生产环境已停用后台静态令牌，请使用正式后台账号登录。");
  }
  memoryAdminToken = token.trim();
}

export function clearStoredAdminToken(): void {
  memoryAdminToken = "";
}
