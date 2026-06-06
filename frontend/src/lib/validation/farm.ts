import { z } from "zod";
import { CROP_TYPES } from "@/lib/api/types";

export const farmSchema = z.object({
  farmer_name: z
    .string()
    .trim()
    .min(1, "Farmer name is required")
    .max(255, "Farmer name must be 255 characters or fewer"),
  county: z
    .string()
    .trim()
    .min(1, "County is required")
    .max(100, "County must be 100 characters or fewer"),
  crop_type: z.enum(CROP_TYPES as [string, ...string[]], {
    message: "Choose a crop type",
  }),
  latitude: z
    .number({ message: "Latitude is required" })
    .min(-90, "Latitude must be between -90 and 90")
    .max(90, "Latitude must be between -90 and 90"),
  longitude: z
    .number({ message: "Longitude is required" })
    .min(-180, "Longitude must be between -180 and 180")
    .max(180, "Longitude must be between -180 and 180"),
  farm_size_acres: z
    .number()
    .min(0, "Farm size must be 0 or greater")
    .nullable()
    .optional(),
});

export type FarmFormValues = z.infer<typeof farmSchema>;
