let memoryAdminToken = "";

export function getStoredAdminToken(): string {
  return memoryAdminToken;
}

export function setStoredAdminToken(token: string): void {
  memoryAdminToken = token;
}
