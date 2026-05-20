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
