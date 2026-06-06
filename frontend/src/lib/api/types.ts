export type CropType = "tea" | "maize" | "coffee" | "beans" | "vegetables";

export const CROP_TYPES: CropType[] = [
  "tea",
  "maize",
  "coffee",
  "beans",
  "vegetables",
];

export type Farm = {
  id: string;
  farmer_name: string;
  county: string;
  crop_type: CropType;
  latitude: number;
  longitude: number;
  farm_size_acres: number | null;
  created_at: string;
  updated_at: string;
};

export type FarmList = {
  items: Farm[];
  total: number;
  limit: number;
  offset: number;
};

export type FarmCreate = {
  farmer_name: string;
  county: string;
  crop_type: CropType;
  latitude: number;
  longitude: number;
  farm_size_acres?: number | null;
};

export type RiskBand = "low" | "medium" | "high";

export type AdvisoryDayScore = {
  date: string;
  rain_score: number;
  heat_score: number;
  wind_score: number;
  humidity_score: number;
  total_score: number;
  risk_band: RiskBand;
};

export type Advisory = {
  id: string;
  farm_id: string;
  generated_at: string;
  daily_scores: AdvisoryDayScore[];
  recommendations: Record<string, unknown>;
  cached: boolean;
};

export type AdvisoryList = {
  items: Advisory[];
  total: number;
  limit: number;
  offset: number;
};

export type OperationType =
  | "spraying"
  | "irrigation"
  | "harvesting"
  | "planting"
  | "field_work";

export const OPERATION_TYPES: OperationType[] = [
  "spraying",
  "irrigation",
  "harvesting",
  "planting",
  "field_work",
];

export type OperationAdvisory = {
  farm_id: string;
  operation: OperationType;
  recommended: boolean;
  priority: "low" | "medium" | "high" | null;
  best_window: string | null;
  window_date: string | null;
  reasons: string[];
  cached: boolean;
};

export type TreeAnalysisUploadResponse = {
  id: string;
  farm_id: string;
  analysis_result: Record<string, unknown>;
  quota_remaining: number;
  weather?: Record<string, unknown> | null;
};

export type TreeAnalysis = {
  id: string;
  farm_id: string;
  image_url: string | null;
  analysis_result: Record<string, unknown>;
  created_at: string;
};

export type TreeAnalysisList = {
  items: TreeAnalysis[];
  total: number;
  limit: number;
  offset: number;
};

export type TreeQuota = {
  limit: number;
  used: number;
  remaining: number;
};

export type QuotaFamily = {
  used: number;
  limit: number;
  remaining: number;
};

export type WeatherAiUsage = {
  api: QuotaFamily;
  ai: QuotaFamily;
  trees: QuotaFamily;
  quota_status: "healthy" | "low" | "critical" | string;
};
