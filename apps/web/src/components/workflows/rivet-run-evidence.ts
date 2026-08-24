export function displayEvidenceState(value: string | null | undefined): string {
  const normalized = value?.trim();
  return normalized ? normalized.replaceAll("-", " ") : "unavailable";
}
