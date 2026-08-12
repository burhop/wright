import type { StreamActivityEntry } from "../store/types";

export function isBrepToolActivity(
  activity: Pick<StreamActivityEntry, "server" | "tool" | "title">,
): boolean {
  return [activity.server, activity.tool, activity.title].some(
    (value) =>
      typeof value === "string" && value.toLowerCase().includes("brep"),
  );
}
