import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { farmSchema, type FarmFormValues } from "@/lib/validation/farm";
import { CROP_TYPES, type FarmCreate } from "@/lib/api/types";

export type FarmFormProps = {
  defaultValues?: Partial<FarmFormValues>;
  onSubmit: (values: FarmCreate) => Promise<void> | void;
  onCancel?: () => void;
  submitLabel?: string;
  submitting?: boolean;
  serverError?: string | null;
};

export function FarmForm({
  defaultValues,
  onSubmit,
  onCancel,
  submitLabel = "Save farm",
  submitting,
  serverError,
}: FarmFormProps) {
  const form = useForm<FarmFormValues>({
    resolver: zodResolver(farmSchema),
    defaultValues: {
      farmer_name: "",
      county: "",
      crop_type: undefined as unknown as FarmFormValues["crop_type"],
      latitude: undefined as unknown as number,
      longitude: undefined as unknown as number,
      farm_size_acres: null,
      ...defaultValues,
    },
  });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = form;

  const cropType = watch("crop_type");

  const submit = handleSubmit(async (values) => {
    const payload: FarmCreate = {
      farmer_name: values.farmer_name.trim(),
      county: values.county.trim(),
      crop_type: values.crop_type as FarmCreate["crop_type"],
      latitude: values.latitude,
      longitude: values.longitude,
      farm_size_acres:
        values.farm_size_acres === undefined ||
        values.farm_size_acres === null ||
        Number.isNaN(values.farm_size_acres)
          ? null
          : values.farm_size_acres,
    };
    await onSubmit(payload);
  });

  return (
    <form onSubmit={submit} className="space-y-5" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Farmer name"
          error={errors.farmer_name?.message}
          htmlFor="farmer_name"
        >
          <Input
            id="farmer_name"
            autoComplete="off"
            {...register("farmer_name")}
          />
        </Field>
        <Field label="County" error={errors.county?.message} htmlFor="county">
          <Input id="county" autoComplete="off" {...register("county")} />
        </Field>
        <Field label="Crop type" error={errors.crop_type?.message} htmlFor="crop_type">
          <Select
            value={cropType ?? ""}
            onValueChange={(v) =>
              setValue("crop_type", v as FarmFormValues["crop_type"], {
                shouldValidate: true,
              })
            }
          >
            <SelectTrigger id="crop_type">
              <SelectValue placeholder="Select a crop" />
            </SelectTrigger>
            <SelectContent>
              {CROP_TYPES.map((c) => (
                <SelectItem key={c} value={c} className="capitalize">
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>
        <Field
          label="Farm size (acres)"
          error={errors.farm_size_acres?.message}
          htmlFor="farm_size_acres"
          hint="Optional"
        >
          <Input
            id="farm_size_acres"
            type="number"
            step="0.01"
            min={0}
            {...register("farm_size_acres", {
              setValueAs: (v) =>
                v === "" || v === null || v === undefined ? null : Number(v),
            })}
          />
        </Field>
        <Field label="Latitude" error={errors.latitude?.message} htmlFor="latitude">
          <Input
            id="latitude"
            type="number"
            step="0.000001"
            inputMode="decimal"
            {...register("latitude", { valueAsNumber: true })}
          />
        </Field>
        <Field
          label="Longitude"
          error={errors.longitude?.message}
          htmlFor="longitude"
        >
          <Input
            id="longitude"
            type="number"
            step="0.000001"
            inputMode="decimal"
            {...register("longitude", { valueAsNumber: true })}
          />
        </Field>
      </div>

      {serverError ? (
        <div
          role="alert"
          className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm"
        >
          {serverError}
        </div>
      ) : null}

      <div className="flex gap-2 justify-end">
        {onCancel ? (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        ) : null}
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : submitLabel}
        </Button>
      </div>
    </form>
  );
}

function Field({
  label,
  htmlFor,
  hint,
  error,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between">
        <Label htmlFor={htmlFor}>{label}</Label>
        {hint ? (
          <span className="text-xs text-muted-foreground">{hint}</span>
        ) : null}
      </div>
      {children}
      {error ? (
        <p className="text-xs text-destructive" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
