// src/components/form/PreferencesSection.tsx
import { useFormContext, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { AnalyzeRequest } from "@/types/request";

interface Props {
  riskProfiles?: string[];
  horizons?: string[];
}

const RISK_LABELS: Record<string, string> = {
  low: "Low — capital preservation",
  medium: "Medium — balanced growth",
  high: "High — aggressive growth",
};

const HORIZON_LABELS: Record<string, string> = {
  "1-3": "1–3 years (short)",
  "3-5": "3–5 years (medium)",
  "5-8": "5–8 years (long)",
  "8+": "8+ years (very long)",
};

const FALLBACK_RISKS = ["low", "medium", "high"];
const FALLBACK_HORIZONS = ["1-3", "3-5", "5-8", "8+"];

export function PreferencesSection({ riskProfiles, horizons }: Props) {
  const { control } = useFormContext<AnalyzeRequest>();

  const safeRisks = (riskProfiles && riskProfiles.length > 0) ? riskProfiles : FALLBACK_RISKS;
  const safeHorizons = (horizons && horizons.length > 0) ? horizons : FALLBACK_HORIZONS;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div className="space-y-2">
        <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
          Risk Tolerance
        </label>
        <Controller
          control={control}
          name="user.preferences.risk_profile"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger className="h-11">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {safeRisks.map((r) => (
                  <SelectItem key={r} value={r}>{RISK_LABELS[r] ?? r}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
          Investment Horizon
        </label>
        <Controller
          control={control}
          name="user.preferences.horizon"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger className="h-11">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {safeHorizons.map((h) => (
                  <SelectItem key={h} value={h}>{HORIZON_LABELS[h] ?? h}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>
    </div>
  );
}
