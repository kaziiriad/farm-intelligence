import { ApiError } from "./client";

export type ErrorContext =
  | "farm"
  | "farmList"
  | "farmForm"
  | "advisory"
  | "operation"
  | "treeUpload"
  | "quota"
  | "usage"
  | "generic";

export function apiErrorToMessage(err: unknown, ctx: ErrorContext): string {
  if (!(err instanceof ApiError)) {
    return err instanceof Error ? err.message : "Something went wrong.";
  }
  const detail = err.detail && err.detail !== `HTTP ${err.status}` ? err.detail : "";
  switch (err.status) {
    case 0:
      return `Cannot reach the API. ${detail}`.trim();
    case 404:
      if (ctx === "farm" || ctx === "advisory" || ctx === "operation")
        return "Farm not found.";
      return detail || "Not found.";
    case 409:
      return (
        detail ||
        "A farm with the same name and coordinates already exists."
      );
    case 413:
      return detail || "Image is too large. Maximum is 20 MB.";
    case 422:
      if (ctx === "operation") return detail || "Invalid operation.";
      return detail || "Validation failed.";
    case 429:
      return detail || "Monthly tree analysis quota exceeded.";
    case 502:
      if (ctx === "usage")
        return detail || "WeatherAI usage could not be loaded.";
      return detail || "WeatherAI upstream failed. Please retry.";
    default:
      return detail || `Request failed (${err.status}).`;
  }
}
