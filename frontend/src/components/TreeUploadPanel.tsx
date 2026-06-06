import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, Image as ImageIcon, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { ErrorState } from "@/components/States";
import { uploadTreeAnalysis } from "@/lib/api/endpoints";
import { quotaKey, treeAnalysesKey } from "@/lib/api/queries";
import type { TreeAnalysisUploadResponse, TreeQuota } from "@/lib/api/types";
import { apiErrorToMessage } from "@/lib/api/error-messages";
import { toast } from "sonner";

export const MAX_IMAGE_BYTES = 20 * 1024 * 1024;

export function TreeUploadPanel({
  farmId,
  quota,
}: {
  farmId: string;
  quota: TreeQuota | undefined;
}) {
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [withWeather, setWithWeather] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [result, setResult] = useState<TreeAnalysisUploadResponse | null>(null);

  const quotaExceeded = (quota?.remaining ?? 0) <= 0;

  const mutation = useMutation({
    mutationFn: () =>
      uploadTreeAnalysis(farmId, { image: file!, withWeather }),
    onSuccess: (data) => {
      setResult(data);
      toast.success("Tree analysis complete");
      qc.invalidateQueries({ queryKey: quotaKey(farmId) });
      qc.invalidateQueries({ queryKey: ["treeAnalyses", farmId] });
      // clear file
      setFile(null);
      setPreview((p) => {
        if (p) URL.revokeObjectURL(p);
        return null;
      });
      if (inputRef.current) inputRef.current.value = "";
    },
    onError: (err) => {
      toast.error(apiErrorToMessage(err, "treeUpload"));
    },
  });

  function pickFile(f: File | null) {
    setLocalError(null);
    if (preview) URL.revokeObjectURL(preview);
    if (!f) {
      setFile(null);
      setPreview(null);
      return;
    }
    if (!f.type.startsWith("image/")) {
      setLocalError("Please choose an image file.");
      return;
    }
    if (f.size > MAX_IMAGE_BYTES) {
      setLocalError(
        `Image is ${(f.size / 1024 / 1024).toFixed(1)} MB. Maximum is 20 MB.`,
      );
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tree analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {quotaExceeded ? (
          <ErrorState message="Monthly tree analysis quota exceeded. Uploads are disabled until the quota resets." />
        ) : null}

        <div>
          <input
            ref={inputRef}
            id="tree-image"
            type="file"
            accept="image/*"
            className="sr-only"
            onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
          />
          {preview ? (
            <div className="relative inline-block">
              <img
                src={preview}
                alt="Selected tree preview"
                className="rounded-lg border max-h-56"
              />
              <button
                type="button"
                onClick={() => pickFile(null)}
                className="absolute -top-2 -right-2 rounded-full bg-background border h-7 w-7 flex items-center justify-center shadow-sm"
                aria-label="Remove image"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <label
              htmlFor="tree-image"
              className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-6 cursor-pointer hover:bg-accent/40 focus-within:ring-2 focus-within:ring-ring"
            >
              <ImageIcon className="h-6 w-6 text-muted-foreground" />
              <span className="text-sm">Choose an image (max 20 MB)</span>
              <span className="text-xs text-muted-foreground">
                JPG, PNG, WebP
              </span>
            </label>
          )}
        </div>

        {localError ? (
          <p role="alert" className="text-sm text-destructive">
            {localError}
          </p>
        ) : null}

        <div className="flex items-center gap-2">
          <Switch
            id="with-weather"
            checked={withWeather}
            onCheckedChange={setWithWeather}
            disabled={mutation.isPending}
          />
          <Label htmlFor="with-weather" className="cursor-pointer">
            Include current weather
          </Label>
        </div>

        <div className="flex justify-end">
          <Button
            disabled={!file || quotaExceeded || mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            <Upload className="h-4 w-4 mr-1.5" />
            {mutation.isPending ? "Analyzing…" : "Upload & analyze"}
          </Button>
        </div>

        {result ? <TreeAnalysisResult result={result} /> : null}
      </CardContent>
    </Card>
  );
}

export function TreeAnalysisResult({
  result,
}: {
  result: TreeAnalysisUploadResponse;
}) {
  const a = result.analysis_result as Record<string, unknown>;
  const treeCount = typeof a?.tree_count === "number" ? a.tree_count : null;
  const canopy =
    typeof a?.canopy_health === "string" ? (a.canopy_health as string) : null;
  const observations = Array.isArray(a?.observations)
    ? (a.observations as unknown[])
    : [];
  const known = new Set(["tree_count", "canopy_health", "observations"]);
  const other = Object.fromEntries(
    Object.entries(a ?? {}).filter(([k]) => !known.has(k)),
  );

  return (
    <div className="rounded-lg border bg-card p-4 space-y-3 mt-3">
      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
        {treeCount != null ? (
          <Stat label="Tree count" value={treeCount.toLocaleString()} />
        ) : null}
        {canopy ? <Stat label="Canopy health" value={canopy} /> : null}
        <Stat label="Quota remaining" value={result.quota_remaining.toString()} />
      </div>

      {observations.length > 0 ? (
        <div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
            Observations
          </div>
          <ul className="text-sm list-disc pl-5">
            {observations.map((o, i) => (
              <li key={i}>
                {typeof o === "string" ? o : JSON.stringify(o)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {Object.keys(other).length > 0 ? (
        <details>
          <summary className="text-sm cursor-pointer text-muted-foreground">
            Full analysis details
          </summary>
          <pre className="text-xs bg-muted rounded p-2 mt-2 overflow-x-auto">
            {JSON.stringify(other, null, 2)}
          </pre>
        </details>
      ) : null}

      {result.weather === null ? (
        <div className="text-sm rounded-md border border-amber-400/40 bg-amber-50 dark:bg-amber-950/30 p-2">
          Weather enrichment was requested but unavailable. Tree analysis is
          shown above.
        </div>
      ) : result.weather ? (
        <details>
          <summary className="text-sm cursor-pointer">Current weather</summary>
          <pre className="text-xs bg-muted rounded p-2 mt-2 overflow-x-auto">
            {JSON.stringify(result.weather, null, 2)}
          </pre>
        </details>
      ) : null}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}
