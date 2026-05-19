#!/bin/bash
# Day 4 — Premium IBM Plex Serif + modernized HTML hybrid
set -e

if [ ! -d "frontend-react" ]; then
    echo "Run from project root: ~/PycharmProjects/ai_loan"
    exit 1
fi

echo "Day 4 — Premium redesign"
echo ""
echo "⚠️  IMPORTANT: First install IBM Plex Serif font!"
echo "   cd frontend-react && npm install @fontsource/ibm-plex-serif"
echo ""
read -p "Have you installed @fontsource/ibm-plex-serif? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Run: cd frontend-react && npm install @fontsource/ibm-plex-serif"
    echo "Then run this script again."
    exit 1
fi

echo "[1/11] Writing src/index.css..."
cat > frontend-react/src/index.css << 'FILE_EOF_01'
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn/tailwind.css";
@import "@fontsource-variable/geist";
@import "@fontsource-variable/geist-mono";
@import "@fontsource/ibm-plex-serif/400.css";
@import "@fontsource/ibm-plex-serif/500.css";
@import "@fontsource/ibm-plex-serif/600.css";
@import "@fontsource/ibm-plex-serif/700.css";
@import "@fontsource/ibm-plex-serif/400-italic.css";

@custom-variant dark (&:is(.dark *));

@theme inline {
    --font-sans: 'Geist Variable', system-ui, -apple-system, sans-serif;
    --font-heading: 'IBM Plex Serif', Georgia, serif;
    --font-mono: 'Geist Mono Variable', monospace;

    --color-sidebar-ring: var(--sidebar-ring);
    --color-sidebar-border: var(--sidebar-border);
    --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
    --color-sidebar-accent: var(--sidebar-accent);
    --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
    --color-sidebar-primary: var(--sidebar-primary);
    --color-sidebar-foreground: var(--sidebar-foreground);
    --color-sidebar: var(--sidebar);
    --color-chart-5: var(--chart-5);
    --color-chart-4: var(--chart-4);
    --color-chart-3: var(--chart-3);
    --color-chart-2: var(--chart-2);
    --color-chart-1: var(--chart-1);
    --color-ring: var(--ring);
    --color-input: var(--input);
    --color-border: var(--border);
    --color-destructive: var(--destructive);
    --color-accent-foreground: var(--accent-foreground);
    --color-accent: var(--accent);
    --color-muted-foreground: var(--muted-foreground);
    --color-muted: var(--muted);
    --color-secondary-foreground: var(--secondary-foreground);
    --color-secondary: var(--secondary);
    --color-primary-foreground: var(--primary-foreground);
    --color-primary: var(--primary);
    --color-popover-foreground: var(--popover-foreground);
    --color-popover: var(--popover);
    --color-card-foreground: var(--card-foreground);
    --color-card: var(--card);
    --color-foreground: var(--foreground);
    --color-background: var(--background);

    --radius-sm: 0.5rem;
    --radius-md: 0.75rem;
    --radius-lg: 1rem;
    --radius-xl: 1.25rem;
}

:root {
    /* ─── WARM AMBER PALETTE (premium, refined) ─── */
    --background: oklch(0.985 0.008 85);
    --foreground: oklch(0.18 0.015 50);

    --card: oklch(0.99 0.005 85);
    --card-foreground: oklch(0.18 0.015 50);

    --popover: oklch(0.99 0.005 85);
    --popover-foreground: oklch(0.18 0.015 50);

    /* Primary — refined amber (less brown, more warmth) */
    --primary: oklch(0.55 0.16 55);
    --primary-foreground: oklch(0.98 0.005 85);

    /* Secondary — soft cream */
    --secondary: oklch(0.95 0.025 90);
    --secondary-foreground: oklch(0.25 0.02 50);

    --muted: oklch(0.94 0.018 85);
    --muted-foreground: oklch(0.45 0.025 60);

    /* Accent — soft yellow for underlines */
    --accent: oklch(0.95 0.10 95);
    --accent-foreground: oklch(0.25 0.05 80);

    --destructive: oklch(0.55 0.20 25);
    --destructive-foreground: oklch(0.98 0.005 85);

    --border: oklch(0.88 0.02 85);
    --input: oklch(0.88 0.02 85);
    --ring: oklch(0.55 0.16 55);

    --radius: 0.875rem;

    /* Chart colors — warmer */
    --chart-1: oklch(0.62 0.18 45);
    --chart-2: oklch(0.60 0.10 150);
    --chart-3: oklch(0.55 0.15 25);
    --chart-4: oklch(0.65 0.12 90);
    --chart-5: oklch(0.50 0.10 280);

    /* Custom premium tokens */
    --amber-50: oklch(0.97 0.025 85);
    --amber-100: oklch(0.93 0.05 85);
    --amber-200: oklch(0.85 0.08 75);
    --amber-300: oklch(0.75 0.12 65);
    --amber-500: oklch(0.62 0.18 55);
    --amber-600: oklch(0.55 0.16 50);
    --amber-700: oklch(0.45 0.14 45);

    --yellow-accent: oklch(0.88 0.16 95);

    /* Sidebar */
    --sidebar: oklch(0.97 0.01 85);
    --sidebar-foreground: oklch(0.18 0.015 50);
    --sidebar-primary: oklch(0.55 0.16 55);
    --sidebar-primary-foreground: oklch(0.98 0.005 85);
    --sidebar-accent: oklch(0.94 0.02 85);
    --sidebar-accent-foreground: oklch(0.25 0.02 50);
    --sidebar-border: oklch(0.88 0.02 85);
    --sidebar-ring: oklch(0.55 0.16 55);
}

@layer base {
    * { @apply border-border; }

    html {
        font-family: var(--font-sans);
        font-feature-settings: "cv11", "ss01";
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        scroll-behavior: smooth;
    }

    body {
        font-family: var(--font-sans);
        background:
            radial-gradient(ellipse 1200px 600px at top center,
                            oklch(0.96 0.06 75 / 0.4),
                            transparent 70%),
            oklch(0.985 0.008 85);
        color: var(--foreground);
        min-height: 100vh;
    }

    code, kbd, pre {
        font-family: var(--font-mono);
    }

    h1, h2, h3, h4 {
        font-family: var(--font-heading);
        letter-spacing: -0.015em;
        font-weight: 600;
    }

    .font-mono, .tabular-nums {
        font-family: var(--font-mono);
        font-feature-settings: "tnum";
    }

    .font-serif {
        font-family: var(--font-heading);
    }
}

/* ─── PREMIUM UTILITIES ─── */

/* Yellow underline accent — like HTML version */
.underline-accent {
    position: relative;
    display: inline-block;
}
.underline-accent::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -4px;
    height: 6px;
    background: oklch(0.88 0.16 95 / 0.5);
    border-radius: 3px;
    z-index: -1;
}

/* Premium card with glass effect */
.card-premium {
    background: oklch(0.99 0.005 85 / 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid oklch(0.88 0.02 85 / 0.6);
    box-shadow:
        0 1px 3px oklch(0.5 0.02 60 / 0.04),
        0 4px 12px oklch(0.5 0.02 60 / 0.04);
}

/* Section header underline (subtle amber) */
.section-divider {
    background: linear-gradient(to right,
        oklch(0.88 0.16 95 / 0.7),
        oklch(0.88 0.16 95 / 0.0));
    height: 2px;
    width: 100%;
    border-radius: 1px;
}

/* Animations */
@keyframes fade-in {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in { animation: fade-in 0.4s ease-out; }

@keyframes slide-up {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-slide-up { animation: slide-up 0.5s ease-out; }

@keyframes gentle-pulse {
    0%, 100% { box-shadow: 0 0 0 0 oklch(0.55 0.16 55 / 0); }
    50%      { box-shadow: 0 0 24px 4px oklch(0.55 0.16 55 / 0.20); }
}
.animate-gentle-pulse {
    animation: gentle-pulse 3s ease-in-out infinite;
}

/* Number animation for live values */
@keyframes number-flash {
    0% { color: var(--primary); }
    100% { color: var(--foreground); }
}
.animate-number {
    animation: number-flash 0.4s ease-out;
}
FILE_EOF_01

echo "[2/11] Writing src/main.tsx..."
cat > frontend-react/src/main.tsx << 'FILE_EOF_02'
// src/main.tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App.tsx";

// Fonts
import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";

import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>
);
FILE_EOF_02

echo "[3/11] Writing src/components/ui/LogoMark.tsx..."
cat > frontend-react/src/components/ui/LogoMark.tsx << 'FILE_EOF_03'
// src/components/ui/LogoMark.tsx

interface Props {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZES = {
  sm: "h-10 w-10 text-base",
  md: "h-14 w-14 text-xl",
  lg: "h-20 w-20 text-3xl",
};

export function LogoMark({ size = "md", className = "" }: Props) {
  return (
    <div
      className={`
        ${SIZES[size]}
        ${className}
        relative
        flex items-center justify-center
        font-serif font-bold text-white
        rounded-2xl
        bg-gradient-to-br from-[oklch(0.62_0.18_55)] to-[oklch(0.45_0.14_45)]
        shadow-lg shadow-amber-500/20
        select-none
      `}
    >
      {/* Highlight on top */}
      <div className="absolute inset-x-2 top-1 h-px bg-white/30 rounded-full" />

      <span className="relative">C</span>

      {/* Subtle glow ring */}
      <div className="absolute inset-0 rounded-2xl ring-1 ring-amber-500/30 ring-offset-2 ring-offset-background/0" />
    </div>
  );
}
FILE_EOF_03

echo "[4/11] Writing src/components/ui/StepIndicator.tsx..."
cat > frontend-react/src/components/ui/StepIndicator.tsx << 'FILE_EOF_04'
// src/components/ui/StepIndicator.tsx
import { Check } from "@phosphor-icons/react";

interface Step {
  number: number;
  label: string;
}

interface Props {
  steps: Step[];
  currentStep: number;
  onStepClick?: (step: number) => void;
}

export function StepIndicator({ steps, currentStep, onStepClick }: Props) {
  return (
    <div className="flex items-center justify-center gap-2 sm:gap-4">
      {steps.map((step, idx) => {
        const isActive = step.number === currentStep;
        const isCompleted = step.number < currentStep;
        const isClickable = isCompleted && onStepClick;

        return (
          <div key={step.number} className="flex items-center gap-2 sm:gap-3">
            <button
              type="button"
              disabled={!isClickable}
              onClick={() => isClickable && onStepClick(step.number)}
              className={`
                flex items-center gap-2 transition-all
                ${isClickable ? "cursor-pointer hover:opacity-80" : "cursor-default"}
              `}
            >
              <div
                className={`
                  flex items-center justify-center h-7 w-7 rounded-full
                  font-mono text-xs font-semibold transition-all
                  ${isActive
                    ? "bg-primary text-primary-foreground shadow-md ring-2 ring-primary/20 ring-offset-2 ring-offset-background"
                    : isCompleted
                      ? "bg-primary/15 text-primary"
                      : "bg-muted text-muted-foreground"
                  }
                `}
              >
                {isCompleted ? (
                  <Check weight="bold" className="h-3.5 w-3.5" />
                ) : (
                  step.number
                )}
              </div>
              <span
                className={`
                  text-sm font-medium hidden sm:inline
                  ${isActive ? "text-foreground" : "text-muted-foreground"}
                `}
              >
                {step.label}
              </span>
            </button>

            {/* Connector line */}
            {idx < steps.length - 1 && (
              <div
                className={`
                  h-px w-6 sm:w-12 transition-colors
                  ${step.number < currentStep ? "bg-primary/40" : "bg-border"}
                `}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
FILE_EOF_04

echo "[5/11] Writing src/components/ui/SectionCard.tsx..."
cat > frontend-react/src/components/ui/SectionCard.tsx << 'FILE_EOF_05'
// src/components/ui/SectionCard.tsx
import type { ReactNode } from "react";

interface Props {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  badge?: string;
  badgeVariant?: "amber" | "yellow" | "green" | "neutral";
  children: ReactNode;
  className?: string;
}

const BADGE_STYLES: Record<string, string> = {
  amber: "bg-[oklch(0.93_0.05_85)] text-[oklch(0.4_0.12_50)]",
  yellow: "bg-[oklch(0.95_0.10_95)] text-[oklch(0.35_0.10_85)]",
  green: "bg-[oklch(0.92_0.04_130)] text-[oklch(0.30_0.05_130)]",
  neutral: "bg-muted text-muted-foreground",
};

export function SectionCard({
  title,
  subtitle,
  icon,
  badge,
  badgeVariant = "amber",
  children,
  className = "",
}: Props) {
  return (
    <section
      className={`
        card-premium rounded-2xl p-6 md:p-8 animate-fade-in
        ${className}
      `}
    >
      {/* Header */}
      <div className="mb-5">
        <div className="flex items-center gap-3 mb-2">
          {icon && <div className="text-primary">{icon}</div>}
          <h2 className="font-serif text-2xl font-semibold tracking-tight">
            {title}
          </h2>
          {badge && (
            <span
              className={`
                inline-flex items-center text-[10px] font-mono font-semibold uppercase
                tracking-wider px-2.5 py-1 rounded-md
                ${BADGE_STYLES[badgeVariant]}
              `}
            >
              {badge}
            </span>
          )}
        </div>
        {subtitle && (
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        )}
        {/* Amber underline accent */}
        <div className="section-divider mt-3" />
      </div>

      {/* Content */}
      <div>{children}</div>
    </section>
  );
}
FILE_EOF_05

echo "[6/11] Writing src/components/form/PersonalSection.tsx..."
cat > frontend-react/src/components/form/PersonalSection.tsx << 'FILE_EOF_06'
// src/components/form/PersonalSection.tsx
import { useFormContext } from "react-hook-form";
import { Input } from "@/components/ui/input";
import type { AnalyzeRequest } from "@/types/request";

export function PersonalSection() {
  const { register, formState: { errors } } = useFormContext<AnalyzeRequest>();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div className="space-y-2">
        <label
          htmlFor="age"
          className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground"
        >
          Age
        </label>
        <Input
          id="age"
          type="number"
          min={18}
          max={100}
          className="h-11"
          {...register("user.personal.age", { valueAsNumber: true, required: true })}
        />
        {errors.user?.personal?.age && (
          <p className="text-xs text-destructive">Age must be between 18 and 100</p>
        )}
      </div>
    </div>
  );
}
FILE_EOF_06

echo "[7/11] Writing src/components/form/LocationSection.tsx..."
cat > frontend-react/src/components/form/LocationSection.tsx << 'FILE_EOF_07'
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
FILE_EOF_07

echo "[8/11] Writing src/components/form/FinancialSection.tsx..."
cat > frontend-react/src/components/form/FinancialSection.tsx << 'FILE_EOF_08'
// src/components/form/FinancialSection.tsx
import { useFormContext } from "react-hook-form";
import { Input } from "@/components/ui/input";
import type { AnalyzeRequest } from "@/types/request";

const FIELDS = [
  { key: "income" as const, label: "Monthly Income", short: "INCOME" },
  { key: "expenses" as const, label: "Monthly Expenses", short: "EXPENSES" },
  { key: "monthly_debt" as const, label: "Monthly Debt", short: "DEBT" },
  { key: "savings" as const, label: "Total Savings", short: "SAVINGS" },
];

export function FinancialSection() {
  const { register } = useFormContext<AnalyzeRequest>();

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {FIELDS.map(({ key, short }) => (
        <div key={key} className="space-y-2">
          <label
            htmlFor={key}
            className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground"
          >
            {short}
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm font-mono">
              $
            </span>
            <Input
              id={key}
              type="number"
              min={0}
              step={100}
              className="h-11 pl-7 font-mono tabular-nums"
              {...register(`user.financial.${key}`, { valueAsNumber: true })}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
FILE_EOF_08

echo "[9/11] Writing src/components/form/ProfessionalSection.tsx..."
cat > frontend-react/src/components/form/ProfessionalSection.tsx << 'FILE_EOF_09'
// src/components/form/ProfessionalSection.tsx
import { useFormContext, useWatch, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Check } from "@phosphor-icons/react";
import type { AnalyzeRequest } from "@/types/request";

interface Props {
  sectors?: string[];
  professionsBySector?: Record<string, string[]>;
  interests?: string[];
  employmentStatuses?: string[];
  weeklyHours?: string[];
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
  sectors, professionsBySector, interests, employmentStatuses, weeklyHours,
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
        {/* Sector */}
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

        {/* Profession */}
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

        {/* Employment */}
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

        {/* Weekly hours */}
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

      {/* Prior experience */}
      <div className="space-y-2">
        <label className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground">
          Prior Experience <span className="normal-case font-sans font-normal text-muted-foreground/70">(optional)</span>
        </label>
        <Textarea
          rows={2}
          placeholder="E.g., 'Built 2 side projects', 'ETF investing for 5 years'..."
          className="resize-none"
          {...register("user.professional.prior_experience")}
        />
      </div>

      {/* Interests as chips */}
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
FILE_EOF_09

echo "[10/11] Writing src/components/form/PreferencesSection.tsx..."
cat > frontend-react/src/components/form/PreferencesSection.tsx << 'FILE_EOF_10'
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
FILE_EOF_10

echo "[11/11] Writing src/pages/FormPage.tsx..."
cat > frontend-react/src/pages/FormPage.tsx << 'FILE_EOF_11'
// src/pages/FormPage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm, FormProvider } from "react-hook-form";
import { useOptions } from "@/hooks/useOptions";
import { useAnalyze } from "@/hooks/useAnalyze";
import { DEMO_PROFILES, type DemoProfileKey } from "@/lib/defaults";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
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
  MapPin, Briefcase, CurrencyDollar, User, Sparkle, Compass,
  TestTube, ArrowRight, ArrowLeft
} from "@phosphor-icons/react";

const STEPS = [
  { number: 1, label: "Profile" },
  { number: 2, label: "Configure" },
  { number: 3, label: "Recommendations" },
];

export function FormPage() {
  const navigate = useNavigate();
  const optionsQuery = useOptions();
  const analyzeMutation = useAnalyze();
  const [activeTab, setActiveTab] = useState<"profile" | "strategies">("profile");

  const methods = useForm<AnalyzeRequest>({
    defaultValues: DEMO_PROFILES.truck_driver.data,
    mode: "onChange",
  });

  const loadDemo = (key: string) => {
    if (key in DEMO_PROFILES) {
      methods.reset(DEMO_PROFILES[key as DemoProfileKey].data);
    }
  };

  const onSubmit = async (data: AnalyzeRequest) => {
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
        <Skeleton className="h-8 w-1/3 mx-auto" />
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
      {/* ─── HERO ─── */}
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

        {/* Demo profile selector */}
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

      {/* ─── STEP INDICATOR ─── */}
      <div className="mb-10">
        <StepIndicator
          steps={STEPS}
          currentStep={currentStep}
          onStepClick={(step) => {
            if (step === 1) setActiveTab("profile");
            else if (step === 2) setActiveTab("strategies");
          }}
        />
      </div>

      {/* ─── FORM ─── */}
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
                  onClick={() => setActiveTab("strategies")}
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
FILE_EOF_11

echo ""
echo "✅ Day 4 premium redesign installed!"
echo ""
echo "Next:"
echo "  1. Restart Vite (Ctrl+C, then make frontend)"
echo "  2. Hard refresh browser (Ctrl+Shift+R)"
echo "  3. Compare to HTML version — should look as good or better"