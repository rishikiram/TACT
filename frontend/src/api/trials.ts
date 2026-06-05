// Fetch calls — points to /api/trials (proxied to localhost:3001 by Vite)

export interface TrialLocation {
  city?: string;
  state?: string;
  country?: string;
  facility?: string;
  geoPoint?: { lat: number; lon: number };
}

export interface TrialIntervention {
  name?: string;
  type?: string;
  description?: string;
  armGroupLabels?: string[];
}

export interface TrialArmGroup {
  label?: string;
  type?: string;
  description?: string;
  interventionNames?: string[];
}

export interface TrialOutcome {
  measure?: string;
  description?: string;
  timeFrame?: string;
}

export interface Trial {
  nctId: string;
  briefTitle: string;
  // statusModule
  overallStatus: string;
  startDate?: string;
  startDateType?: string;
  primaryCompletionDate?: string;
  primaryCompletionDateType?: string;
  completionDate?: string;
  completionDateType?: string;
  lastUpdatePost?: string;
  // sponsorCollaboratorsModule
  sponsor?: string;
  sponsorClass?: string;
  // conditionsModule
  conditions: string[];
  conditionKeywords: string[];
  // armsInterventionsModule
  interventions: TrialIntervention[];
  armGroups: TrialArmGroup[];
  // designModule
  phases: string[];
  phase1: boolean;
  phase2: boolean;
  phase3: boolean;
  phase4: boolean;
  phaseText?: string;
  studyType?: string;
  enrollment?: number;
  enrollmentType?: string;
  masking?: string;
  allocation?: string;
  interventionModel?: string;
  primaryPurpose?: string;
  // eligibilityModule
  eligibilityCriteria?: string;
  healthyVolunteers?: boolean;
  stdAges?: string[];
  // contactsLocationsModule
  locations: TrialLocation[];
  multicountry: boolean;
  // outcomesModule
  primaryOutcomes: TrialOutcome[];
  secondaryOutcomes: TrialOutcome[];
  // descriptionModule
  briefSummary?: string;
}

export type FetchTrialsParams = Record<string, string | number>;

export interface FetchTrialsResult {
  trials: Trial[];
  nextPageToken?: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapStudy(study: any): Trial {
  const p = study.protocolSection ?? {};
  const status = p.statusModule ?? {};
  const design = p.designModule ?? {};
  const sponsor = p.sponsorCollaboratorsModule ?? {};
  const conditions = p.conditionsModule ?? {};
  const arms = p.armsInterventionsModule ?? {};
  const eligibility = p.eligibilityModule ?? {};
  const outcomes = p.outcomesModule ?? {};
  const locations = p.contactsLocationsModule ?? {};
  const designInfo = design.designInfo ?? {};
  const phases: string[] = design.phases ?? [];

  const locs: TrialLocation[] = locations.locations ?? [];
  const countries = new Set(locs.map((l: TrialLocation) => l.country));

  return {
    nctId: p.identificationModule?.nctId ?? "",
    briefTitle: p.identificationModule?.briefTitle ?? "",
    briefSummary: p.descriptionModule?.briefSummary,
    // statusModule
    overallStatus: status.overallStatus ?? "",
    startDate: status.startDateStruct?.date,
    startDateType: status.startDateStruct?.type,
    primaryCompletionDate: status.primaryCompletionDateStruct?.date,
    primaryCompletionDateType: status.primaryCompletionDateStruct?.type,
    completionDate: status.completionDateStruct?.date,
    completionDateType: status.completionDateStruct?.type,
    lastUpdatePost: status.lastUpdatePostDateStruct?.date,
    // sponsorCollaboratorsModule
    sponsor: sponsor.leadSponsor?.name,
    sponsorClass: sponsor.leadSponsor?.class,
    // conditionsModule
    conditions: conditions.conditions ?? [],
    conditionKeywords: conditions.keywords ?? [],
    // armsInterventionsModule
    interventions: arms.interventions ?? [],
    armGroups: arms.armGroups ?? [],
    // designModule
    phases,
    phase1: phases.includes("PHASE1"),
    phase2: phases.includes("PHASE2"),
    phase3: phases.includes("PHASE3"),
    phase4: phases.includes("PHASE4"),
    phaseText: phases.length ? phases.join("/") : undefined,
    studyType: design.studyType,
    enrollment: design.enrollmentInfo?.count,
    enrollmentType: design.enrollmentInfo?.type,
    masking: designInfo.maskingInfo?.masking,
    allocation: designInfo.allocation,
    interventionModel: designInfo.interventionModel,
    primaryPurpose: designInfo.primaryPurpose,
    // eligibilityModule
    eligibilityCriteria: eligibility.eligibilityCriteria,
    healthyVolunteers: eligibility.healthyVolunteers,
    stdAges: eligibility.stdAges,
    // contactsLocationsModule
    locations: locs,
    multicountry: countries.size > 1,
    // outcomesModule
    primaryOutcomes: outcomes.primaryOutcomes ?? [],
    secondaryOutcomes: outcomes.secondaryOutcomes ?? [],
  };
}

function buildQuery(params: FetchTrialsParams): URLSearchParams {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) query.set(key, String(value));
  }
  return query;
}

export async function fetchTrials(
  params: FetchTrialsParams
): Promise<FetchTrialsResult> {
  const query = buildQuery(params);

  const res = await fetch(`/api/trials?${query.toString()}`);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data: any = await res.json();
  return { trials: (data.studies ?? []).map(mapStudy), nextPageToken: data.nextPageToken };
}

// Fetches all pages via the backend's /api/trials/all endpoint.
// pageSize and pageToken are managed by the backend — do not pass them here.
export async function fetchAllTrials(
  params: FetchTrialsParams
): Promise<FetchTrialsResult> {
  const query = buildQuery(params);

  const res = await fetch(`/api/trials/all?${query.toString()}`);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data: any = await res.json();
  return { trials: (data.studies ?? []).map(mapStudy) };
}
