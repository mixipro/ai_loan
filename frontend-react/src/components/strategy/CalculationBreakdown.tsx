// src/components/strategy/CalculationBreakdown.tsx
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CaretDown, CaretUp, Calculator } from "@phosphor-icons/react";
import type { CalcBreakdown } from "@/types/response";

interface Props {
  breakdown: CalcBreakdown;
}

export function CalculationBreakdown({ breakdown }: Props) {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Calculator weight="duotone" className="h-5 w-5 text-primary" />
          Calculation Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {breakdown.steps.map((step) => {
          const isExpanded = expandedStep === step.step;
          return (
            <div
              key={step.step}
              className={`
                border rounded-lg overflow-hidden transition-all
                ${isExpanded ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}
              `}
            >
              <button
                type="button"
                onClick={() => setExpandedStep(isExpanded ? null : step.step)}
                className="w-full flex items-center justify-between p-3 text-left"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <Badge variant="outline" className="shrink-0 tabular-nums">
                    Step {step.step}
                  </Badge>
                  <span className="font-medium text-sm truncate">{step.title}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-primary font-semibold whitespace-nowrap">
                    {step.result.split(" ")[0]}
                  </span>
                  {isExpanded ? <CaretUp className="h-4 w-4" /> : <CaretDown className="h-4 w-4" />}
                </div>
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 pt-1 space-y-3 animate-fade-in">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {step.explanation}
                  </p>

                  <div className="bg-background border rounded p-2.5 font-mono text-xs">
                    <div className="text-muted-foreground mb-1">Formula:</div>
                    <div className="text-foreground">{step.formula}</div>
                  </div>

                  <div className="flex items-baseline justify-between">
                    <span className="text-xs text-muted-foreground">Result:</span>
                    <span className="font-mono font-semibold text-primary">{step.result}</span>
                  </div>

                  {step.note && (
                    <div className="bg-amber-50 border border-amber-200 rounded p-2 text-xs text-amber-900">
                      {step.note}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Conclusion */}
        {breakdown.conclusion && (
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <h4 className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wide">
              Conclusion
            </h4>
            <p className="text-sm whitespace-pre-wrap leading-relaxed">
              {breakdown.conclusion}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
