import { Link } from "@tanstack/react-router";
import { MapPin, Sprout } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { Farm } from "@/lib/api/types";

export function FarmCard({ farm }: { farm: Farm }) {
  return (
    <Link
      to="/farms/$farmId"
      params={{ farmId: farm.id }}
      className="block group"
    >
      <Card className="hover:border-primary/50 transition-colors h-full">
        <CardContent className="p-4 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-medium truncate group-hover:text-primary">
              {farm.farmer_name}
            </h3>
            <span className="text-xs uppercase tracking-wide rounded bg-secondary text-secondary-foreground px-1.5 py-0.5">
              {farm.crop_type}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <MapPin className="h-3.5 w-3.5" />
            <span className="truncate">{farm.county}</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground tabular-nums">
            <Sprout className="h-3.5 w-3.5" />
            <span>
              {farm.latitude.toFixed(4)}, {farm.longitude.toFixed(4)}
              {farm.farm_size_acres != null
                ? ` · ${farm.farm_size_acres} ac`
                : ""}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
