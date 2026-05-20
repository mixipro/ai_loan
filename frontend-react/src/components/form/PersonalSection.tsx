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
