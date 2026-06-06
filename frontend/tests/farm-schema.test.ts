import { describe, it, expect } from "vitest";
import { farmSchema } from "@/lib/validation/farm";

describe("farm schema", () => {
  const valid = {
    farmer_name: "Jane",
    county: "Kiambu",
    crop_type: "tea",
    latitude: -1.23,
    longitude: 36.7,
    farm_size_acres: 2,
  };

  it("accepts valid payload", () => {
    expect(farmSchema.safeParse(valid).success).toBe(true);
  });

  it("rejects out-of-range latitude", () => {
    const r = farmSchema.safeParse({ ...valid, latitude: 100 });
    expect(r.success).toBe(false);
  });

  it("rejects out-of-range longitude", () => {
    const r = farmSchema.safeParse({ ...valid, longitude: -200 });
    expect(r.success).toBe(false);
  });

  it("rejects invalid crop", () => {
    const r = farmSchema.safeParse({ ...valid, crop_type: "rice" });
    expect(r.success).toBe(false);
  });

  it("rejects negative farm size", () => {
    const r = farmSchema.safeParse({ ...valid, farm_size_acres: -1 });
    expect(r.success).toBe(false);
  });

  it("accepts missing farm size", () => {
    const { farm_size_acres: _, ...rest } = valid;
    void _;
    expect(farmSchema.safeParse(rest).success).toBe(true);
  });

  it("rejects empty farmer name", () => {
    expect(
      farmSchema.safeParse({ ...valid, farmer_name: "  " }).success,
    ).toBe(false);
  });
});
