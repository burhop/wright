export function isDesktop(): boolean {
  return typeof window !== "undefined" && typeof window.wrightDesktop !== "undefined";
}

export function detectEnvironment(): 'browser' | 'desktop' {
  return isDesktop() ? 'desktop' : 'browser';
}
