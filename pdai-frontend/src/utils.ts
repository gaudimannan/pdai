export function parsePercent(value: string | number): number {
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  const parsed = Number.parseFloat(value.replace("%", ""));
  return Number.isFinite(parsed) ? Math.max(0, Math.min(parsed, 100)) : 0;
}

export function splitIssue(issue: string) {
  const parts = issue.split(" - ");
  return {
    plant: parts[0] || "UNKNOWN",
    condition: parts.length > 1 ? parts.slice(1).join(" - ") : issue
  };
}
