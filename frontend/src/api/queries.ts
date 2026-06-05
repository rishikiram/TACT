import type { FetchTrialsParams } from "./trials";

// Actively recruiting Phase 2 diabetes trials, capped at 100 results
export const RECRUITING_DIABETES: FetchTrialsParams = {
  "query.cond": "diabetes",
  "filter.overallStatus": "RECRUITING",
  "filter.advanced": "PHASE2",
  pageSize: 1000,
};

// All oncology trials, ideally with location data
export const ONCOLOGY: FetchTrialsParams = {
  "query.cond": "cancer",
  pageSize: 1000,
};

export const NSCLC: FetchTrialsParams = {
  "query.cond": "stage 3 NSCLC OR stage III non-small cell lung cancer OR stage 3 non small cell lung cancer",
  pageSize: 1000,
};

export const NSCLC_precision: FetchTrialsParams = {
  "query.cond": "NSCLC OR non-small cell lung cancer OR non small cell lung cancer",
  "query.term": "adenocarcinoma",
  "query.intr": "targeted therapy OR precision medicine OR inhibitor",
};

export const NSCLC_KRAS: FetchTrialsParams = {
  "query.cond": "NSCLC OR non-small cell lung cancer OR non small cell lung cancer",
  "query.intr": "KRAS G12C inhibitor",
};

export const NSCLC_2line: FetchTrialsParams = {
  "query.cond": '"NSCLC" OR "non-small cell lung cancer"',
  "query.term": '"second line" OR "previously treated" OR "progressed"',
  // "filter.overallStatus": "COMPLETED",
};

export const NSCLC_ADENOCARCINOMA: FetchTrialsParams = {
  "query.cond": "non-small cell lung cancer OR NSCLC OR non small cell lung cancer",
  "query.term": "adenocarcinoma",
  "query.intr": "targeted therapy OR precision medicine",
};

export const PRESETS: { label: string; params: FetchTrialsParams }[] = [
  { label: "NSCLC KRAS G12C", params: NSCLC_KRAS },
  { label: "NSCLC 2nd-line treatment", params: NSCLC_2line},
  { label: "NSCLC Adenocarcinoma", params: NSCLC_ADENOCARCINOMA },
  { label: "NSCLC Precision", params: NSCLC_precision },
  { label: "NSCLC", params: NSCLC },
  // { label: "Oncology", params: ONCOLOGY },
  // { label: "Recruiting Diabetes (Phase 2)", params: RECRUITING_DIABETES },
];
