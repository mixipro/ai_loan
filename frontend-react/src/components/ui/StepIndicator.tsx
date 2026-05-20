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
