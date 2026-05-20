// src/components/form/ProfessionalSection.tsx
import { useFormContext, useWatch, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Check, Sparkle } from "@phosphor-icons/react";
import type { AnalyzeRequest } from "@/types/request";

interface Props {
  sectors?: string[];
  professionsBySector?: Record<string, string[]>;
  interests?: string[];
  employmentStatuses?: string[];
  weeklyHours?: string[];
  techRoles?: string[];
  equityCompensations?: string[];
  companyStages?: string[];
  entertainmentRoles?: string[];
}

const HOURS_LABELS: Record<string, string> = {
  "0-5": "0–5 hours (passive)",
  "5-15": "5–15 hours (light)",
  "15-30": "15–30 hours (moderate)",
  "30+": "30+ hours (full-time)",
};

const FALLBACK_INTERESTS = [
  "fitness", "running", "cooking", "programming",
  "technology", "investing", "real estate", "travel",
  "reading", "music",
];
const FALLBACK_SECTORS = ["Technology", "Healthcare", "Finance", "Other"];
const FALLBACK_EMPLOYMENT = [
  "full-time", "part-time", "freelancer", "self-employed",
  "unemployed", "student", "retired",
];
const FALLBACK_HOURS = ["0-5", "5-15", "15-30", "30+"];

export function ProfessionalSection({
  sectors,
  professionsBySector,
  interests,
  employmentStatuses,
  weeklyHours,
  techRoles,
  equityCompensations,
  companyStages,
  entertainmentRoles,
}: Props) {
  const { register, control, setValue } = useFormContext<AnalyzeRequest>();
  const selectedSector = useWatch({ control, name: "user.professional.sector" });
  const currentInterests = useWatch({ control, name: "user.professional.interests" }) ?? [];

  const safeSectors = (sectors && sectors.length > 0) ? sectors : FALLBACK_SECTORS;
  const safeProfessionsBySector = professionsBySector ?? {};
  const safeInterests = (interests && interests.length > 0) ? interests : FALLBACK_INTERESTS;
  const safeEmployment = (employmentStatuses && employmentStatuses.length > 0) ? employmentStatuses : FALLBACK_EMPLOYMENT;
  const safeHours = (weeklyHours && weeklyHours.length > 0) ? weeklyHours : FALLBACK_HOURS;
  const professions = safeProfessionsBySector[selectedSector] ?? [];

  // California-specific fields based on sector
  const isTech = selectedSector === "Technology";
  const isEntertainment = selectedSector === "Entertainment" || selectedSector === "Film & TV";
  const showCalifornia = isTech || isEntertainment;

  const toggleInterest = (interest: string) => {
    const current = currentInterests as string[];
    if (current.includes(interest)) {
      setValue("user.professional.interests", current.filter((i) => i !== interest));
    } else if (current.length < 4) {
      setValue("user.professional.interests", [...current, interest]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="space-y-2">
          <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
            Sector
          </label>
          <Controller
            control={control}
            name="user.professional.sector"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(v) => {
                  field.onChange(v);
                  const first = safeProfessionsBySector[v]?.[0] ?? "";
                  setValue("user.professional.profession", first);
                  setValue("user.professional.tech_role", undefined);
                  setValue("user.professional.equity_compensation", undefined);
                  setValue("user.professional.company_stage", undefined);
                  setValue("user.professional.entertainment_role", undefined);
                }}
              >
                <SelectTrigger className="h-11">
                  <SelectValue placeholder="Select sector" />
                </SelectTrigger>
                <SelectContent className="max-h-72">
                  {safeSectors.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          <p className="text-xs text-muted-foreground tabular-nums">
            {safeSectors.length} sectors available
          </p>
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
            Profession
          </label>
          <Controller
            control={control}
            name="user.professional.profession"
            render={({ field }) => (
              professions.length > 0 ? (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger className="h-11">
                    <SelectValue placeholder="Select profession" />
                  </SelectTrigger>
                  <SelectContent className="max-h-72">
                    {professions.map((p) => (
                      <SelectItem key={p} value={p}>{p}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input className="h-11" placeholder="Enter profession" {...field} />
              )
            )}
          />
          {professions.length > 0 && (
            <p className="text-xs text-muted-foreground tabular-nums">
              {professions.length} professions in {selectedSector}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
            Employment Status
          </label>
          <Controller
            control={control}
            name="user.professional.employment_status"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger className="h-11">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {safeEmployment.map((e) => (
                    <SelectItem key={e} value={e}>{e}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
            Weekly Hours Available
          </label>
          <Controller
            control={control}
            name="user.professional.weekly_hours"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger className="h-11">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {safeHours.map((h) => (
                    <SelectItem key={h} value={h}>{HOURS_LABELS[h] ?? h}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      {/* ─── CALIFORNIA-SPECIFIC ─── */}
      {showCalifornia && (
        <div className="rounded-xl border-2 border-dashed border-amber-300/60 bg-amber-50/40 p-5 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <Sparkle weight="duotone" className="h-5 w-5 text-amber-600" />
            <h3 className="text-sm font-semibold tracking-wide text-amber-700 uppercase">
              🌴 California-Specific Details
            </h3>
            <Badge variant="outline" className="text-[10px]">Optional</Badge>
          </div>

          {isTech && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
                  Tech Role
                </label>
                <Controller
                  control={control}
                  name="user.professional.tech_role"
                  render={({ field }) => (
                    <Select
                      value={field.value ?? "_none_"}
                      onValueChange={(v) => field.onChange(v === "_none_" ? undefined : v)}
                    >
                      <SelectTrigger className="h-11">
                        <SelectValue placeholder="— None —" />
                      </SelectTrigger>
                      <SelectContent className="max-h-72">
                        <SelectItem value="_none_">— None —</SelectItem>
                        {(techRoles ?? []).map((r) => (
                          <SelectItem key={r} value={r}>{r}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
                <p className="text-xs text-muted-foreground">FAANG, startup, etc.</p>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
                  Equity Compensation
                </label>
                <Controller
                  control={control}
                  name="user.professional.equity_compensation"
                  render={({ field }) => (
                    <Select
                      value={field.value ?? "_none_"}
                      onValueChange={(v) => field.onChange(v === "_none_" ? undefined : v)}
                    >
                      <SelectTrigger className="h-11">
                        <SelectValue placeholder="— None —" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="_none_">— None —</SelectItem>
                        {(equityCompensations ?? []).map((e) => (
                          <SelectItem key={e} value={e}>{e}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
                <p className="text-xs text-muted-foreground">RSU, ISO, Founder stock</p>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
                  Company Stage
                </label>
                <Controller
                  control={control}
                  name="user.professional.company_stage"
                  render={({ field }) => (
                    <Select
                      value={field.value ?? "_none_"}
                      onValueChange={(v) => field.onChange(v === "_none_" ? undefined : v)}
                    >
                      <SelectTrigger className="h-11">
                        <SelectValue placeholder="— None —" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="_none_">— None —</SelectItem>
                        {(companyStages ?? []).map((c) => (
                          <SelectItem key={c} value={c}>{c}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
                <p className="text-xs text-muted-foreground">Seed, Series A-D, IPO</p>
              </div>
            </div>
          )}

          {isEntertainment && (
            <div className="space-y-2 md:max-w-md">
              <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
                Entertainment Role
              </label>
              <Controller
                control={control}
                name="user.professional.entertainment_role"
                render={({ field }) => (
                  <Select
                    value={field.value ?? "_none_"}
                    onValueChange={(v) => field.onChange(v === "_none_" ? undefined : v)}
                  >
                    <SelectTrigger className="h-11">
                      <SelectValue placeholder="— None —" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="_none_">— None —</SelectItem>
                      {(entertainmentRoles ?? []).map((r) => (
                        <SelectItem key={r} value={r}>{r}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              <p className="text-xs text-muted-foreground">Writer, Director, Above/Below-the-line</p>
            </div>
          )}
        </div>
      )}

      {/* Prior experience */}
      <div className="space-y-2">
        <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
          Prior Experience{" "}
          <span className="normal-case font-sans font-normal text-muted-foreground/70">
            (optional)
          </span>
        </label>
        <Textarea
          rows={2}
          placeholder="E.g., 'Built 2 side projects', 'ETF investing for 5 years'..."
          className="resize-none"
          {...register("user.professional.prior_experience")}
        />
      </div>

      {/* Interests */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
              Interests
            </label>
            <p className="text-xs text-muted-foreground mt-1">
              Select up to 4 — used to personalize recommendations
            </p>
          </div>
          <Badge variant={currentInterests.length === 4 ? "default" : "outline"} className="tabular-nums">
            {currentInterests.length} / 4 selected
          </Badge>
        </div>

        <div className="flex flex-wrap gap-2">
          {safeInterests.map((interest) => {
            const checked = (currentInterests as string[]).includes(interest);
            const disabled = !checked && (currentInterests as string[]).length >= 4;
            return (
              <button
                key={interest}
                type="button"
                disabled={disabled}
                onClick={() => toggleInterest(interest)}
                className={`
                  inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
                  text-xs font-medium transition-all border
                  ${checked
                    ? "bg-primary text-primary-foreground border-primary shadow-sm scale-105"
                    : disabled
                      ? "bg-muted text-muted-foreground border-border opacity-40 cursor-not-allowed"
                      : "bg-background text-foreground border-border hover:border-primary hover:bg-primary/5 cursor-pointer hover:scale-105"
                  }
                `}
              >
                {checked && <Check weight="bold" className="h-3 w-3" />}
                <span className="capitalize">{interest}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
