import { queryOptions } from "@tanstack/react-query";
import {
  getFarm,
  getFarmTreeQuota,
  getOperationAdvisory,
  getWeatherAiUsage,
  listAdvisories,
  listFarms,
  listTreeAnalyses,
} from "./endpoints";
import type { OperationType } from "./types";

export const farmsKey = (limit: number, offset: number) =>
  ["farms", { limit, offset }] as const;
export const farmKey = (id: string) => ["farm", id] as const;
export const advisoriesKey = (id: string, limit: number, offset: number) =>
  ["advisories", id, { limit, offset }] as const;
export const quotaKey = (id: string) => ["quota", id] as const;
export const treeAnalysesKey = (id: string, limit: number, offset: number) =>
  ["treeAnalyses", id, { limit, offset }] as const;
export const opAdvisoryKey = (
  id: string,
  op: OperationType,
  date?: string,
) => ["operationAdvisory", id, op, date ?? null] as const;
export const usageKey = ["weatherAiUsage"] as const;

export const farmsQuery = (limit = 20, offset = 0) =>
  queryOptions({
    queryKey: farmsKey(limit, offset),
    queryFn: () => listFarms({ limit, offset }),
  });

export const farmQuery = (id: string) =>
  queryOptions({
    queryKey: farmKey(id),
    queryFn: () => getFarm(id),
  });

export const advisoriesQuery = (id: string, limit = 20, offset = 0) =>
  queryOptions({
    queryKey: advisoriesKey(id, limit, offset),
    queryFn: () => listAdvisories(id, { limit, offset }),
  });

export const quotaQuery = (id: string) =>
  queryOptions({
    queryKey: quotaKey(id),
    queryFn: () => getFarmTreeQuota(id),
  });

export const treeAnalysesQuery = (id: string, limit = 20, offset = 0) =>
  queryOptions({
    queryKey: treeAnalysesKey(id, limit, offset),
    queryFn: () => listTreeAnalyses(id, { limit, offset }),
  });

export const opAdvisoryQuery = (
  id: string,
  op: OperationType,
  date?: string,
) =>
  queryOptions({
    queryKey: opAdvisoryKey(id, op, date),
    queryFn: () => getOperationAdvisory(id, op, { date }),
    enabled: Boolean(id && op),
  });

export const usageQuery = () =>
  queryOptions({
    queryKey: usageKey,
    queryFn: () => getWeatherAiUsage(),
  });
