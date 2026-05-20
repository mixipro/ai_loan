// src/components/form/LocationSection.tsx
import { useFormContext, useWatch, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import type { AnalyzeRequest } from "@/types/request";
import type { RegionOption } from "@/types/options";

interface Props {
  regions?: RegionOption[];
  citiesByRegion?: Record<string, string[]>;
}

const FALLBACK_REGIONS: RegionOption[] = [
  { value: "BAY_AREA", label: "Bay Area", description: "", primary_industries: [] },
  { value: "LOS_ANGELES", label: "Los Angeles", description: "", primary_industries: [] },
  { value: "SAN_DIEGO", label: "San Diego", description: "", primary_industries: [] },
];

export function LocationSection({ regions, citiesByRegion }: Props) {
  const { control, setValue } = useFormContext<AnalyzeRequest>();
  const selectedRegion = useWatch({ control, name: "user.location.region" });

  const safeRegions = (regions && regions.length > 0) ? regions : FALLBACK_REGIONS;
  const safeCitiesByRegion = citiesByRegion ?? {};
  const cities = safeCitiesByRegion[selectedRegion] ?? [];

  const regionLabel = safeRegions.find((r) => r.value === selectedRegion)?.label ?? selectedRegion;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div className="space-y-2">
        <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
          Region
        </label>
        <Controller
          control={control}
          name="user.location.region"
          render={({ field }) => (
            <Select
              value={field.value}
              onValueChange={(v) => {
                field.onChange(v);
                const firstCity = safeCitiesByRegion[v]?.[0] ?? "";
                setValue("user.location.city", firstCity);
              }}
            >
              <SelectTrigger className="h-11">
                <SelectValue placeholder="Select a region" />
              </SelectTrigger>
              <SelectContent>
                {safeRegions.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
          City
        </label>
        <Controller
          control={control}
          name="user.location.city"
          render={({ field }) => (
            cities.length > 0 ? (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger className="h-11">
                  <SelectValue placeholder="Select a city" />
                </SelectTrigger>
                <SelectContent className="max-h-72">
                  {cities.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input className="h-11" placeholder="Enter city name" {...field} />
            )
          )}
        />
        {cities.length > 0 && (
          <p className="text-xs text-muted-foreground tabular-nums">
            {cities.length} cities in {regionLabel}
          </p>
        )}
      </div>
    </div>
  );
}
