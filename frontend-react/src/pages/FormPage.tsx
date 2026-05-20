// src/pages/FormPage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm, FormProvider } from "react-hook-form";
import { useOptions } from "@/hooks/useOptions";
import { useAnalyze } from "@/hooks/useAnalyze";
import { DEMO_PROFILES, type DemoProfileKey } from "@/lib/defaults";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import type { AnalyzeRequest } from "@/types/request";
import { PersonalSection } from "@/components/form/PersonalSection";
import { LocationSection } from "@/components/form/LocationSection";
import { FinancialSection } from "@/components/form/FinancialSection";
import { ProfessionalSection } from "@/components/form/ProfessionalSection";
import { PreferencesSection } from "@/components/form/PreferencesSection";
import { StrategiesSection } from "@/components/form/StrategiesSection";
import { LogoMark } from "@/components/ui/LogoMark";
import { StepIndicator } from "@/components/ui/StepIndicator";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  MapPin, Briefcase, CurrencyDollar, Sparkle, Compass,
  TestTube, ArrowRight, ArrowLeft, Warning,
} from "@phosphor-icons/react";

const STEPS = [
  { number: 1, label: "Profile" },
  { number: 2, label: "Configure" },
  { number: 3, label: "Recommendations" },
];

// Validation rules — what fields are required
interface ValidationError {
  field: string;
  label: string;
  reason: string;
}

function validateProfile(data: AnalyzeRequest): ValidationError[] {
  const errors: ValidationError[] = [];
  const u = data.user;

  // Personal
  if (!u.personal.age || u.personal.age < 18 || u.personal.age > 100) {
    errors.push({ field: "personal.age", label: "Age", reason: "Must be 18–100" });
  }

  // Location
  if (!u.location.region) {
    errors.push({ field: "location.region", label: "Region", reason: "Select a region" });
  }
  if (!u.location.city || u.location.city.trim() === "") {
    errors.push({ field: "location.city", label: "City", reason: "Select or enter a city" });
  }

  // Financial
  if (u.financial.income == null || u.financial.income < 0) {
    errors.push({ field: "financial.income", label: "Monthly Income", reason: "Required" });
  }
  if (u.financial.expenses == null || u.financial.expenses < 0) {
    errors.push({ field: "financial.expenses", label: "Monthly Expenses", reason: "Required" });
  }
  if (u.financial.savings == null || u.financial.savings < 0) {
    errors.push({ field: "financial.savings", label: "Total Savings", reason: "Required" });
  }

  // Professional
  if (!u.professional.sector || u.professional.sector.trim() === "") {
    errors.push({ field: "professional.sector", label: "Sector", reason: "Select a sector" });
  }
  if (!u.professional.profession || u.professional.profession.trim() === "") {
    errors.push({ field: "professional.profession", label: "Profession", reason: "Select or enter a profession" });
  }

  // Preferences
  if (!u.preferences.risk_profile) {
    errors.push({ field: "preferences.risk_profile", label: "Risk Tolerance", reason: "Required" });
  }
  if (!u.preferences.horizon) {
    errors.push({ field: "preferences.horizon", label: "Investment Horizon", reason: "Required" });
  }

  return errors;
}

// Scroll to first error field
function scrollToField(field: string) {
  // Try multiple selectors
  const selectors = [
    `[name="user.${field}"]`,
    `#${field.split(".").pop()}`,
    `[name*="${field.split(".").pop()}"]`,
  ];

  for (const sel of selectors) {
    const el = document.querySelector(sel) as HTMLElement | null;
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      try { el.focus(); } catch { /* noop */ }
      return;
    }
  }

  // Fallback: scroll to top of form
  window.scrollTo({ top: 0, behavior: "smooth" });
}

export function FormPage() {
  const navigate = useNavigate();
  const optionsQuery = useOptions();
  const analyzeMutation = useAnalyze();
  const [activeTab, setActiveTab] = useState<"profile" | "strategies">("profile");
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

  const methods = useForm<AnalyzeRequest>({
    defaultValues: DEMO_PROFILES.truck_driver.data,
    mode: "onChange",
  });

  const loadDemo = (key: string) => {
    if (key in DEMO_PROFILES) {
      methods.reset(DEMO_PROFILES[key as DemoProfileKey].data);
      setValidationErrors([]);
    }
  };

  // ─── Validation gate for Profile → Strategies ───
  const tryGoToStrategies = () => {
    const data = methods.getValues();
    const errors = validateProfile(data);

    if (errors.length > 0) {
      setValidationErrors(errors);
      // Scroll to first error after render
      setTimeout(() => scrollToField(errors[0].field), 100);
      return;
    }

    setValidationErrors([]);
    setActiveTab("strategies");
  };

  const onSubmit = async (data: AnalyzeRequest) => {
    // Final validation gate
    const errors = validateProfile(data);
    if (errors.length > 0) {
      setValidationErrors(errors);
      setActiveTab("profile");
      setTimeout(() => scrollToField(errors[0].field), 100);
      return;
    }

    try {
      const result = await analyzeMutation.mutateAsync(data);
      sessionStorage.setItem("analysis_result", JSON.stringify(result));
      sessionStorage.setItem("analysis_input", JSON.stringify(data));
      navigate("/results");
    } catch (error) {
      console.error("Submit failed:", error);
    }
  };

  if (optionsQuery.isLoading) {
    return (
      <div className="container mx-auto py-12 max-w-5xl px-4 space-y-4">
        <Skeleton className="h-20 w-1/2 mx-auto" />
        <div className="mt-12 space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </div>
    );
  }

  if (optionsQuery.isError) {
    return (
      <div className="container mx-auto py-12 max-w-3xl px-4">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive font-serif">Cannot reach backend</CardTitle>
            <CardDescription>
              Make sure FastAPI is running:{" "}
              <code className="bg-muted px-2 py-0.5 rounded text-xs">make backend</code>
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const options = optionsQuery.data!;
  const currentStep = activeTab === "profile" ? 1 : 2;

  return (
    <div className="container mx-auto py-10 max-w-5xl px-4 animate-fade-in">
      {/* HERO */}
      <div className="text-center mb-10">
        <div className="flex justify-center mb-5">
          <LogoMark size="lg" />
        </div>

        <h1 className="font-serif text-5xl md:text-6xl font-bold tracking-tight mb-3">
          California<span className="text-primary">CFO</span>
        </h1>
        <p className="text-muted-foreground text-base md:text-lg max-w-xl mx-auto">
          AI Financial Advisor That Actually{" "}
          <span className="underline-accent font-medium text-foreground">Knows California</span>
        </p>

        <div className="mt-6 flex items-center justify-center gap-2">
          <Select onValueChange={loadDemo}>
            <SelectTrigger className="h-9 w-[220px] text-xs">
              <TestTube weight="duotone" className="h-3.5 w-3.5 mr-1" />
              <SelectValue placeholder="Load demo profile…" />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(DEMO_PROFILES) as DemoProfileKey[]).map((key) => (
                <SelectItem key={key} value={key} className="text-xs">
                  {DEMO_PROFILES[key].label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* STEP INDICATOR */}
      <div className="mb-10">
        <StepIndicator
          steps={STEPS}
          currentStep={currentStep}
          onStepClick={(step) => {
            if (step === 1) setActiveTab("profile");
            else if (step === 2 && activeTab === "strategies") setActiveTab("strategies");
          }}
        />
      </div>

      {/* ─── VALIDATION ERROR BANNER ─── */}
      {validationErrors.length > 0 && activeTab === "profile" && (
        <div className="mb-6 rounded-xl border-2 border-destructive/40 bg-destructive/5 p-4 animate-slide-up">
          <div className="flex items-start gap-3">
            <Warning weight="fill" className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-destructive mb-2">
                Please complete required fields ({validationErrors.length})
              </h3>
              <ul className="space-y-1">
                {validationErrors.map((err) => (
                  <li key={err.field} className="text-sm flex items-center gap-2">
                    <span className="text-destructive">•</span>
                    <button
                      type="button"
                      onClick={() => scrollToField(err.field)}
                      className="text-left hover:underline font-medium"
                    >
                      {err.label}
                    </button>
                    <span className="text-muted-foreground text-xs">— {err.reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* FORM */}
      <FormProvider {...methods}>
        <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
          {activeTab === "profile" ? (
            <>
              <SectionCard
                title="Personal & Location"
                icon={<MapPin weight="duotone" className="h-6 w-6" />}
                badge="California Resident"
                badgeVariant="amber"
              >
                <div className="space-y-6">
                  <PersonalSection />
                  <LocationSection
                    regions={options.regions}
                    citiesByRegion={options.cities_by_region}
                  />
                </div>
              </SectionCard>

              <SectionCard
                title="Financial Data"
                icon={<CurrencyDollar weight="duotone" className="h-6 w-6" />}
                badge="USD"
                badgeVariant="yellow"
              >
                <FinancialSection />
              </SectionCard>

              <SectionCard
                title="Professional Profile"
                icon={<Briefcase weight="duotone" className="h-6 w-6" />}
              >
                <ProfessionalSection
                  sectors={options.sectors}
                  professionsBySector={options.professions_by_sector}
                  interests={options.predefined_interests}
                  employmentStatuses={options.employment_statuses}
                  weeklyHours={options.weekly_hours}
                  techRoles={options.tech_roles}
                  equityCompensations={options.equity_compensations}
                  companyStages={options.company_stages}
                  entertainmentRoles={options.entertainment_roles}
                />
              </SectionCard>

              <SectionCard
                title="Preferences"
                icon={<Compass weight="duotone" className="h-6 w-6" />}
              >
                <PreferencesSection
                  riskProfiles={options.risk_profiles}
                  horizons={options.horizons}
                />
              </SectionCard>

              <div className="flex justify-end pt-2">
                <Button
                  type="button"
                  onClick={tryGoToStrategies}
                  size="lg"
                  className="gap-2 px-6"
                >
                  Continue to Strategies
                  <ArrowRight weight="bold" className="h-4 w-4" />
                </Button>
              </div>
            </>
          ) : (
            <>
              <StrategiesSection />

              <div className="flex justify-between items-center pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setActiveTab("profile")}
                  className="gap-2"
                >
                  <ArrowLeft weight="bold" className="h-4 w-4" />
                  Back to Profile
                </Button>
                <Button
                  type="submit"
                  size="lg"
                  disabled={analyzeMutation.isPending}
                  className="min-w-[260px] gap-2 shadow-md hover:shadow-lg transition-shadow"
                >
                  {analyzeMutation.isPending ? (
                    <>
                      <span className="animate-spin">⏳</span>
                      Analyzing… (~30 seconds)
                    </>
                  ) : (
                    <>
                      <Sparkle weight="fill" className="h-4 w-4" />
                      Get AI Recommendations
                    </>
                  )}
                </Button>
              </div>
            </>
          )}
        </form>
      </FormProvider>
    </div>
  );
}