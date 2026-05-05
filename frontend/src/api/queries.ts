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

export const NSCLC_v2: FetchTrialsParams = {
  condition: "stage 3 NSCLC OR stage III non-small cell lung cancer OR stage 3 non small cell lung cancer",
  pageSize: 1000,
  filterAdvanced: "PHASE2 OR PHASE3",
  // fields: ["protocolSection.contactsLocationsModule"] // Lets pull everything for now until we run into data issues
  // things to add later:
  // US and EU
  // Exclude studies not yet enrolling
  // Exclude phase 1 studies
};