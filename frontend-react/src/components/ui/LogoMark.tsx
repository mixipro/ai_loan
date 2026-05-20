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
