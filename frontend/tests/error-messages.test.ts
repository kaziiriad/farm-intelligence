import { describe, it, expect } from "vitest";
import { ApiError } from "@/lib/api/client";
import { apiErrorToMessage } from "@/lib/api/error-messages";

describe("apiErrorToMessage", () => {
  it("maps 404 farm", () => {
    expect(apiErrorToMessage(new ApiError(404, "HTTP 404", null), "farm")).toBe(
      "Farm not found.",
    );
  });
  it("maps 409 with backend detail", () => {
    expect(
      apiErrorToMessage(
        new ApiError(409, "duplicate farm", null),
        "farmForm",
      ),
    ).toBe("duplicate farm");
  });
  it("maps 413 default", () => {
    expect(
      apiErrorToMessage(new ApiError(413, "HTTP 413", null), "treeUpload"),
    ).toMatch(/too large/i);
  });
  it("maps 429", () => {
    expect(
      apiErrorToMessage(new ApiError(429, "HTTP 429", null), "treeUpload"),
    ).toMatch(/quota/i);
  });
  it("maps 502 advisory", () => {
    expect(
      apiErrorToMessage(new ApiError(502, "HTTP 502", null), "advisory"),
    ).toMatch(/WeatherAI/i);
  });
  it("maps 422 operation as invalid operation", () => {
    expect(
      apiErrorToMessage(new ApiError(422, "HTTP 422", null), "operation"),
    ).toBe("Invalid operation.");
  });
});
