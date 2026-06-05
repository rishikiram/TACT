import type { FetchTrialsParams } from "./trials";

// Actively recruiting Phase 2 diabetes trials, capped at 100 results
export const RECRUITING_DIABETES: FetchTrialsParams = {
  condition: "diabetes",
  status: "RECRUITING",
  filterAdvanced: "PHASE2",
  pageSize: 1000,
};

// All oncology trials, ideally with location data
export const ONCOLOGY: FetchTrialsParams = {
  condition: "cancer",
  // fields: ["protocolSection.contactsLocationsModule"] // Lets pull everything for now until we run into data issues
  pageSize: 1000,
  // things to add later:
  // US and EU
  // Exclude studies not yet enrolling
  // Exclude phase 1 studies
  // how to handle  exceptions ( null data, missing fields). Can I look up the missing information? such as missing lon/lat.
};

export const NSCLC: FetchTrialsParams = {
  condition: "stage 3 NSCLC OR stage III non-small cell lung cancer OR stage 3 non small cell lung cancer",
  pageSize: 1000,
  // filterAdvanced: "PHASE2 OR PHASE3",
  // fields: ["protocolSection.contactsLocationsModule"] // Lets pull everything for now until we run into data issues
  // things to add later:
  // US and EU
  // Exclude studies not yet enrolling
  // Exclude phase 1 studies
};

export const NSCLC_precision: FetchTrialsParams = {
  condition: "NSCLC OR non-small cell lung cancer OR non small cell lung cancer",
  term: "adenocarcinoma",
  intr: "targeted therapy OR precision medicine OR inhibitor",
  // pageSize: 1000,
  // filterAdvanced: "PHASE2 OR PHASE3",
  // fields: ["protocolSection.contactsLocationsModule"] // Lets pull everything for now until we run into data issues
  // things to add later:
  // US and EU
  // Exclude studies not yet enrolling
  // Exclude phase 1 studies
};

export const NSCLC_KRAS: FetchTrialsParams = {
  condition: "NSCLC OR non-small cell lung cancer OR non small cell lung cancer",
  intr: "KRAS G12C inhibitor"
};

export const NSCLC_2line: FetchTrialsParams = {
  condition: '"NSCLC" OR "non-small cell lung cancer"',
  term: '"second line" OR "previously treated" OR "progressed"',
  // filter:
  //   {overallStatus: "COMPLETED"}
};
// ?query.cond=non-small cell lung cancer
// &query.term=("second line" OR "previously treated" OR "progressed")
// &filter.overallStatus=COMPLETED

export const NSCLC_ADENOCARCINOMA: FetchTrialsParams = {
  condition: "non-small cell lung cancer OR NSCLC OR non small cell lung cancer",
  term: "adenocarcinoma",
  intr: "targeted therapy OR precision medicine",
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