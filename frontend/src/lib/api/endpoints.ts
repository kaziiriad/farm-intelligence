import { request } from "./client";
import type {
  Advisory,
  AdvisoryList,
  Farm,
  FarmCreate,
  FarmList,
  OperationAdvisory,
  OperationType,
  TreeAnalysisList,
  TreeAnalysisUploadResponse,
  TreeQuota,
  WeatherAiUsage,
} from "./types";

export function listFarms(params?: { limit?: number; offset?: number }) {
  return request<FarmList>("/api/v1/farms", {
    query: { limit: params?.limit ?? 20, offset: params?.offset ?? 0 },
  });
}

export function getFarm(farmId: string) {
  return request<Farm>(`/api/v1/farms/${encodeURIComponent(farmId)}`);
}

export function createFarm(payload: FarmCreate) {
  return request<Farm>("/api/v1/farms", { method: "POST", body: payload });
}

export function updateFarm(farmId: string, payload: Partial<FarmCreate>) {
  return request<Farm>(`/api/v1/farms/${encodeURIComponent(farmId)}`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteFarm(farmId: string) {
  return request<void>(`/api/v1/farms/${encodeURIComponent(farmId)}`, {
    method: "DELETE",
  });
}

export function generateAdvisory(farmId: string) {
  return request<Advisory>(
    `/api/v1/farms/${encodeURIComponent(farmId)}/advisory`,
  );
}

export function listAdvisories(
  farmId: string,
  params?: { limit?: number; offset?: number },
) {
  return request<AdvisoryList>(
    `/api/v1/farms/${encodeURIComponent(farmId)}/advisories`,
    { query: { limit: params?.limit ?? 20, offset: params?.offset ?? 0 } },
  );
}

export function getOperationAdvisory(
  farmId: string,
  operation: OperationType,
  params?: { date?: string },
) {
  return request<OperationAdvisory>(
    `/api/v1/farms/${encodeURIComponent(farmId)}/operations/${operation}`,
    { query: { date: params?.date } },
  );
}

export function uploadTreeAnalysis(
  farmId: string,
  input: { image: File; withWeather?: boolean },
) {
  const fd = new FormData();
  fd.append("image", input.image);
  return request<TreeAnalysisUploadResponse>(
    `/api/v1/farms/${encodeURIComponent(farmId)}/tree-analysis`,
    {
      method: "POST",
      formData: fd,
      query: input.withWeather ? { with_weather: true } : undefined,
    },
  );
}

export function getFarmTreeQuota(farmId: string) {
  return request<TreeQuota>(
    `/api/v1/farms/${encodeURIComponent(farmId)}/quota`,
  );
}

export function listTreeAnalyses(
  farmId: string,
  params?: { limit?: number; offset?: number },
) {
  return request<TreeAnalysisList>(
    `/api/v1/farms/${encodeURIComponent(farmId)}/tree-analyses`,
    { query: { limit: params?.limit ?? 20, offset: params?.offset ?? 0 } },
  );
}

export function getWeatherAiUsage() {
  return request<WeatherAiUsage>("/api/v1/weather-ai/usage");
}

export function getHealth() {
  return request<{ status: string }>("/health");
}

export function getReadiness() {
  return request<{ status: string; reason?: string }>("/health/ready");
}
